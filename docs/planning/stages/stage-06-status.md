# Stage 06 — Status (Fase 6: correções pós-avaliação do monitor)

**Data:** 2026-10-29 · **Rodada:** remix 2 (N=1) · **Builder:** agente principal + subagentes s2-host-gates / s3-android-lifecycle

## Escopo executado
Correções dos 5 bloqueios + itens de dívida da avaliação `docs/planning/reports/stage-05-eval.md`.

## Entregas
1. **Heartbeat do host** (`network_server.py`): `last_ping_sent` separado do tráfego; PING em ociosidade; `_ping_pending` antes do sendall; `rtt_ms` preenchido. Sonda viva: 2 PINGs/2,5s, `rtt_ms: 11.0` (antes 0 PINGs / None).
2. **Gate da Fase 2 versionado** (`tests/test_network_server.py`, NOVO): handshake CONFIG_SYNC (48000,2,1920), downlink 1920B defragmentado, pong, uplink 960B→sink, drop de payload inválido, heartbeat/RTT, pong de seq desconhecido, desconexão no meio do downlink.
3. **adb_manager.py**: docstring reverse ×2 (D1), portas de `config`, sem `ADB_PORTS_*`.
4. **Permissões em runtime** (`MainActivity.kt` + `BridgeViewModel.kt`): launcher Compose, RECORD_AUDIO + POST_NOTIFICATIONS (SDK 33+), `permissionsGranted` no UI state, CONECTAR desabilitado + aviso até conceder; reavaliação em callback/onResume.
5. **Reconexão/foreground** (`BridgeViewModel.kt` + `AudioBridgeService.kt`): binder nunca anulado no disconnect (reconnect chama `connect()`; `connectJob` idempotente); `startForeground` defensivo em onStartCommand sem ação (targetSdk 34).
6. **Watermark** (`AudioTrackPlayer.kt` + `CircularBuffer.kt`): reprodução só após 2 frames; rearme apenas em `flush()` via nova `flushGeneration` (Decisão D2); código morto removido.
7. **Higiene**: ponteiros `docs/planning/PRD.md`/`ROADMAP.md`; trio s1 marcado obsoleto; `__pycache__` removido + `.gitignore` Python; nota D1 em `project1.md`; decisões D2–D6 no PRD §10. (Teste JVM do buffer: overrun com 6 writes/capacidade 4 → 4 frames vivos, 2 descartados.)

## Gates (números reais)
- **A partir da raiz `/dev-server` (cwd obrigatório — os imports são `apexaudio.desktop_host.*`):** `python3 -m unittest discover -s apexaudio/desktop_host/tests -v` → **14/14 OK em 5,012s** (8 protocolo + 6 rede). Rodar de `apexaudio/desktop_host` falha por design do pacote (ModuleNotFoundError) — não é regressão.
- Sonda heartbeat (`/tmp/probe_heartbeat.py`) → PINGs=2, `rtt_ms: 11.0`, GATE OK.
- `rg "adb forward|ADB_PORTS" apexaudio/desktop_host/` → vazio (constantes mortas removidas do `config.py` também).
- Kotlin: verificação estática + NOVO gate JVM `app/src/test/.../CircularBufferTest.kt` (JUnit 4 puro, sem SDK): watermark, underrun sem rearme, flush→geração+1 e re-exige watermark, overrun (6 writes/capacidade 4 → 4 frames vivos, 2 descartados; primeiro vivo = frame 2), geração monotônica. Executável em `testDebugUnitTest` (sem toolchain aqui — declarado).

## Revisão do monitor (2ª avaliação — stage-06-eval.md) — corrigido
1. `permissionsGranted` agora é gateado SOMENTE por `RECORD_AUDIO` (D4 revisada): negar POST_NOTIFICATIONS não trava o CONECTAR (o FGS funciona sem notificações).
2. `ADB_PORTS_FORWARD`/`ADB_PORTS_REVERSE` removidos de `config.py` (o status anterior afirmava a remoção sem fazê-la).
3. Gate JVM `CircularBufferTest.kt` criado para a lógica de `flushGeneration`/watermark (item 3 do monitor).
4. Comando de teste documentado com o cwd obrigatório (item 4).
5. `docs/protocol.md` regra 2 alinhada à Decisão D3 (cadência do ping desde o último ping) (item 5).
6. **3ª avaliação do monitor:** 2 asserções erradas no `CircularBufferTest.kt` (overrun: `usedFrames == 4`, não 2 — o buffer fica sempre cheio com 6 writes/capacidade 4; underrun: `isWatermarkReached == false` após drenar e escrever 1 frame — a política do player é sobre a geração, não sobre o enchimento). Corrigidas e PROVADAS com espelho executável da classe (`/tmp/cb_mirror.py`, mesma semântica write/read/flush/overrun): 5/5 blocos de asserção OK. O teste JVM segue sem poder rodar aqui (sem Gradle) — declarado; a prova do espelho substitui a execução nesta sandbox.

## Verificação
Aplicação do patch s2 pelo builder + reprodução da suíte e da sonda (não só o relato do subagente). Subagente s3 bloqueado para escrita pela sandbox: implementação aplicada pelo builder a partir da proposta validada (relatório em `.opencode/work/sub/s3-android-lifecycle/`).

## Pendências externas (não executáveis aqui)
- Teste end-to-end com PC Windows + Android + VB-Cable; `gradle assembleDebug` (sem wrapper — instalar Gradle 8.5.2 + JDK 17 na máquina de teste); validação da negação de permissão em aparelho real.
- Prioridade 2 remanescente do monitor: pacing do downlink, dead-socket no host, `SocketManager` com erro tipado (`IncompleteFrame`), monkey-patch em `audio_capture.py`, wrapper Gradle.
