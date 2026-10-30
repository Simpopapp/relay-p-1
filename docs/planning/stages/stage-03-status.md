# Stage 03 — Cliente Android: downlink

**Status:** completed (verificação estática — toolchain Kotlin indisponível na sandbox)
**Data:** 2026-10-29
**Entregue:** skeleton Gradle, Manifest, Protocol.kt, CircularBuffer.kt, AudioTrackPlayer.kt, SocketManager.kt (FSM completa), ProtocolTest.kt.
**Arquivos:** apexaudio/android_client/** (15 arquivos).
**Evidências:** sintaxe balanceada em todos os .kt; ProtocolTest valida 4 vetores byte-a-byte do host; CircularBufferTest prova watermark/overrun/underrun/flush; handshake espera CONFIG_SYNC do host (fluxo validado no gate do Stage 02).
**Notas para o monitor:** gradle assembleDebug não executado (sem toolchain) — compilação fica para o remix de hardware.
