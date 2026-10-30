# Planejamento — s3-host-ws (host HTTP+WS porta única, N=2)

## Missão
Migrar o host Windows do ApexAudio 2 para um servidor HTTP+WebSocket em porta única
59900 (Fase 3 do roadmap central), servindo a página do celular e o túnel de áudio
binário na mesma porta, com adb automatizado e oferta do VB-Cable. É o motor do
produto: sem ele a página não tem com quem falar.

## Escopo
- `apexaudio/desktop_host/ws_server.py` — HTTP + WebSocket :59900 (aiohttp), serve
  `apexaudio/web_client/` e `/ws` binário.
- Reuso/evolução de: pacing 10ms, heartbeat 1000ms, dead-socket 3s, CONFIG_SYNC,
  `protocol.py`, `audio_capture.py`, `audio_sink.py`.
- `adb_manager.py`: reverse tcp:59900 apenas, re-aplicar ao re-plugar, abrir a página
  no celular (RF3/RF4); localizar/baixar adb (RF2).
- Oferta de instalação do VB-Cable (RF5), mantendo downlink sem o driver.
- `main.py`: orquestrador com o novo servidor + console/dashboard.
- `docs/protocol.md`: seção nova "Transporte WS"; `requirements.txt` (aiohttp).
- Testes novos de WS/integração no padrão da suíte existente.

## Fora do escopo
- `apexaudio/web_client/` (página) — pacote s2-webclient (serva o diretório por
  caminho configurável; trate diretório ausente como 404 sem quebrar).
- Site TanStack (`src/`), rota /demo, integração no preview — agente principal.
- `AGENTS.md` (atualização da regra D1→D2-1) — agente principal; relate a mudança.
- PyInstaller/CI (Fase 4) e hardware real (Fase 5).

## Por quê
- Porta única = um só `adb reverse`, menos pontos de falha (D2-1); o WS dentro do
  túnel USB remove a burocracia de rede do project1.
- Pacing/heartbeat/dead-socket já provados na suíte do project1 devem sobreviver
  à migração — os gates existentes continuam verdes (CA1).

## Fronteiras
- Recebe: `web_client/` servido por caminho (não dependa do conteúdo);
  regras de transporte do `docs/protocol.md` §Regras 1–5 (valem para WS).
- Entrega: servidor + testes verdes + seção "Transporte WS" no protocol.md +
  relatório com evidências e a nova redação da regra do AGENTS.md.

## Dono exclusivo de
- `apexaudio/desktop_host/` (inteiro), `apexaudio/docs/protocol.md`.
