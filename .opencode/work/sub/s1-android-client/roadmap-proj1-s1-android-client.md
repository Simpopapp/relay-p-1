# Roadmap — s1-android-client

> **OBSOLETO (2026-10-29):** o trabalho deste trio foi concluído e integrado nas
> Fases 1–5 do roadmap central (`.opencode/roadmap-proj1.md`), que é a única fonte
> de verdade de fases e gates. Os checkboxes abaixo desatualizados NÃO contradizem
> o estado central. Mantido como registro histórico — não executar a partir daqui.

- [ ] Fase A — Protocol.kt + CircularBuffer.kt + ProtocolTest.kt com vetores de paridade do host (gates: vetores byte-a-byte conferidos contra desktop_host/protocol.py e docs/protocol.md; decoder rejeita magic/truncado).
- [ ] Fase B — AudioTrackPlayer.kt + AudioRecordCapturer.kt (gates: buffer 2×minBufferSize; blocos de 960B com ganho/mute; sem bloqueio no thread de áudio).
- [ ] Fase C — SocketManager.kt (FSM completa) + AudioBridgeService.kt (gates: backoff 500/1000/2000→5000ms; dead socket 3000ms; flush no reconnect; locks de sistema).
- [ ] Fase D — Manifest + Gradle + MainActivity/BridgeViewModel (gates: foregroundServiceType correto; todos os controles do PRD §8.1 presentes; compilação verificável por inspeção — gradle indisponível aqui, declarar no relatório).
Gates finais: todos os arquivos da estrutura existem; paridade ABP byte-a-byte confirmada; relatório final entregue ao agente principal.
