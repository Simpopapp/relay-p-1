# Stage 08 — ApexAudio 2 (N=2): Fases 1–3 do roadmap-proj2

**Data:** 2026-10-30
**Escopo da rodada:** Fase 1 (site vitrine), Fase 2 (página do celular) e Fase 3 (host HTTP+WS porta única).
**Execução:** enxame de 3 subagentes (s1-site, s2-webclient, s3-host-ws) com pilares em `.opencode/work/sub/`; integração, gates e verificação pelo agente principal.

## O que foi entregue

- **Fase 1:** `src/routes/index.tsx` (home: hero, 4 passos, duas vias, download), `src/routes/ajuda.tsx` (5 blocos com âncoras), `src/components/site/site-shell.tsx`; head() completo e distinto por rota; /demo (`src/routes/demo.tsx`) com iframe do cliente real em modo demonstração.
- **Fase 2:** `apexaudio/web_client/` completo (abp.js, app.js, player/capturer worklets, demo-source, manifest, sw.js, ícones) + 4 suites de teste; paridade ABP byte-exata contra `protocol.py`; demo `?demo=1` sem WebSocket e sem permissão de microfone.
- **Fase 3:** `apexaudio/desktop_host/ws_server.py` (HTTP + `/ws` binário :59900, CONFIG_SYNC pós-upgrade, pacing 10ms, heartbeat 1000ms, dead-socket 3s), `adb_manager.py` (reverse único 59900, replug, RF2/RF4, RF5 VB-Cable), `main.py` assíncrono + dashboard, `docs/protocol.md` seção "Transporte WS", `requirements.txt` com aiohttp. TCP legado preservado só para regressão.

## Gates (números reais)

- Python: `python3 -m unittest discover -s apexaudio/desktop_host/tests -t /dev-server` — **35/35 OK, 20,6s** (21 legado preservados + 8 WS + 6 adb).
- WS: CONFIG_SYNC pós-upgrade; **~100,6 frames/s** com fonte seca; uplink 960B entregue ao sink; dead-socket **3,00s** nas duas vias.
- JS: `node --test apexaudio/web_client/tests/*.test.mjs` — **11/11 OK, 143ms**.
- Preview (Playwright desktop): / e /ajuda renderizam sem pageerror/console.error; /demo inicia ONLINE (RTT ~12ms simulado, buffer 3/4), badge "Demonstração", zero WebSockets em modo demo.
- Documentação: AGENTS.md atualizado com a regra D2-1 (porta única substitui D1 do project1).

## Decisões centrais desta rodada

- D2-1 aplicada em código, protocol.md e AGENTS.md (uma porta, um reverse).
- Contrato ABP JS fixado em vetores byte-exatos (PING/PONG/CONFIG_SYNC/áudio) em `prd-project2-s2-webclient.md`.
- Modo demo desacoplado do host (sem WS, fonte simulada) para a vitrine funcionar sem hardware.

## Pendências (blockers externos)

- Fase 4: repositório GitHub conectado para o CI gerar o `ApexAudio.exe`; URL de release provisória no site.
- Fase 5: validação em hardware real (Windows + Android + VB-Cable); arquivar `android_client/`.
