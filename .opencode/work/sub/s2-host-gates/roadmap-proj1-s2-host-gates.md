# Roadmap — subagente s2-host-gates (N=1)

## Fase A — Heartbeat do downlink
- [x] `_serve_downlink` envia PING em ociosidade ≥ 1000ms, `_ping_pending` populado antes do sendall, `last_ping_sent` independente do tráfego de áudio.
- Gates: OK — sonda: PINGs=2, `rtt_ms=10.5` (cópia) e `rtt_ms=11.0` (aplicado pelo builder).

## Fase B — Gate versionado
- [x] `tests/test_network_server.py` cobre handshake CONFIG_SYNC (48000,2,1920), downlink 1920B, pong, uplink 960B→sink, drop de payload inválido, heartbeat/RTT (+pong desconhecido, desconexão no meio).
- Gates: OK — 14/14 unittest verde em 5,014s (aplicado e reproduzido pelo builder).

## Fase C — Higiene do adb_manager
- [x] Docstring D1 (reverse ×2), portas de `config`, sem referências a `ADB_PORTS_*`/`adb forward` para 59900.
- Gates: OK — `rg "adb forward|ADB_PORTS" adb_manager.py` vazio; módulo importado OK.

## Gates finais do pacote
- [x] Suíte completa verde (14/14); nenhum arquivo fora do escopo tocado; relatório final entregue. Observação: aplicação no repositório feita pelo agente principal (sandbox sem escrita para subagentes).
