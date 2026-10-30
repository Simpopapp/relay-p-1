package com.apex.audio.engine

import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioTrack
import com.apex.audio.data.CircularBuffer

/**
 * Downlink engine (PC ➔ fone) — PRD §5.1.
 * AudioTrack MODE_STREAM + PERFORMANCE_MODE_LOW_LATENCY, buffer 2×minBufferSize
 * (caminho Fast Track). Consome o ring buffer; underrun injeta silêncio.
 *
 * Watermark (PRD §3.2, Fase 6): a reprodução só começa após
 * [CircularBuffer.WATERMARK_FRAMES] frames (20ms) acumulados. Depois de um
 * underrun NÃO re-exige o watermark (evita soluços virarem rajadas de
 * latência); o rearme acontece somente no `flush()` do reconnect, detectado
 * pela geração de flush do buffer (PRD §6: nada de áudio residual).
 */
class AudioTrackPlayer(
    private val sampleRate: Int,
    private val frameBytes: Int,
    private val buffer: CircularBuffer,
) {
    private val silence = ByteArray(frameBytes)
    private var track: AudioTrack? = null
    @Volatile private var running = false
    private var worker: Thread? = null

    val underruns: Int get() = underrunCount.get()
    private val underrunCount = java.util.concurrent.atomic.AtomicInteger(0)

    fun start() {
        if (running) return
        val minBuffer = AudioTrack.getMinBufferSize(
            sampleRate,
            AudioFormat.CHANNEL_OUT_STEREO,
            AudioFormat.ENCODING_PCM_16BIT,
        )
        val track = AudioTrack.Builder()
            .setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_MEDIA)
                    .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                    .setFlags(AudioAttributes.FLAG_LOW_LATENCY)
                    .build()
            )
            .setAudioFormat(
                AudioFormat.Builder()
                    .setSampleRate(sampleRate)
                    .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                    .setChannelMask(AudioFormat.CHANNEL_OUT_STEREO)
                    .build()
            )
            .setTransferMode(AudioTrack.MODE_STREAM)
            .setBufferSizeInBytes(minBuffer * 2)
            .setPerformanceMode(AudioTrack.PERFORMANCE_MODE_LOW_LATENCY)
            .build()
        this.track = track
        track.play()
        running = true
        worker = Thread({
            var watermarkReached = false
            var lastFlushGeneration = buffer.flushGeneration
            while (running) {
                // flush do reconnect: re-exige o watermark antes de tocar
                val generation = buffer.flushGeneration
                if (generation != lastFlushGeneration) {
                    lastFlushGeneration = generation
                    watermarkReached = false
                }
                if (!watermarkReached && buffer.isWatermarkReached) {
                    watermarkReached = true
                }
                val frame = if (watermarkReached) buffer.read() else null
                if (frame == null) {
                    underrunCount.incrementAndGet()
                    track.write(silence, 0, frameBytes)
                } else {
                    track.write(frame, 0, frameBytes)
                }
            }
        }, "apex-downlink-player")
        worker?.start()
    }

    fun stop() {
        running = false
        worker?.join(500)
        worker = null
        track?.let {
            try {
                it.stop()
                it.flush()
                it.release()
            } catch (_: IllegalStateException) {
            }
        }
        track = null
    }
}
