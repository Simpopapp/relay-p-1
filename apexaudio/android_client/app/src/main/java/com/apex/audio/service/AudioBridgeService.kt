package com.apex.audio.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Binder
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import android.net.wifi.WifiManager
import androidx.core.app.NotificationCompat
import com.apex.audio.R
import com.apex.audio.data.CircularBuffer
import com.apex.audio.engine.AudioRecordCapturer
import com.apex.audio.engine.AudioTrackPlayer
import com.apex.audio.network.BridgeState
import com.apex.audio.network.SocketManager

/**
 * Foreground service do túnel (PRD §5.3): mantém o stream vivo em background
 * com PARTIAL_WAKE_LOCK (sempre) e WifiLock LOW_LATENCY (só em modo LAN).
 * Notificação IMPORTANCE_LOW com RTT e ação "Desconectar".
 */
class AudioBridgeService : Service() {

    inner class LocalBinder : Binder() {
        val service: AudioBridgeService get() = this@AudioBridgeService
    }

    private val binder = LocalBinder()
    private var socketManager: SocketManager? = null
    private var player: AudioTrackPlayer? = null
    private var capturer: AudioRecordCapturer? = null
    private var wakeLock: PowerManager.WakeLock? = null
    private var wifiLock: WifiManager.WifiLock? = null
    private val ringBuffer = CircularBuffer(frameBytes = 1920)

    @Volatile var currentState: BridgeState = BridgeState.DISCONNECTED
        private set

    @Volatile var currentRtt: Float = -1f
        private set

    override fun onBind(intent: Intent?): IBinder = binder

    fun connect(host: String, lanMode: Boolean) {
        if (socketManager != null) return
        acquireLocks(lanMode)
        startForegroundWithNotification(BridgeState.CONNECTING)
        player = AudioTrackPlayer(SAMPLE_RATE, 1920, ringBuffer).also { it.start() }
        capturer = AudioRecordCapturer(SAMPLE_RATE, 960) { frame ->
            socketManager?.sendUplink(frame)
        }.also { it.start() }
        socketManager = SocketManager(
            host = host,
            onState = { state ->
                currentState = state
                updateNotification()
                if (state == BridgeState.RECONNECTING || state == BridgeState.CONNECTING) {
                    ringBuffer.flush()
                }
            },
            onRtt = { rtt ->
                currentRtt = rtt
            },
            onDownlinkAudio = { payload -> ringBuffer.write(payload) },
            onFlushBuffers = { ringBuffer.flush() },
        ).also { it.connect() }
    }

    fun disconnect() {
        socketManager?.disconnect()
        socketManager = null
        capturer?.stop()
        capturer = null
        player?.stop()
        player = null
        releaseLocks()
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    fun setMicGain(gain: Float) {
        capturer?.gain = gain
    }

    fun setMicMuted(muted: Boolean) {
        capturer?.muted = muted
    }

    val bufferFrames: Int get() = ringBuffer.usedFrames
    val bufferDrops: Int get() = ringBuffer.drops
    val bufferHealthPercent: Int
        get() = (ringBuffer.usedFrames * 100) / CircularBuffer.CAPACITY_FRAMES

    private fun acquireLocks(lanMode: Boolean) {
        val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
        wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "ApexAudio::bridge").apply {
            acquire(30 * 60 * 1000L)
        }
        if (lanMode) {
            val wm = applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
            @Suppress("DEPRECATION")
            wifiLock = wm.createWifiLock(WifiManager.WIFI_MODE_FULL_LOW_LATENCY, "ApexAudio::wifi").apply {
                acquire()
            }
        }
    }

    private fun releaseLocks() {
        try {
            if (wakeLock?.isHeld == true) wakeLock?.release()
        } catch (_: SecurityException) {
        }
        wakeLock = null
        try {
            if (wifiLock?.isHeld == true) wifiLock?.release()
        } catch (_: SecurityException) {
        }
        wifiLock = null
    }

    private fun startForegroundWithNotification(state: BridgeState) {
        val manager = getSystemService(NotificationManager::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            manager.createNotificationChannel(
                NotificationChannel(CHANNEL_ID, "ApexAudio Bridge", NotificationManager.IMPORTANCE_LOW)
            )
        }
        val notification = buildNotification(state)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(
                NOTIFICATION_ID, notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE or
                    ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK,
            )
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }
    }

    private fun updateNotification() {
        val manager = getSystemService(NotificationManager::class.java)
        manager?.notify(NOTIFICATION_ID, buildNotification(currentState))
    }

    private fun buildNotification(state: BridgeState): Notification {
        val rtt = if (currentRtt >= 0) " | RTT: %.1f ms".format(currentRtt) else ""
        val statusLine = when (state) {
            BridgeState.STREAMING -> "Transmitindo áudio via USB/LAN$rtt"
            BridgeState.RECONNECTING -> "Reconectando (silencioso)…"
            BridgeState.HANDSHAKE -> "Negociando handshake…"
            BridgeState.CONNECTING -> "Conectando…"
            BridgeState.DISCONNECTED -> "Desconectado"
        }
        val openIntent = PendingIntent.getActivity(
            this, 0,
            Intent(this, com.apex.audio.ui.MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE,
        )
        val disconnectIntent = PendingIntent.getService(
            this, 1,
            Intent(this, AudioBridgeService::class.java).setAction(ACTION_DISCONNECT),
            PendingIntent.FLAG_IMMUTABLE,
        )
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_bridge)
            .setContentTitle("ApexAudio Bridge Ativo")
            .setContentText(statusLine)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .setContentIntent(openIntent)
            .addAction(0, "Desconectar", disconnectIntent)
            .build()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_DISCONNECT) {
            disconnect()
        } else {
            // Defesa targetSdk 34 (Fase 6): startForegroundService sem ação
            // exige promoção a foreground no ato — evita
            // ForegroundServiceDidNotStartInTimeException no reconectar.
            startForegroundWithNotification(currentState)
        }
        return START_STICKY
    }

    override fun onDestroy() {
        disconnect()
        super.onDestroy()
    }

    companion object {
        const val CHANNEL_ID = "apexaudio_bridge"
        const val NOTIFICATION_ID = 1
        const val ACTION_DISCONNECT = "com.apex.audio.DISCONNECT"
        const val SAMPLE_RATE = 48000
    }
}
