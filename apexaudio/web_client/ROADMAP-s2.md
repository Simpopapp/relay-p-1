# Execução sequencial
- [x] A: ABP e paridade — 8 testes verdes.
- [x] B: downlink, ring, handshake, heartbeat e backoff — 9 testes verdes acumulados; teste de player cobre limite 4, silêncio e flush. Estado por eventos, sem polling.
- [x] C: captura mono — 10 testes verdes acumulados; clamp ±32767, ganho, mute e 960B comprovados.
- [x] D: fonte demo — 11 testes verdes acumulados; 1920B estéreo e RTT simulado; Chromium confirmou ONLINE e zero WS.
- [x] E: UI/PWA/Wake Lock implementados — Chromium 390×844 confirmou start/stop, ganho/mute, SW controlando e zero pageerrors.
- [ ] Gate de /demo integrado: agente principal.
- [ ] Hardware real, host WS, instalação PWA no telefone e Wake Lock físico: validação de integração.
