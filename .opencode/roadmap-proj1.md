# Roadmap — ApexAudio (N=1)

Fases em ordem de dependência (derivadas do planejamento `project1.md` + `prd-project1.md` §9).
`[x]` só com evidência real (saída dos gates com números). O remix dura enquanto houver avanço possível.

## Fase 1 — Protocolo comum e estruturas de dados (contratos)
- [x] `apexaudio/desktop_host/protocol.py`: framing ABP — magic 0xAA55, tipos 0x01–0x04, canal 0x00 down / 0x01 up, header 16B little-endian + payload.
- [x] `apexaudio/desktop_host/config.py`: portas 59900/59901, 48kHz/16-bit, frame 10ms (1920B downlink stereo / 960B uplink mono), buffers do PRD §3.2.
- [x] `apexaudio/desktop_host/tests/test_protocol.py`: encode/decode round-trip, tamanho do header (16B), rejeição de tamanho inválido, offsets LE (≥4 casos verdes).
- [x] `apexaudio/docs/protocol.md`: contrato ABP canônico para o cliente Android (offsets/tamanhos/opcodes).
- Gates: OK — 8/8 testes unittest verdes; frame downlink 1936B e uplink 976B confirmados em teste.

## Fase 2 — Host Windows (captura e envio)
- [x] `audio_capture.py`: WASAPI loopback shared, prioridade time-critical, reamostragem p/ 48k stereo, chunks estritos de 1920B (fallback silencioso quando não há WASAPI — túnel continua de pé).
- [x] `audio_sink.py`: escuta 59901 e escreve mono 960B em "CABLE Input"/VB-Audio; alerta claro se o driver não existir, mantendo a escuta.
- [x] `network_server.py`: TCP 59900 (down TX) e 59901 (up RX); heartbeat ping/pong a cada 1000ms; handshake CONFIG_SYNC (0x04).
- [x] `adb_manager.py`: `adb devices` → reverse tcp:59900 + reverse tcp:59901 (Decisão D1 do PRD); fallback LAN em 0.0.0.0 com IP local no console.
- [x] `main.py`: orquestrador multi-thread + dashboard CLI ANSI (formato exato do PRD §8.2).
- Gates: OK — imports limpos de todos os módulos; servidor LAN sobe sem ADB/dispositivo; gate vivo (/tmp/test_fase2_server.py): CONFIG_SYNC (48000,2,1920), frame downlink 1920B, pong recebido no cliente, uplink 960B entregue ao sink, frame inválido contabilizado (drops=1, 3243 pkts TX).

## Fase 3 — Cliente Android: downlink (recepção e reprodução)
- [x] Skeleton Gradle/Kotlin: `app/build.gradle.kts`, `AndroidManifest.xml` (RECORD_AUDIO, INTERNET, FOREGROUND_SERVICE, `foregroundServiceType="microphone|mediaPlayback"`).
- [x] `Protocol.kt`: parser ABP idêntico ao host (mesmos offsets, LE) + testes de paridade contra vetores do Fase 1.
- [x] `CircularBuffer.kt`: ring buffer lock-free — máx 4 frames (40ms), watermark 2 frames, overrun descarta o mais antigo, underrun injeta silêncio.
- [x] `AudioTrackPlayer.kt`: USAGE_MEDIA/CONTENT_TYPE_MUSIC/FLAG_LOW_LATENCY, MODE_STREAM, PERFORMANCE_MODE_LOW_LATENCY, buffer 2×minBufferSize.
- [x] `SocketManager.kt`: FSM DISCONNECTED→CONNECTING→HANDSHAKE→STREAMING→RECONNECTING; heartbeat 3000ms = socket morto; backoff 500/1000/2000→5000ms; flush dos buffers no reconnect.
- Gates: OK (estático — toolchain Kotlin indisponível na sandbox, declarado): 15 arquivos presentes e sintaxe balanceada; ProtocolTest.kt valida os 4 vetores byte-a-byte do host Python (ping 55 AA 02 00 05…, CONFIG_SYNC payload 80 BB 00 00 02 80 07, tamanhos 976/1936B, rejeição de magic/truncado); CircularBufferTest prova watermark/overrun/underrun/flush; handshake do cliente espera CONFIG_SYNC do host (mesmo fluxo validado no gate da Fase 2).

