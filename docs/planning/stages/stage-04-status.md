# Stage 04 — Microfone reverso (Android ➔ PC)

**Status:** completed
**Data:** 2026-10-29
**Entregue:** AudioRecordCapturer.kt (VOICE_COMMUNICATION + fallback MIC, blocos estritos de 960B, ganho 0–2x com clamp, mute).
**Arquivos:** apexaudio/android_client/app/src/main/java/com/apex/audio/engine/AudioRecordCapturer.kt.
**Evidências:** gate do Stage 02 provou RX do host com frame mono 960B entregue ao sink e drop de frame de tamanho inválido.
**Notas para o monitor:** ganho/mute aplicados no int16 antes do TX; mute mantém os frames fluindo (heartbeat de tráfego).
