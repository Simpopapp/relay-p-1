# Planejamento — subagente s1-android-client (N=1)

## Missão
Construir o cliente Android do ApexAudio (Fases 3–5 do roadmap central): receber o downlink
PC→fone via AudioTrack de baixa latência, transmitir o microfone via AudioRecord para o PC,
sustentar a conexão com FSM resiliente e entregar a UI Compose de telemetria. Serve ao
objetivo central: fazer PC e celular funcionarem como um único "transceptor soldado" via
USB/ADB ou LAN, com latência imperceptível.

## Escopo (seu)
Todo o conteúdo de `apexaudio/android_client/`: skeleton Gradle/Kotlin, Manifest, `data/`
(Protocol.kt, CircularBuffer.kt), `engine/` (AudioTrackPlayer.kt, AudioRecordCapturer.kt),
`service/AudioBridgeService.kt`, `network/SocketManager.kt`, `ui/` (MainActivity.kt,
BridgeViewModel.kt), e os testes unitários Kotlin de Protocol/CircularBuffer.

## Fora do escopo (não toque)
- `apexaudio/desktop_host/` — pertence ao agente principal (Fase 2).
- `apexaudio/docs/protocol.md` — contrato já fixado; você consome, não altera.
- `.opencode/` (pilares centrais) e qualquer arquivo fora de `apexaudio/android_client/`.

## Por quê
Erros de latência e de framing são os dois modos de falha letais: um ring buffer com lock
ou um parser com endianness errado destrói a promessa de <20–40ms. A FSM (PRD §6) existe
para o app reconectar silenciosamente sem avisos audíveis.

## Fronteiras
- Recebe: contrato ABP (`apexaudio/docs/protocol.md` + `desktop_host/protocol.py` como
  referência de comportamento), constantes de `desktop_host/config.py`.
- Entrega: cliente Android completo e compilável; relatório final ao agente principal
  (nunca ao usuário, nunca ao oc/monitor).

## Dono exclusivo de
`apexaudio/android_client/**` (arquivos novos, nada pré-existente).
