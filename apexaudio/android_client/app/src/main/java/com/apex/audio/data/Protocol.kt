package com.apex.audio.data

import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Apex Binary Protocol (ABP) — parser idêntico ao `desktop_host/protocol.py`.
 * Contrato canônico: `apexaudio/docs/protocol.md`. Cabeçalho de 16 bytes,
 * little-endian em TODOS os campos multi-byte.
 */
object Protocol {
    const val MAGIC: Int = 0xAA55
    const val PACKET_AUDIO: Int = 0x01
    const val PACKET_PING: Int = 0x02
    const val PACKET_PONG: Int = 0x03
    const val PACKET_CONFIG_SYNC: Int = 0x04
    const val CHANNEL_DOWNLINK: Int = 0x00
    const val CHANNEL_UPLINK: Int = 0x01
    const val HEADER_SIZE: Int = 16

    open class ProtocolError(message: String) : Exception(message)

    class IncompleteFrame(message: String) : ProtocolError(message)

    data class Frame(
        val packetType: Int,
        val channelId: Int,
        val sequenceNum: Int,
        val timestampUs: Long,
        val payload: ByteArray,
    )

    fun encode(
        packetType: Int,
        channelId: Int,
        sequenceNum: Int,
        timestampUs: Long,
        payload: ByteArray = ByteArray(0),
    ): ByteArray {
        val buf = ByteBuffer.allocate(HEADER_SIZE + payload.size)
            .order(ByteOrder.LITTLE_ENDIAN)
        buf.putShort(MAGIC.toShort())
        buf.put(packetType.toByte())
        buf.put(channelId.toByte())
        buf.putInt(sequenceNum)
        buf.putInt(timestampUs.toInt())
        buf.putInt(payload.size)
        buf.put(payload)
        return buf.array()
    }

    /**
     * Decodifica o primeiro frame contido em [buffer] a partir de [offset].
     * Retorna (frame, bytes consumidos). Levanta [IncompleteFrame] se o buffer
     * não contém um frame completo; [ProtocolError] se magic/size forem inválidos.
     */
    fun decode(buffer: ByteArray, offset: Int = 0, length: Int = buffer.size - offset): Pair<Frame, Int> {
        if (length < HEADER_SIZE) {
            throw IncompleteFrame("buffer incompleto: $length < $HEADER_SIZE")
        }
        val bb = ByteBuffer.wrap(buffer, offset, length).order(ByteOrder.LITTLE_ENDIAN)
        val magic = bb.short.toInt() and 0xFFFF
        if (magic != MAGIC) throw ProtocolError("magic inválido: 0x" + magic.toString(16))
        val type = bb.get().toInt() and 0xFF
        val channel = bb.get().toInt() and 0xFF
        val sequence = bb.int
        val timestampUs = bb.int.toLong() and 0xFFFFFFFFL
        val size = bb.int
        if (size < 0) {
            // Corrupção de stream (no host Python o size é uint32: bytes altíssimos
            // viram "payload incompleto" → ProtocolError → ressincroniza). Mesma
            // semântica aqui: NÃO é espera de bytes, é erro de protocolo (D8 rev.).
            throw ProtocolError("size inválido: $size")
        }
        if (length - HEADER_SIZE < size) {
            throw IncompleteFrame("payload incompleto: tem " + (length - HEADER_SIZE) + " de " + size)
        }
        val payload = ByteArray(size)
        bb.get(payload)
        return Frame(type, channel, sequence, timestampUs, payload) to (HEADER_SIZE + size)
    }

    fun makeConfigSync(sampleRate: Int, channels: Int, frameBytes: Int, sequenceNum: Int): ByteArray {
        val payload = ByteBuffer.allocate(7).order(ByteOrder.LITTLE_ENDIAN)
            .putInt(sampleRate)
            .put(channels.toByte())
            .putShort(frameBytes.toShort())
            .array()
        return encode(PACKET_CONFIG_SYNC, CHANNEL_DOWNLINK, sequenceNum, 0L, payload)
    }

    fun parseConfigSync(frame: Frame): Triple<Int, Int, Int> {
        require(frame.packetType == PACKET_CONFIG_SYNC && frame.payload.size == 7) {
            "CONFIG_SYNC inválido"
        }
        val bb = ByteBuffer.wrap(frame.payload).order(ByteOrder.LITTLE_ENDIAN)
        return Triple(bb.int, bb.get().toInt() and 0xFF, bb.short.toInt() and 0xFFFF)
    }

    fun makePing(sequenceNum: Int, timestampUs: Long): ByteArray =
        encode(PACKET_PING, CHANNEL_DOWNLINK, sequenceNum, timestampUs)

    fun makePong(sequenceNum: Int, timestampUs: Long): ByteArray =
        encode(PACKET_PONG, CHANNEL_DOWNLINK, sequenceNum, timestampUs)
}
