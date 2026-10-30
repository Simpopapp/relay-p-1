package com.apex.audio.data

import java.util.concurrent.atomic.AtomicInteger

/**
 * Ring buffer lock-free do jitter buffer (PRD §3.2):
 * - máx [CAPACITY_FRAMES] frames (40ms);
 * - watermark de [WATERMARK_FRAMES] frames antes de começar a reproduzir;
 * - overrun: descarta o frame mais antigo (avança o read pointer), nunca bloqueia;
 * - underrun: [read] retorna null e o player injeta silêncio sintético.
 *
 * Segurança do lock-free: cada slot é uma referência única trocada por última
 * escrita; o consumidor copia a referência antes do CAS do ponteiro, portanto
 * um frame descartado por overrun só pode ser lido com dados no-older que o
 * slot — a política de áudio tolera isso (frame descartável).
 */
class CircularBuffer(
    private val frameBytes: Int,
    private val capacityFrames: Int = CAPACITY_FRAMES,
) {
    private val slots = Array(capacityFrames) { ByteArray(frameBytes) }
    private val writeIdx = AtomicInteger(0)
    private val readIdx = AtomicInteger(0)
    private val dropsCounter = AtomicInteger(0)
    private val flushGenerationCounter = AtomicInteger(0)

    var lastDroppedSequence: Int = -1
        private set

    val drops: Int get() = dropsCounter.get()

    /**
     * Geração de flush: incrementa a cada [flush]. O player compara para
     * re-exigir o watermark somente após um flush real (reconnect), e nunca
     * após um underrun comum — `usedFrames == 0` não distingue os dois casos.
     */
    val flushGeneration: Int get() = flushGenerationCounter.get()

    val usedFrames: Int get() = writeIdx.get() - readIdx.get()

    val isWatermarkReached: Boolean get() = usedFrames >= WATERMARK_FRAMES

    /** Escreve um frame. Overrun descarta o mais antigo e contabiliza o drop. */
    fun write(frame: ByteArray) {
        if (frame.size != frameBytes) return
        while (true) {
            val w = writeIdx.get()
            val r = readIdx.get()
            if (w - r >= capacityFrames) {
                // overrun: libera um slot descartando o mais antigo
                if (readIdx.compareAndSet(r, r + 1)) {
                    dropsCounter.incrementAndGet()
                }
                continue
            }
            slots[Math.floorMod(w, capacityFrames)] = frame.copyOf()
            if (writeIdx.compareAndSet(w, w + 1)) return
        }
    }

    /** Lê o frame mais antigo ou null se vazio (underrun → silêncio no player). */
    fun read(): ByteArray? {
        while (true) {
            val r = readIdx.get()
            val w = writeIdx.get()
            if (w - r <= 0) return null
            val frame = slots[Math.floorMod(r, capacityFrames)]
            if (readIdx.compareAndSet(r, r + 1)) return frame
        }
    }

    /** Flush no reconnect (PRD §6: nada de áudio residual). Avança a geração. */
    fun flush() {
        readIdx.set(writeIdx.get())
        flushGenerationCounter.incrementAndGet()
    }

    companion object {
        const val CAPACITY_FRAMES: Int = 4
        const val WATERMARK_FRAMES: Int = 2
    }
}
