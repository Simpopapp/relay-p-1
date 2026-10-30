# Roadmap — s3-host-ws (N=2, pacote host porta única)

## Fase A — Servidor WS
- [ ] `ws_server.py`: HTTP estático + `/ws` binário, CONFIG_SYNC pós-upgrade,
      pacing 10ms, heartbeat 1000ms, dead-socket 3s (reuso do network_server).
- Gates: módulo importa limpo; servidor sobe na sandbox sem áudio real.

## Fase B — Testes de WS/integração
- [ ] `test_ws_server.py`: 6 provas do prd-s3 (CONFIG_SYNC, ~100 frames/s,
      uplink no sink, RTT/PING, dead-socket, HTTP/404).
- Gates: suíte completa verde de ≥2 cwds; números reais no relatório.

## Fase C — adb e VB-Cable
- [ ] `adb_manager.py`: reverse único 59900, re-aplicação ao re-plugar, RF4, RF2.
- [ ] RF5: oferta de instalação do VB-Cable sem bloquear o downlink.
- [ ] `main.py`: orquestração nova + dashboard atualizado.
- Gates: caminhos unit-testados com adb mockado; sem hardware exigido.

## Fase D — Documento e fechamento
- [ ] `docs/protocol.md`: seção "Transporte WS".
- [ ] `requirements.txt`: aiohttp; RELATORIO.md com evidências + redação AGENTS.md.
- Gates: CA1 (suíte toda verde) confirmado no relatório.
