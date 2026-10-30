# PRD — subagente s3-android-lifecycle (N=1)

O COMO do pacote de ciclo de vida Android. Precedência: `project1-s3-android-lifecycle.md`.
Dúvida não coberta → decida e registre na seção "Registro de decisões".

## Decisões técnicas já tomadas (siga sem reabrir)
- **Stack:** Kotlin + Jetpack Compose (Material3), `ComponentActivity`, `AndroidViewModel`, `StateFlow`. minSdk 30, targetSdk 34.
- **Contratos fixos (não editar):** `SocketManager.kt` (FSM DISCONNECTED→CONNECTING→HANDSHAKE→STREAMING→RECONNECTING), `CircularBuffer.kt` (capacidade 4 frames, watermark 2, `usedFrames`, `drops`, `isWatermarkReached`, `flush`), `AudioRecordCapturer.kt` (960B/frame, `gain`, `muted`), `AudioBridgeService.LocalBinder` (expõe `service`), constantes de `AudioBridgeService` (CHANNEL_ID, NOTIFICATION_ID, ACTION_DISCONNECT, SAMPLE_RATE).
- **PRD §8.1:** botão único CONECTAR (verde)/DESCONECTAR (vermelho), status ONLINE/CONNECTING/OFFLINE, telemetria 4Hz, slider ganho 0–2x, mute. **Não redesenhe a UI**; mude só o fluxo de permissão/binding.
- **Decisão D1 (central):** `adb reverse` nas duas portas — irrelevante aqui, mas não "corrija" hosts padrão.

## Tarefa 1 — Permissões em runtime (`MainActivity.kt` + `BridgeViewModel.kt`)
- Em `MainActivity.onCreate`, ANTES de exibir o botão habilitado: pedir `RECORD_AUDIO` e, se SDK ≥ 33, `POST_NOTIFICATIONS` via `rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions)` (Compose) — mantenha o padrão Compose do arquivo.
- Novo estado `permissionsGranted: Boolean` no `BridgeUiState` (via ViewModel, `checkSelfPermission`); exposição no `ui: StateFlow`.
- Botão CONECTAR: desabilitado (cinza, sem clique) enquanto `permissionsGranted == false`; abaixo dele, linha de status: "Permissão de microfone necessária" quando faltar.
- Após concessão, reavaliar `permissionsGranted` automaticamente (não exigir toque extra).
- Se o usuário negar: botão segue desabilitado; sem crash, sem loop infinito de pedido (pede uma vez por entrada na tela).

## Tarefa 2 — Reconexão e binder (`BridgeViewModel.kt`)
Defeitos atuais: `toggleConnect()` (else, ~linha 108) faz `service = null` após `disconnect()` e nunca rebinda; o wait-loop de 20×100ms já cobre o primeiro connect, mas o segundo CONECTAR fica morto.

Correção:
- NUNCA anular `service` em desconexão do usuário. Manter o binder vivo (BIND_AUTO_CREATE do init já é persistente; `onServiceDisconnected` (crash do processo) apenas zera `service` e o sistema rebinda automaticamente).
- `toggleConnect()` else-branch: chamar apenas `service?.disconnect()` + estado UI DISCONNECTED. O serviço faz `stopSelf()` — com BIND_AUTO_CREATE o binding recria a instância quando necessário e `onServiceConnected` repovoará `service`; garantir que o wait-loop do connect também sirva para o reconectar (reutilizar a mesma rotina para os dois ramos).
- Idempotência: se `state != DISCONNECTED` ao clicar CONECTAR, não disparar segunda conexão.
- `onCleared` mantém unbind seguro.

## Tarefa 3 — `startForeground` defensivo (`AudioBridgeService.kt`)
- `onStartCommand`: para qualquer intent que NÃO seja `ACTION_DISCONNECT` (inclusive null/sem ação), chamar `startForegroundWithNotification(currentState)` imediatamente (requisito Android 12+/targetSdk 34 para `startForegroundService`). `ACTION_DISCONNECT` continua chamando `disconnect()`.
- Evitar chamada duplicada de `startForeground` quando já em foreground é aceitável de forma simples: chamar sempre é seguro (idempotente no Android). Registre a decisão.
- `disconnect()` continua: parar engines, liberar locks, `stopForeground(STOP_FOREGROUND_REMOVE)` + `stopSelf()`.

## Tarefa 4 — Watermark no player (`AudioTrackPlayer.kt`)
- Hoje o player escreve silêncio em underrun sem nunca consultar `isWatermarkReached` (CircularBuffer, watermark = 2 frames = 20ms, PRD §3.2).
- Correção: enquanto `!ringBuffer.isWatermarkReached` E nunca tiver atingido o watermark desde o último flush, reproduzir silêncio (mantém o AudioTrack alimentado); uma vez atingido, reproduzir frames do buffer; em underrun posterior, silêncio (política do PRD) e — importante — NÃO voltar a exigir watermark até o próximo `flush()` (evita "burst" de latência a cada soluço).
- Manter o contrato público da classe (construtor + `start()`/`stop()`) intacto — o serviço consome como hoje.
- Remover código morto apontado pelo monitor se trivial (`PROPERTY_OUTPUT_LATENCY`/`TAG` não usados) — mesma dono de arquivo, mudança segura.

## Casos de borda e testes esperados
- Verificação é ESTÁTICA (não há toolchain Kotlin/Gradle na sandbox): conferir por leitura que cada alteração compila "no papel" (imports corretos, `@OptIn`/ExperimentalComposeApi quando necessário, null-safety).
- Cenários a provar no relatório: (a) primeiro connect com permissão concedida; (b) negação → botão desabilitado, sem crash; (c) desconectar→conectar → `connect()` executado de novo; (d) `startForegroundService` sem ação → não crash; (e) watermark: reprodução só após 2 frames, sem re-exigência após underrun.

## Tools e skills recomendadas
- Leitura atenta dos 4 arquivos + `CircularBuffer.kt`/`AudioRecordCapturer.kt`/`SocketManager.kt` (contratos) antes de editar.
- `rg -n "requestPermissions|checkSelfPermission|isWatermarkReached"` para confirmar o antes/depois.

## Registro de decisões do subagente
(vazio — preencha numerado: D-s3-1, D-s3-2, …)

## Proibições
- Não editar manifest, gradle, `SocketManager.kt`, `Protocol.kt`, `CircularBuffer.kt`, `AudioRecordCapturer.kt`, testes existentes, nada em `apexaudio/desktop_host/**`, pilares centrais, roadmap central.
- Não criar módulos novos nem dependências.
- Não perguntar ao usuário; não usar oc/monitor; não finalizar o remix.
