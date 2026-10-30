package com.apex.audio.engine

import android.annotation.SuppressLint
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder

/**
 * Uplink engine (microfone do celular ➔ PC) — PRD §5.2.
 * VOICE_COMMUNICATION (AEC por hardware) com fallback para MIC; lê blocos
 * estritos de 960B mono 48kHz e despacha cada bloco via [onFrame].
 * Ganho (0.0x–2.0x) e mute são aplicados no int16 ANTES do TX.
 */
class AudioRecordCapturer(
    private val sampleRate: Int,
    private val frameBytes: Int,
    private val onFrame: (ByteArray) -> Unit,
) {
    @Volatile var gain: Float = 1.0f
    @Volatile var muted: Boolean = false

    @Volatile private var running = false
    private var worker: Thread? = null
    private var record: AudioRecord? = null

    /** true se o fallback MIC foi necessário (VOICE_COMMUNICATION indisponível). */
    var usedFallbackSource: Boolean = false
        private set

    @SuppressLint("MissingPermission")
    fun start() {
        if (running) return
        val minBuffer = AudioRecord.getMinBufferSize(
            sampleRate, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT
        ).coerceAtLeast(frameBytes * 2)

        var rec: AudioRecord? = null
        try {
            rec = AudioRecord(
                MediaRecorder.AudioSource.VOICE_COMMUNICATION,
                sampleRate, AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT, minBuffer,
            )
        } catch (_: IllegalArgumentException) {
            usedFallbackSource = true
        }
        if (rec == null || rec.state != AudioRecord.STATE_INITIALIZED) {
            rec?.release()
            rec = AudioRecord(
                MediaRecorder.AudioSource.MIC,
                sampleRate, AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT, minBuffer,
            )
            usedFallbackSource = true
        }
        record = rec
        rec.startRecording()
        running = true
        worker = Thread({
            val chunk = ByteArray(frameBytes)
            while (running) {
                var read = 0
                while (running && read < frameBytes) {
                    val n = rec.read(chunk, read, frameBytes - read)
                    if (n <= 0) break
                    read += n
                }
                if (read == frameBytes) {
                    onFrame(applyGainAndMute(chunk))
                }
            }
        }, "apex-uplink-capture")
        worker?.start()
    }

    private fun applyGainAndMute(chunk: ByteArray): ByteArray {
        if (muted) return ByteArray(frameBytes)
        val g = gain
        if (g == 1.0f) return chunk
        val out = chunk.copyOf()
        var i = 0
        while (i < out.size) {
            var sample = ((out[i].toInt() and 0xFF) or (out[i + 1].toInt() shl 8)).toShort()
            var amplified = (sample * g).toInt()
            if (amplified > Short.MAX_VALUE.toInt()) amplified = Short.MAX_VALUE.toInt()
            if (amplified < Short.MIN_VALUE.toInt()) amplified = Short.MIN_VALUE.toInt()
            sample = amplified.toShort()
            out[i] = (sample.toInt() and 0xFF).toByte()
            out[i + 1] = ((sample.toInt() shr 8) and 0xFF).toByte()
            i += 2
        }
        return out
    }

    fun stop() {
        running = false
        worker?.join(500)
        worker = null
        record?.let {
            try {
                it.stop()
            } catch (_: IllegalStateException) {
            }
            it.release()
        }
        record = null
    }
}
