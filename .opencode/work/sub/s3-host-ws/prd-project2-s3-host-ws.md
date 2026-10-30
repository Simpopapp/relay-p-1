# PRD — s3-host-ws (host HTTP+WS porta única, N=2)

## Decisões técnicas já tomadas (siga sem reabrir)
- D2-1: porta única 59900, HTTP + WebSocket. D2-4: **aiohttp** (HTTP estático +
  WS maduros; áudio continua em threads fora do event loop). Adicione `aiohttp`
  ao `requirements.txt` — sem dependências além dessa.
- Cada mensagem WS binária = 1 frame ABP completo (header 16B LE + payload).
  Handshake: host envia CONFIG_SYNC (48000, 2, 1920) logo após o upgrade.
- Heartbeat: PING a cada 1000ms no downlink quando ocioso; PING no uplink após
  1000ms sem receber nada; 3000ms sem pacote completo RECEBIDO do cliente =
  sessão morta (PONG conta; áudio ecoado não). RTT via PING/PONG.
- Pacing: primeiro frame após handshake imediato; seguintes em ticks monotônicos
  de 10ms; sem rajada; acima de 3 ticks, ressincroniza. Fonte seca → silêncio
  na mesma cadência (~100 frames/s).
- Ambiente: Windows (WASAPI/VB-Cable), mas o servidor roda e é testável na sandbox
  Linux SEM áudio real (captures têm fallback silencioso — confirme em
  `audio_capture.py`/`audio_sink.py` antes de codar).

## Estado do código (confirme lendo, não presuma)
- `protocol.py` — framing ABP; `config.py` — portas/formatos; `network_server.py`
  — TCP cru das duas portas + pacing/heartbeat (referência, NÃO delete: os gates
  `test_network_server.py` precisam continuar verdes).
- `adb_manager.py` — hoje faz reverse nas DUAS portas; mude para reverse só 59900
  (Decisão D1 vira D2-1) + re-aplicação ao re-plugar + RF4 (abrir página no
  celular) + RF2 (PATH → pasta local → download platform-tools do Google;
  download só com rede; erro claro sem rede).
- `main.py` — orquestra threads; o dashboard CLI mostra: celular detectado, túnel
  (reverse ok), áudio (WASAPI/VB-Cable), RTT.
- `tests/` — suíte independente de cwd e de portas fixas; siga esse padrão
  (portas dinâmicas por teste, `tests/__init__.py` já insere a raiz).

## Estrutura nova
- `ws_server.py`: classe `WsBridgeServer(port=59900, web_dir="apexaudio/web_client")`.
  - HTTP: serve `web_dir` (index.html em /); diretório ausente → 404, sem crash.
  - `/ws`: upgrade binário; 1 conexão por vez? Não — aceite múltiplas, mas só a
    primeira em STREAMING consume o downlink (demais recebem CONFIG_SYNC + silêncio).
  - Integra `LoopbackCapture` (downlink) e `audio_sink` (uplink mono 960B) via
    threads/queues já existentes; event loop aiohttp NÃO roda áudio.
- `test_ws_server.py` (novo, padrão da suíte): cliente WS de teste (use
  `aiohttp.ClientSession.ws_connect` no teste assíncrono) que prova:
  1. CONFIG_SYNC chega logo após conectar (payload 48000/2/1920).
  2. Com fonte seca: ~100 frames/s de 1936B (números reais, tolerância ±15%).
  3. Uplink: cliente envia frame ABP canal 0x01 com 960B → sink recebe (probe).
  4. PONG do cliente preenche RTT; PING do host chega quando ocioso.
  5. Dead-socket: sem nada do cliente por ~3s, sessão encerra.
  6. HTTP: GET / serve index.html quando web_dir existe; 404 quando não.

## RF2/RF4/RF5 (sem device real: teste o caminho de decisão, não o hardware)
- RF2: `adb_manager.locate()`: PATH → pasta local → download (zip platform-tools,
  extrai `adb.exe`); sandbox: caminho de download testável com URL mockável.
- RF3/RF4: `reverse tcp:59900 tcp:59900` + `am start -a VIEW -d http://localhost:59900`;
  re-aplicar quando `adb devices` mostra replug (poll 2s).
- RF5: checa `audio_sink`/dispositivo CABLE; sem driver, oferece instalar
  (mensagem + ação de download do VB-Cable oficial) e segue com downlink.
- Sem hardware, gates = testes unitários dos caminhos com adb mockado
  (padrão de `tests/test_capture.py`: sem monkey-patch de `_run`; injete inicializador).

## docs/protocol.md — seção "Transporte WS" (append, não reescreva o resto)
- WS binário em :59900; msg = 1 frame ABP; CONFIG_SYNC do host pós-upgrade;
  heartbeat 1000ms; 3000ms sem pacote recebido = morto; cliente reconecta
  (backoff 500/1000/2000→5000); HTTP estático e WS na mesma porta.

## Entrega
- Escreva em `/tmp/remix/s3-host-ws/apexaudio/...` espelhando o projeto +
  `RELATORIO.md`. Se o ambiente der acesso de escrita/execução em `/dev-server`,
  rode a suíte DENTRO do projeto e reporte os números; se não, copie a árvore
  para /tmp, rode lá (`python3 -m unittest discover apexaudio/desktop_host/tests -v`
  de outro cwd para provar independência de cwd) e reporte.
- Relatório: números reais (frames/s, tempo até dead-socket, N testes), decisões
  (numeradas), e a redação proposta da nova regra do AGENTS.md.

## Proibições
- Não queira os gates existentes (`test_protocol.py`, `test_network_server.py`,
  `test_capture.py` — todos verdes hoje: 21/21 no roadmap central, Fase 7).
- Não delete `network_server.py` nem mude a API pública usada pelos testes.
- Não toque em `apexaudio/web_client/`, `src/`, pilares centrais/alheios.
- Sem dependências além de `aiohttp` (tests podem usar stdlib + aiohttp).

## Registro de decisões (preencha, numerado)
- (vazio)
