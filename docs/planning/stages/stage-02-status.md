# Stage 02 — Host Windows (captura e envio)

**Status:** completed
**Data:** 2026-10-29
**Entregue:** audio_capture.py (WASAPI loopback + reamostragem + fallback silencioso), audio_sink.py (VB-Cable), network_server.py (59900/59901 + heartbeat + CONFIG_SYNC), adb_manager.py (reverse nas duas portas), main.py (dashboard ANSI), requirements.txt.
**Arquivos:** apexaudio/desktop_host/{audio_capture.py,audio_sink.py,network_server.py,adb_manager.py,main.py,requirements.txt}.
**Evidências:** imports limpos; gate vivo (/tmp/test_fase2_server.py): CONFIG_SYNC (48000,2,1920) recebido, frame downlink 1920B, pong round-trip, uplink 960B no sink, drop contabilizado (drops=1 em 3243 pkts TX).
**Notas para o monitor:** correção aplicada em rede — sendall bloqueante + select p/ leitura (timeout de 0.05s matava o fluxo); ADB usa `adb reverse` nas duas portas (Decisão D1 do PRD §10).