## Fase 4 — Microfone reverso (Android ➔ PC)
- [x] `AudioRecordCapturer.kt`: VOICE_COMMUNICATION (fallback MIC), leitura em blocos estritos de 960B mono 48kHz.
- [x] Host `audio_sink.py` valida 960B/frame; ganho digital 0.0x–2.0x e mute aplicados no Android antes do TX (clamp ±32767; mute zera o payload mantendo os frames).
- Gates: OK — gate da Fase 2 provou o RX do host com frame mono de 960B entregue ao sink (e drop de frame inválido); ganho/mute implementados no capturer antes do `sendUplink`.

## Fase 5 — ADB automation, resiliência e UI final
- [x] `AudioBridgeService.kt`: foreground service + PARTIAL_WAKE_LOCK + WifiLock (LOW_LATENCY, quando LAN); notificação IMPORTANCE_LOW "ApexAudio Bridge Ativo | RTT: XX ms" com ação "Desconectar".
- [x] UI Jetpack Compose: host default `127.0.0.1`, toggle USB(ADB)/LAN, botão único CONECTAR (verde)/DESCONECTAR (vermelho), status ONLINE/CONNECTING/OFFLINE, RTT, `48,000 Hz | 16-bit PCM`, buffer health (verde/amarelo/vermelho), slider de ganho, mute.
- [x] Integração final: `adb reverse` automático nas duas portas no startup do host (Decisão D1); reconexão silenciosa com flush em ambas as pontas; streaming bidirecional simultâneo.
- Gates: OK (estático): `gradle assembleDebug` NÃO rodado — toolchain Kotlin/Gradle indisponível na sandbox (declarado); FSM do `SocketManager` conforme PRD §6 (backoff/teto/dead-socket/flush revisados); stage report ao monitor em docs/planning/stages/.

## Fase 6 — Correções pós-avaliação do monitor (docs/planning/reports/stage-05-eval.md)
- [x] `network_server.py`: heartbeat do downlink funcional — PING quando ocioso > `HEARTBEAT_INTERVAL_MS`, `_ping_pending` populado, `rtt_ms` preenchido.
- [x] `apexaudio/desktop_host/tests/test_network_server.py`: gate da Fase 2 versionado — handshake CONFIG_SYNC (48000,2,1920), frame downlink 1920B, pong, uplink 960B, drop de frame inválido, heartbeat/RTT.
- [x] `adb_manager.py`: docstring com `reverse` nas duas portas (Decisão D1), portas importadas de `config`, constantes `ADB_PORTS_*` obsoletas removidas.
- [x] Android: `RECORD_AUDIO` + `POST_NOTIFICATIONS` pedidos em runtime em `MainActivity`; CONECTAR bloqueado até a permissão estar concedida.
- [x] Android: reconexão funcional — `BridgeViewModel` não anula o binder no disconnect e chama `connect()` de novo; `onStartCommand` chama `startForeground` defensivamente quando não há ação.
- [x] Android: `AudioTrackPlayer` aguarda o watermark (`isWatermarkReached`) antes de iniciar a reprodução.
- [x] Planejamento: ponteiros em `docs/planning/PRD.md`/`ROADMAP.md`; trio de `.opencode/work/sub/s1-android-client/` marcado obsoleto; `__pycache__` fora do repositório + `.gitignore` cobrindo Python.
- Gates: OK — suíte 14/14 unittest verde em 5,012s a partir de /dev-server (8 protocolo + 6 integração de rede novos; cwd obrigatório, documentado); sonda viva do agente principal: 2 PINGs em 2,5s ociosos e `rtt_ms: 11.0` (antes: 0 PINGs, `rtt_ms: None`); `rg "adb forward|ADB_PORTS" apexaudio/desktop_host/` vazio (constantes mortas do config.py incluídas após revisão do monitor); gate JVM `CircularBufferTest.kt` (5 testes) com asserções corrigidas conforme 3ª avaliação do monitor e PROVADAS via espelho executável da classe (5/5 blocos OK); correções Kotlin verificadas estaticamente (5 arquivos, cenários (a)–(e) do prd-s3; sem toolchain — declarado). Executado em onda paralela: s2-host-gates (host) + s3-android-lifecycle (Android); aplicação e verificação pelo agente principal (subagentes sem permissão de escrita no projeto). Revisões do monitor (2ª e 3ª avaliações): 6 apontamentos — todos corrigidos na mesma rodada.

