# Planejamento — subagente s3-android-lifecycle (N=1)

## Missão
Tornar o cliente Android do ApexAudio utilizável no primeiro toque real: pedir as
permissões em runtime antes de conectar, consertar o ciclo de vida do serviço/binder
(para que desconectar→conectar funcione e o foreground service não crash) e respeitar
o watermark do jitter buffer na reprodução. Sem isso, o teste de hardware externo
falha no primeiro CONECTAR e mascara todo o resto (avaliação do monitor).

## Escopo (exclusivo)
- `apexaudio/android_client/app/src/main/java/com/apex/audio/ui/MainActivity.kt` — fluxo de permissão em runtime.
- `apexaudio/android_client/app/src/main/java/com/apex/audio/ui/BridgeViewModel.kt` — binder/reconexão + estado de permissão.
- `apexaudio/android_client/app/src/main/java/com/apex/audio/service/AudioBridgeService.kt` — `startForeground` defensivo no `onStartCommand`.
- `apexaudio/android_client/app/src/main/java/com/apex/audio/engine/AudioTrackPlayer.kt` — gate de watermark.

## Fora do escopo
- `SocketManager.kt`, `Protocol.kt`, `CircularBuffer.kt`, `AudioRecordCapturer.kt`, manifest, gradle, testes Kotlin existentes (mudança ali exige relatório ao agente principal).
- Qualquer arquivo do host Python (pacote s2-host-gates), pilares centrais, arquivos de outros subagentes.

## Por quê
Monitor provou: zero ocorrências de `requestPermissions|checkSelfPermission` no
projeto — `AudioRecord.startRecording()` lança `SecurityException` em aparelho real
(minSdk 30). `BridgeViewModel.toggleConnect()` anula `service = null` ao desconectar e
nunca rebinda → segundo CONECTAR morto. `onStartCommand` sem ação não chama
`startForeground` → risco de `ForegroundServiceDidNotStartInTimeException` em
targetSdk 34 (segundo `startForegroundService`). `isWatermarkReached` nunca é
consultado — o player inicia em underrun constante, contrariando PRD §3.2.

## Fronteiras
- Recebe: código atual das 4 classes, PRD §3.2/§5/§6/§8.1, avaliação do monitor (stage-05-eval.md).
- Entrega: código corrigido + relatório final; verificação é estática (sem toolchain Kotlin na sandbox) — declarar isso nos gates.
- Não fala com o usuário, não usa `oc`, não marca o roadmap central.
