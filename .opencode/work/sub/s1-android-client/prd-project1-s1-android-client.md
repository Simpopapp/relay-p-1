# PRD — subagente s1-android-client

Referências: PRD central §2 (ABP), §3 (buffering), §5 (engines), §6 (FSM), §8.1 (UI).
O contrato ABP canônico está em `apexaudio/docs/protocol.md` — implemente EXATAMENTE esse
layout (header 16B LE, magic 0xAA55, offsets 0/2/3/4/8/12). Divergência = bug de paridade.

## Decisões técnicas já tomadas (siga sem mudar)
1. **Kotlin + Jetpack Compose**, minSdk 30, targetSdk 34, package `com.apex.audio`.
2. **Downlink:** `AudioTrack` MODE_STREAM + PERFORMANCE_MODE_LOW_LATENCY +
   USAGE_MEDIA/CONTENT_TYPE_MUSIC/FLAG_LOW_LATENCY; buffer interno 2×getMinBufferSize()
   (caminho Fast Track).
3. **Uplink:** `AudioRecord` com VOICE_COMMUNICATION e fallback para MIC (constante de
   escolha no código, preferência salta em ConfigSync), blocos estritos de 960B mono 48kHz.
4. **Rede:** dois sockets TCP — connect em 59900 (downlink RX) e 59901 (uplink TX). Host
   default 127.0.0.1 (ADB) ou IP LAN escolhido na UI.
5. **FSM:** DISCONNECTED → CONNECTING → HANDSHAKE → STREAMING → RECONNECTING (PRD §6).
   Sem pacote por 3000ms = socket morto. Backoff 500/1000/2000ms, teto 5000ms. Flush de
   buffers nas duas pontas ao reconectar. Reconexão silenciosa (sem som, sem toast).
6. **Ring buffer:** lock-free (AtomicInteger read/write index, array pre-alocado), 4 frames
   de 1920B, watermark 2 frames, overrun descarta o frame mais antigo, underrun injeta
   silêncio (zeros) — nunca bloqueia o thread de áudio.
7. **Serviço:** `AudioBridgeService` foreground, `foregroundServiceType="microphone|mediaPlayback"`,
   PARTIAL_WAKE_LOCK durante stream, WifiLock WIFI_MODE_FULL_LOW_LATENCY só em modo LAN,
   notificação IMPORTANCE_LOW com RTT e ação "Desconectar".
8. **Ganho de microfone:** multiplicação PCM no int16 antes do TX (clamp ±32767), slider
   0.0x–2.0x; mute zera o payload mantendo os frames fluindo (heartbeat de tráfego).

## Contratos que você consome
- ABP: header `<HBBIII` LE — magic 0xAA55, type, channel, seq u32, ts_us u32, size u32, payload.
- CONFIG_SYNC payload 7B: `uint32 sample_rate, uint8 channels, uint16 frame_bytes`.
- Portas: 59900 downlink (você CONECTA como cliente TCP), 59901 uplink (você SERVE como
  cliente também — conecta ao host; o host escuta 59901).
- Constantes do PRD: 48000 Hz, 16-bit, frame 10ms.

## Estrutura de arquivos (crie todos)

```
android_client/
├── settings.gradle.kts
├── build.gradle.kts                      # raiz, plugins androidApplication+kotlin alias
├── gradle.properties                     # Jetifier off, AndroidX on
├── app/build.gradle.kts                  # compose, minSdk 30, targetSdk 34
├── app/src/main/AndroidManifest.xml      # permissões + service + activity
└── app/src/main/java/com/apex/audio/
    ├── data/Protocol.kt                  # encode/decode ABP + CONFIG_SYNC + ping/pong
    ├── data/CircularBuffer.kt            # ring buffer lock-free (regra 6)
    ├── engine/AudioTrackPlayer.kt        # reprodução downlink
    ├── engine/AudioRecordCapturer.kt     # captura uplink com ganho/mute
    ├── service/AudioBridgeService.kt     # foreground service + wakelocks
    ├── network/SocketManager.kt          # FSM + sockets + heartbeat + reconexão
    ├── ui/MainActivity.kt                # tela única Compose
    ├── ui/BridgeViewModel.kt             # estado da UI (StateFlow)
    └── test/java/com/apex/audio/ProtocolTest.kt   # paridade ABP (vetores abaixo)
```

## Escopo por fase (aceite mensurável)
**Fase A (data + rede núcleo):** Protocol.kt e CircularBuffer.kt completos; ProtocolTest.kt
com estes vetores exatos do host Python (verifique contra `desktop_host/protocol.py`):
- header de frame ping seq=5 ts=123456 payload vazio = `55 AA 02 00 05 00 00 00 40 E2 01 00 00 00 00 00`.
- CONFIG_SYNC(48000,2,1920,seq=9): payload = `80 BB 00 00 02 80 07`.
- frame uplink com payload de 960B tem 976B de total; downlink 1920B → 1936B.
- decoder rejeita magic errado e payload truncado.

**Fase B (engines):** AudioTrackPlayer (loop de escrita de frames do ring buffer) e
AudioRecordCapturer (leitura de 960B, ganho, mute, TX imediato).

**Fase C (rede + serviço):** SocketManager com FSM completa, heartbeat ping 1000ms sem
tráfego, RTT via pong, reconexão backoff; AudioBridgeService com locks e notificação.

**Fase D (UI + integração):** MainActivity/BridgeViewModel: toggle USB/LAN, campo host,
botão único CONECTAR/DESCONECTAR, status, RTT, `48,000 Hz | 16-bit PCM`, barra de buffer
health (verde <3 frames, amarelo 3, vermelho drops>0), slider ganho 0–2x, mute.

## Casos de borda que você deve provar (em teste ou comentário de design)
- Overrun: escrita com buffer cheio descarta o mais antigo SEM bloquear.
- Underrun: leitura com buffer vazio retorna silêncio e o player continua.
- Sequência com salto (drop detectado via SEQUENCE_NUM): não reinicia, apenas registra.
- Reconexão: nenhum áudio residual antigo tocado após reconnect (flush antes de retomar).

## Tools do ambiente
Use `code--write` para criar arquivos e `code--line_replace` para correções. Verifique
sintaxe conferindo o arquivo final com `code--view` após escrever. NÃO rode gradle
(toolchain indisponível); NÃO rode o dev server web. Validação = seus testes Kotlin
estáticos + conformidade estrita com os vetores de paridade acima.

## Registro de decisões (preencha, numerado)
(vazio — preencha no seu relatório)

## Proibições
- Não editar nada fora de `apexaudio/android_client/` (nem docs, nem host, nem .opencode).
- Não instalar dependências além de: compose, lifecycle, coroutines (todas no gradle).
- Não perguntar ao usuário; decisões vão no seu registro e no relatório final.
- Não usar oc/monitor; não marcar o roadmap central.
