# Roadmap — subagente s3-android-lifecycle (N=1)

## Fase A — Permissões em runtime
- [x] `MainActivity` pede RECORD_AUDIO (+POST_NOTIFICATIONS em SDK≥33) via launcher Compose; `BridgeUiState.permissionsGranted`; CONECTAR desabilitado até conceder, com aviso visível.
- Gates: OK (estático) — `rg` confirma `checkSelfPermission`/`rememberLauncherForActivityResult` no projeto; leitura prova negação sem crash e sem loop (reavaliação só em callback/onResume). Aplicado pelo agente principal (sandbox sem escrita p/ subagente).

## Fase B — Reconexão e foreground
- [x] `BridgeViewModel` não anula o binder no disconnect; reconnect executa `connect()`; idempotência no toggle (`connectJob`).
- [x] `AudioBridgeService.onStartCommand` chama `startForegroundWithNotification` para intent sem ação (defesa targetSdk 34).
- Gates: OK (estático) — leitura prova os cenários (a)–(d); nenhum contrato alterado.

## Fase C — Watermark no player
- [x] `AudioTrackPlayer` só reproduz após `isWatermarkReached` (2 frames), sem re-exigir após underrun até o próximo flush (via `flushGeneration` nova em `CircularBuffer` — Decisão D2 do PRD central, extensão de contrato autorizada pelo agente principal); código morto (`AudioManager`, companion TAG) removido.
- Gates: OK (estático) — leitura prova cenário (e); contrato público da classe preservado (nova propriedade somente leitura).

## Gates finais do pacote
- [x] Relatório final com as 5 provas estáticas; implementação aplicada e conferida pelo agente principal; nenhum arquivo fora do escopo além da extensão D2 autorizada.
