package com.apex.audio

import com.apex.audio.data.CircularBuffer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Gate JVM do jitter buffer (PRD §3.2 + Decisão D2 do PRD §10):
 * watermark, flushGeneration, overrun e underrun — sem SDK Android,
 * roda em `testDebugUnitTest` (JUnit 4 puro).
 */
class CircularBufferTest {

    private fun newBuffer(): CircularBuffer = CircularBuffer(frameBytes = 1920)

    private fun frame(tag: Byte): ByteArray = ByteArray(1920) { tag }

    @Test
    fun `watermark exige dois frames antes de liberar`() {
        val buffer = newBuffer()
        assertFalse(buffer.isWatermarkReached)
        buffer.write(frame(1))
        assertFalse(buffer.isWatermarkReached)
        buffer.write(frame(2))
        assertTrue(buffer.isWatermarkReached)
    }

    @Test
    fun `underrun comum NAO rearma o watermark`() {
        val buffer = newBuffer()
        buffer.write(frame(1))
        buffer.write(frame(2))
        assertTrue(buffer.isWatermarkReached)
        assertEquals(frame(1).size, buffer.read()?.size)
        assertEquals(frame(2).size, buffer.read()?.size)
        assertNull(buffer.read()) // buffer seco
        // buffer seco não incrementa a geração: o player NÃO re-exige o watermark
        assertEquals(0, buffer.flushGeneration)
        // com 1 frame só, o buffer ainda não atingiu o watermark — mas o player
        // (AudioTrackPlayer) não volta a exigi-lo porque a geração não mudou
        buffer.write(frame(3))
        assertFalse(buffer.isWatermarkReached)
    }

    @Test
    fun `flush avanca a geracao e esvazia o buffer`() {
        val buffer = newBuffer()
        buffer.write(frame(1))
        buffer.write(frame(2))
        val before = buffer.flushGeneration
        buffer.flush()
        assertEquals(before + 1, buffer.flushGeneration)
        assertEquals(0, buffer.usedFrames)
        assertNull(buffer.read())
        assertFalse(buffer.isWatermarkReached) // re-exige o watermark após flush
    }

    @Test
    fun `overrun descarta o mais antigo e conta drop`() {
        val buffer = newBuffer()
        repeat(6) { buffer.write(frame(it.toByte())) }
        assertEquals(4, buffer.usedFrames)      // 6 - 2 descartados: buffer SEMPRE cheio
        assertEquals(2, buffer.drops)           // 2 frames descartados
        val first = buffer.read()               // deve ser o frame 2 (o mais antigo vivo)
        assertEquals(2.toByte(), first!![0])
    }

    @Test
    fun `flushGeneration segue monotônica entre flushes`() {
        val buffer = newBuffer()
        val g0 = buffer.flushGeneration
        buffer.flush(); buffer.flush()
        assertEquals(g0 + 2, buffer.flushGeneration)
    }
}
