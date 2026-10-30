# Apex Binary Protocol (ABP) — contrato canônico

Fonte de verdade: `desktop_host/protocol.py` (Python) ≡ `android_client/.../Protocol.kt` (Kotlin).
Qualquer divergência entre as duas implementações é bug; o Python é a referência.

## Cabeçalho (16 bytes, little-endian em TODO campo)

| Offset | Tamanho | Tipo    | Campo         | Valor |
|--------|---------|---------|---------------|-------|
| 0      | 2       | uint16  | MAGIC         | `0xAA55` (bytes no fio: `55 AA`) |
| 2      | 1       | uint8   | PACKET_TYPE   | `0x01` áudio, `0x02` ping, `0x03` pong, `0x04` config |
| 3      | 1       | uint8   | CHANNEL_ID    | `0x00` downlink (stereo), `0x01` uplink (mono) |
| 4      | 4       | uint32  | SEQUENCE_NUM  | contador incremental (rollback permitido) |
| 8      | 4       | uint32  | TIMESTAMP_US  | microssegundos monotônicos locais |
| 12     | 4       | uint32  | PAYLOAD_SIZE  | bytes exatos do payload |
| 16     | N       | uint8[] | PAYLOAD       | PCM linear 16-bit LE |

## Payloads

- **AUDIO (0x01):** PCM bruto. Downlink: stereo 48kHz, 1920B/frame (10ms).
  Uplink: mono 48kHz, 960B/frame (10ms).
- **PING/PONG (0x02/0x03):** payload vazio; timestamp ecoado de volta → RTT = recv_ts − ts.
- **CONFIG_SYNC (0x04):** payload de 7 bytes: `uint32 sample_rate, uint8 channels, uint16 frame_bytes` (LE). Enviado na conexão, antes do primeiro AUDIO, com `sample_rate=48000, frame_bytes=1920`.

## Regras de transporte

1. TCP fragmenta: leia SEMPRE primeiro o cabeçalho de 16 bytes, depois `PAYLOAD_SIZE` bytes
   exatos. Nunca assuma pacote por `read()`.
2. Heartbeat (D3/D7 do PRD §10): no downlink, o host envia PING a cada
   1000ms desde o ÚLTIMO PING, independentemente do áudio enviado. No uplink,
   envia PING após 1000ms sem pacote recebido e sem PING enviado. PING/PONG usa
   o canal da conexão e o registro de RTT ocorre antes de enviar o PING.
   Nas DUAS portas, 3000ms sem pacote completo RECEBIDO do cliente encerra a
   sessão; PONG conta, áudio enviado pelo host e fragmentos incompletos não.
   O cliente é responsável pela reconexão.
3. Reconexão: backoff 500/1000/2000ms (teto 5000ms), buffers locais esvaziados com flush()
   nas duas pontas.
4. Frames de áudio são descartáveis: ante a integridade, prefira descartar o frame antigo
   (ring buffer de 4 frames no Android) a acumular atraso.

5. Pacing do host: primeiro frame após handshake imediato, seguintes em ticks
   monotônicos de 10ms (`FRAME_MS`), com intervalo mínimo de um frame entre
   envios. Até três ticks de atraso, os slots vencidos são consumidos sem
   rajada de frames; acima disso, a base é ressincronizada e os ticks perdidos
   são descartados. Fonte seca envia silêncio na mesma cadência.