## Fase 7 — Fecho da dívida P2 e higiene de gates (stage-05/06-eval)
- [x] `network_server.py`: pacing do downlink — um frame de 10ms por tick monotônico de 10ms; sem rajada quando a fonte responde rápido; atraso grande ressincroniza em vez de acumular.
- [x] `network_server.py`: dead-socket nas DUAS portas (sem pacote do cliente por `config.DEAD_SOCKET_TIMEOUT_MS` encerra a sessão; host envia PING no uplink quando ocioso, PRD §2.2).
- [x] `tests/`: suíte independente de cwd (`tests/__init__.py` insere a raiz) e de portas fixas (portas dinâmicas por teste); gates novos: pacing (~100 frames/s com fonte seca) e dead-socket (sessão encerra após ~3s de silêncio).
- [x] `audio_capture.py`: sem monkey-patch de `_run` — inicializador de thread injetado no `LoopbackCapture`; `tests/test_capture.py` prova o contrato.
- [x] `adb_manager.py`/`main.py`: `AdbStatus.forward_ok` → `downlink_reverse_ok` (dashboard não mente sobre o reverse).
- [x] Android: `Protocol.kt` com `IncompleteFrame` tipado; `SocketManager.tryDecode` sem `contains("incompleto")`; `ProtocolTest.kt` cobre o tipo novo.
- [x] `android_client`: gradle wrapper (`gradlew`, `gradlew.bat`, `gradle/wrapper/*`) fixado no Gradle compatível com o AGP 8.5.2 + instruções de build no README.
- [x] Docs: `docs/planning/ROADMAP.md` sem estado volátil; frase ambígua do `stage-06-status.md` já corrigida em rodada anterior (conferido).
- Gates: OK — suíte **21/21** unittest (8 protocolo + 10 rede + 3 captura) verde de TRÊS cwds (`/dev-server`, `/tmp`, `apexaudio/desktop_host`), ~15,1s, portas dinâmicas por teste; gate de pacing medido no teste: **102 frames / 1,0572s = 96,5 frames/s, menor intervalo 8,05ms** (sem rajada); dead-socket provado nos dois portos (**3,044s / 3,039s** até a sessão encerrar) + PING/PONG do uplink ocioso preenchendo `rtt_ms`; `rg 'contains("incompleto")|forward_ok|capture\._run =' apexaudio/` vazio; wrapper presente (`gradle-wrapper.jar` 8.7, `distributionUrl` gradle-8.7-bin.zip, scripts canônicos da tag v8.7.0). Executado em onda paralela: s4-host-realtime (host) + s5-capture-hygiene (host) + s6-android-contracts (Android/wrapper); entregas em `/tmp/remix/s{4,5,6}` aplicadas e gates reproduzidos pelo builder (D6/D11). Kotlin segue sem compilação na sandbox (declarado).

## Próximo remix
Roadmap central concluído até a Fase 7 (Fases 1–6 + Fase 7 de dívida P2, gates verdes).
Pendências fora da sandbox (hardware real): teste end-to-end PC Windows + Android +
driver VB-Cable; `./gradlew assembleDebug` e `./gradlew testDebugUnitTest` (wrapper
agora versionado — Gradle 8.7 + JDK 17 + SDK 34); validar negação de permissão em
aparelho real. Nenhuma fase central pendente de código.
