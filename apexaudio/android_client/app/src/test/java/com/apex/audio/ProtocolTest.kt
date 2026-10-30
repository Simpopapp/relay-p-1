package com.apex.audio

import com.apex.audio.data.CircularBuffer
import com.apex.audio.data.Protocol
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Testes de paridade ABP contra o host Python (vetores de
 * `desktop_host/protocol.py`, gate da Fase A).
 */
class ProtocolTest {

    private fun hex(bytes: ByteArray): String =
        bytes.joinToString(" ") { "%02X".format(it) }

    @Test
    fun `ping header matches host vector`() {
        val raw = Protocol.makePing(sequenceNum = 5, timestampUs = 123456L)
        assertEquals(
            "55 AA 02 00 05 00 00 00 40 E2 01 00 00 00 00 00",
            hex(raw),
        )
    }

    @Test
    fun `config sync payload matches host vector`() {
        val raw = Protocol.makeConfigSync(48000, 2, 1920, sequenceNum = 9)
        val payload = raw.copyOfRange(16, raw.size)
        assertEquals("80 BB 00 00 02 80 07", hex(payload))
        val (frame, _) = Protocol.decode(raw)
        assertEquals(Triple(48000, 2, 1920), Protocol.parseConfigSync(frame))
    }

    @Test
    fun `frame sizes match prd`() {
        val up = Protocol.encode(Protocol.PACKET_AUDIO, Protocol.CHANNEL_UPLINK, 0, 0, ByteArray(960))
        val down = Protocol.encode(Protocol.PACKET_AUDIO, Protocol.CHANNEL_DOWNLINK, 0, 0, ByteArray(1920))
        assertEquals(976, up.size)
        assertEquals(1936, down.size)
    }

    @Test(expected = Protocol.ProtocolError::class)
    fun `rejects bad magic`() {
        val bad = ByteArray(32)
        bad[0] = 0x00
        bad[1] = 0x00
        Protocol.decode(bad)
    }

    @Test(expected = Protocol.ProtocolError::class)
    fun `rejects truncated payload`() {
        val good = Protocol.encode(Protocol.PACKET_AUDIO, Protocol.CHANNEL_DOWNLINK, 1, 0, ByteArray(1920))
        Protocol.decode(good.copyOfRange(0, 20))
    }

    @Test
    fun decode_truncated_header_throws_incomplete_frame() {
        val raw = Protocol.makePing(sequenceNum = 5, timestampUs = 123456L)
        try {
            Protocol.decode(raw.copyOfRange(0, Protocol.HEADER_SIZE - 1))
            throw AssertionError("Esperava IncompleteFrame para header truncado")
        } catch (e: Protocol.ProtocolError) {
            assertTrue(e is Protocol.IncompleteFrame)
        }
    }

    @Test
    fun decode_truncated_payload_throws_incomplete_frame() {
        val raw = Protocol.encode(Protocol.PACKET_AUDIO, Protocol.CHANNEL_DOWNLINK, 1, 0, ByteArray(1920))
        try {
            Protocol.decode(raw.copyOfRange(0, 20))
            throw AssertionError("Esperava IncompleteFrame para payload truncado")
        } catch (e: Protocol.ProtocolError) {
            assertTrue(e is Protocol.IncompleteFrame)
        }
    }

    @Test
    fun decode_negative_size_is_not_incomplete() {
        // D8 rev. (stage-07-eval P3): size negativo é corrupção de stream — o host
        // Python lê size como uint32 e trata bytes altíssimos como ProtocolError
        // (ressincroniza). O cliente NÃO pode esperar bytes que nunca chegarão.
        val raw = Protocol.makePing(sequenceNum = 5, timestampUs = 123456L)
        raw[12] = 0xFF.toByte() // PAYLOAD_SIZE little-endian: 0xFFFFFFFF
        raw[13] = 0xFF.toByte()
        raw[14] = 0xFF.toByte()
        raw[15] = 0xFF.toByte()
        try {
            Protocol.decode(raw)
            throw AssertionError("Esperava ProtocolError para size negativo")
        } catch (e: Protocol.ProtocolError) {
            assertTrue(e !is Protocol.IncompleteFrame)
        }
    }

    @Test
    fun decode_invalid_magic_is_not_incomplete() {
        val raw = Protocol.makePing(sequenceNum = 5, timestampUs = 123456L)
        raw[0] = 0x00
        raw[1] = 0x00
        try {
            Protocol.decode(raw)
            throw AssertionError("Esperava ProtocolError para magic inválido")
        } catch (e: Protocol.ProtocolError) {
            assertTrue(e !is Protocol.IncompleteFrame)
        }
    }

    @Test
    fun `round trip preserves fields`() {
        val payload = ByteArray(1920) { (it % 251).toByte() }
        val raw = Protocol.encode(Protocol.PACKET_AUDIO, Protocol.CHANNEL_DOWNLINK, 777, 42L, payload)
        val (frame, consumed) = Protocol.decode(raw)
        assertEquals(raw.size, consumed)
        assertEquals(Protocol.PACKET_AUDIO, frame.packetType)
        assertEquals(777, frame.sequenceNum)
        assertEquals(42L, frame.timestampUs)
        assertArrayEquals(payload, frame.payload)
    }
}

/** Gates da Fase A sobre o ring buffer (PRD §3.2). */
class CircularBufferTest {

    @Test
    fun `watermark gates playback start`() {
        val rb = CircularBuffer(frameBytes = 1920)
        rb.write(ByteArray(1920))
        assertTrue(!rb.isWatermarkReached)
        rb.write(ByteArray(1920))
        assertTrue(rb.isWatermarkReached)
    }

    @Test
    fun `overrun drops oldest without blocking`() {
        val rb = CircularBuffer(frameBytes = 1920)
        repeat(6) { rb.write(byteArrayOf(it.toByte()) + ByteArray(1919)) }
        assertEquals(2, rb.drops)             // 6 escritas em 4 slots → 2 drops
        assertEquals(4, rb.usedFrames)
        // o mais antigo (frame 0 e 1) foi descartado
        assertEquals(2, rb.read()!![0].toInt())
    }

    @Test
    fun `underrun returns null`() {
        val rb = CircularBuffer(frameBytes = 1920)
        assertNull(rb.read())
    }

    @Test
    fun `flush clears residual audio`() {
        val rb = CircularBuffer(frameBytes = 1920)
        rb.write(ByteArray(1920) { 7 })
        rb.flush()
        assertNull(rb.read())
    }
}
