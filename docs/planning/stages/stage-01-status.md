# Stage 01 — Protocolo comum e estruturas de dados

**Status:** completed
**Data:** 2026-10-29
**Entregue:** `desktop_host/protocol.py` (ABP 16B LE), `desktop_host/config.py`, contrato canônico `apexaudio/docs/protocol.md`.
**Arquivos:** apexaudio/desktop_host/{protocol.py,config.py,__init__.py,tests/test_protocol.py}, apexaudio/docs/protocol.md.
**Evidências:** 8/8 testes unittest verdes; frame downlink 1936B / uplink 976B confirmados.
**Notas para o monitor:** vetores byte-a-byte servem de base de paridade para o Kotlin (ProtocolTest.kt).
