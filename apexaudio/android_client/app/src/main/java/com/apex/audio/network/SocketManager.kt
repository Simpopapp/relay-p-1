package com.apex.audio.network

import android.util.Log
import com.apex.audio.data.Protocol
import java.io.IOException
import java.io.InputStream
import java.io.OutputStream
import java.net.InetSocketAddress
import java.net.Socket
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicInteger
import kotlin.math.min

enum class BridgeState { DISCONNECTED, CONNECTING, HANDSHAKE, STREAMING, RECONNECTING }

/**
 * Gerenciador TCP com FSM (PRD §6):
 * DISCONNECTED → CONNECTING → HANDSHAKE → STREAMING ⇄ RECONNECTING.
 * - downlink: socket cliente em host:59900 (recebe áudio/pings, responde pong);
 * - uplink: socket cliente em host:59901 (envia 960B, responde ping);
 * - sem qualquer pacote por 3000ms → socket morto;
 * - reconexão: backoff 500/1000/2000ms (teto 5000ms), flush dos buffers locais;
 * - reconexão silenciosa: nenhum aviso audível.
 */
class SocketManager(
    private val host: String,
    private val onState: (BridgeState) -> Unit,
    private val onRtt: (Float) -> Unit,
    private val onDownlinkAudio: (ByteArray) -> Unit,
    private val onFlushBuffers: () -> Unit,
) {
    companion object {
        const val PORT_DOWNLINK: Int = 59900
        const val PORT_UPLINK: Int = 59901
        private const val TAG = "SocketManager"
        private const val CONNECT_TIMEOUT_MS = 5000
        private const val DEAD_SOCKET_MS = 3000
        private const val HEARTBEAT_MS = 1000L
        private val BACKOFF_MS = longArrayOf(500, 1000, 2000)
        private const val BACKOFF_CAP_MS = 5000L
    }

    @Volatile var state: BridgeState = BridgeState.DISCONNECTED
        private set

    @Volatile var lastRttMs: Float = -1f
        private set

    @Volatile var sequenceGaps: Int = 0
        private set

    private val running = java.util.concurrent.atomic.AtomicBoolean(false)
    private var downSocket: Socket? = null
    private var upSocket: Socket? = null
    private var downOut: OutputStream? = null
    private var upOut: OutputStream? = null
    private var lastPacketAt: Long = 0L
    private var expectedSequence = -1
    private val pendingPings = ConcurrentHashMap<Int, Long>()
    private val pingSeq = AtomicInteger(0)
    private var orchestrator: Thread? = null

    fun connect() {
        if (!running.compareAndSet(false, true)) return
        setState(BridgeState.CONNECTING)
        orchestrator = Thread({ reconnectLoop() }, "apex-orchestrator").also { it.start() }
    }

    fun disconnect() {
        running.set(false)
        closeSockets()
        orchestrator?.join(1000)
        orchestrator = null
        setState(BridgeState.DISCONNECTED)
    }

    /** Envia um quadro mono de 960B pelo uplink (chamado pelo capturer). */
    fun sendUplink(frame: ByteArray) {
        val out = upOut ?: return
        try {
            out.write(Protocol.encode(Protocol.PACKET_AUDIO, Protocol.CHANNEL_UPLINK,
                pingSeq.incrementAndGet(), System.nanoTime() / 1000, frame))
            out.flush()
        } catch (e: IOException) {
            Log.w(TAG, "uplink send falhou: ${e.message}")
        }
    }

    private fun setState(s: BridgeState) {
        state = s
        onState(s)
    }

    private fun reconnectLoop() {
        var attempt = 0
        while (running.get()) {
            try {
                establish()
                attempt = 0
                streamLoop()
            } catch (e: Exception) {
                Log.w(TAG, "sessão interrompida: ${e.javaClass.simpleName}: ${e.message}")
            }
            if (!running.get()) break
            setState(BridgeState.RECONNECTING)
            onFlushBuffers() // PRD §6: nada de áudio residual após reconnect
            val backoff = min(BACKOFF_MS[attempt.coerceAtMost(BACKOFF_MS.size - 1)], BACKOFF_CAP_MS)
            attempt++
            try {
                Thread.sleep(backoff)
            } catch (_: InterruptedException) {
            }
        }
    }

    private fun establish() {
        closeSockets()
        val down = Socket()
        down.connect(InetSocketAddress(host, PORT_DOWNLINK), CONNECT_TIMEOUT_MS)
        down.tcpNoDelay = true
        down.soTimeout = DEAD_SOCKET_MS / 2
        val up = Socket()
        up.connect(InetSocketAddress(host, PORT_UPLINK), CONNECT_TIMEOUT_MS)
        up.tcpNoDelay = true
        up.soTimeout = DEAD_SOCKET_MS / 2
        downSocket = down
        upSocket = up
        downOut = down.getOutputStream()
        upOut = up.getOutputStream()
        setState(BridgeState.HANDSHAKE)
        // handshake: o primeiro frame do downlink deve ser CONFIG_SYNC
        val bb = ByteBufferReader()
        var synced = false
        while (!synced) {
            val buf = ByteArray(4096)
            val n = down.getInputStream().read(buf)
            if (n <= 0) throw IOException("handshake: conexão fechada")
            bb.append(buf, n)
            var consumed = true
            while (consumed) {
                val (frame, rest) = tryDecode(bb)
                if (frame == null) {
                    consumed = false
                } else {
                    bb.consume(rest)
                    if (frame.packetType == Protocol.PACKET_CONFIG_SYNC) {
                        val (rate, channels, frameBytes) = Protocol.parseConfigSync(frame)
                        Log.i(TAG, "handshake OK: ${rate}Hz ch=$channels frame=$frameBytes")
                        synced = true
                    }
                }
            }
        }
        lastPacketAt = System.nanoTime()
        setState(BridgeState.STREAMING)
        startUplinkReader(up)
    }

    /** Loop principal: lê frames do downlink até queda ou dead socket. */
    private fun streamLoop() {
        val down = downSocket ?: throw IOException("socket downlink ausente")
        val bb = ByteBufferReader()
        val input = down.getInputStream()
        while (running.get()) {
            val buf = ByteArray(8192)
            val n = try {
                input.read(buf)
            } catch (e: java.net.SocketTimeoutException) {
                checkHealth()
                continue
            } catch (e: IOException) {
                throw e
            }
            if (n <= 0) throw IOException("downlink fechado")
            lastPacketAt = System.nanoTime()
            bb.append(buf, n)
            var consumed = true
            while (consumed) {
                val (frame, consumedBytes) = tryDecode(bb)
                if (frame == null) {
                    consumed = false
                } else {
                    bb.consume(consumedBytes)
                    handleFrame(frame)
                }
            }
        }
    }

    private fun handleFrame(frame: Protocol.Frame) {
        when (frame.packetType) {
            Protocol.PACKET_AUDIO -> {
                if (expectedSequence >= 0 && frame.sequenceNum > expectedSequence + 1) {
                    sequenceGaps += frame.sequenceNum - expectedSequence - 1
                }
                expectedSequence = frame.sequenceNum
                onDownlinkAudio(frame.payload)
            }
            Protocol.PACKET_PING -> sendDownlink(Protocol.makePong(frame.sequenceNum, frame.timestampUs))
            Protocol.PACKET_PONG -> {
                val sentAt = pendingPings.remove(frame.sequenceNum)
                if (sentAt != null) {
                    lastRttMs = (System.nanoTime() - sentAt) / 1_000_000f
                    onRtt(lastRttMs)
                }
            }
        }
    }

    private fun checkHealth() {
        val idle = System.nanoTime() - lastPacketAt
        if (idle > DEAD_SOCKET_MS * 1_000_000L) {
            throw IOException("socket morto: ${idle / 1_000_000}ms sem pacotes")
        }
        sendHeartbeatIfIdle()
    }

    private fun sendHeartbeatIfIdle() {
        if (pendingPings.isNotEmpty()) return
        val seq = pingSeq.incrementAndGet()
        pendingPings[seq] = System.nanoTime()
        sendDownlink(Protocol.makePing(seq, System.nanoTime() / 1000))
    }

    private fun sendDownlink(bytes: ByteArray) {
        try {
            downOut?.write(bytes)
            downOut?.flush()
        } catch (_: IOException) {
        }
    }

    /** Thread de leitura do uplink: responde pings do host (mantém o túnel vivo). */
    private fun startUplinkReader(up: Socket) {
        Thread({
            val bb = ByteBufferReader()
            try {
                while (running.get()) {
                    val buf = ByteArray(4096)
                    up.soTimeout = DEAD_SOCKET_MS / 2
                    val n = try {
                        up.getInputStream().read(buf)
                    } catch (_: java.net.SocketTimeoutException) {
                        continue
                    } catch (_: IOException) {
                        break
                    }
                    if (n <= 0) break
                    lastPacketAt = System.nanoTime()
                    bb.append(buf, n)
                    var consumed = true
                    while (consumed) {
                        val (frame, used) = tryDecode(bb)
                        if (frame == null) consumed = false
                        else {
                            bb.consume(used)
                            if (frame.packetType == Protocol.PACKET_PING) {
                                sendUplink(Protocol.makePong(frame.sequenceNum, frame.timestampUs))
                            }
                        }
                    }
                }
            } finally {
                // queda no uplink derruba a sessão inteira (túnel de mão dupla)
                if (running.get()) closeSockets()
            }
        }, "apex-uplink-reader").apply { isDaemon = true }.start()
    }

    private fun tryDecode(bb: ByteBufferReader): Pair<Protocol.Frame?, Int> {
        return try {
            Protocol.decode(bb.array, bb.offset, bb.size)
        } catch (e: Protocol.IncompleteFrame) {
            null to 0                       // aguarda mais bytes do socket
        } catch (e: Protocol.ProtocolError) {
            bb.reset()                      // corrompido: ressincroniza
            null to 0
        }
    }

    private fun closeSockets() {
        for (s in listOf(downSocket, upSocket)) {
            try {
                s?.close()
            } catch (_: IOException) {
            }
        }
        downSocket = null
        upSocket = null
        downOut = null
        upOut = null
        pendingPings.clear()
    }

    /** Buffer de leitura deslizante para o framing do stream TCP. */
    private class ByteBufferReader {
        var array: ByteArray = ByteArray(0)
            private set
        var offset: Int = 0
            private set
        val size: Int get() = array.size - offset

        fun append(data: ByteArray, length: Int) {
            val used = array.copyOfRange(offset, array.size)
            array = used + data.copyOf(length)
            offset = 0
        }

        fun consume(n: Int) {
            offset += n
            if (offset >= array.size) {
                array = ByteArray(0)
                offset = 0
            }
        }

        fun reset() {
            array = ByteArray(0)
            offset = 0
        }
    }
}
