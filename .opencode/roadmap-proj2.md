# Roadmap — ApexAudio 2 (N=2)

Derivado de `project2.md` + `prd-project2.md`. `[x]` só com evidência real (números dos gates).

## Fase 1 — Site visível no preview (vitrine)
- [x] Home: proposta, 4 passos de uso, botão "Baixar para Windows" (link da última release).
- [x] /ajuda: depuração USB passo a passo, microfone no Discord, problemas comuns, antivírus.
- [x] head() próprio em cada rota; design próprio (sem visual genérico).
- Gates: OK — Playwright desktop: / e /ajuda renderizam com SiteShell (nav Início/Demo/Ajuda), hero, 4 passos, duas vias e download; zero pageerror/console.error; head() completo e títulos distintos nas duas rotas; download aponta para `github.com/apexaudio/apexaudio/releases/latest` (URL provisória — confirmar repositório/release na Fase 4).

## Fase 2 — Página do celular (cliente web)
- [x] `apexaudio/web_client/` estático (index.html, app.js, worklets, manifest, sw.js), sem build.
- [x] Downlink: WS → AudioWorklet player com buffer adaptativo 2–4 frames.
- [x] Uplink: getUserMedia → worklet → s16 mono 960B/frame, ganho e mute.
- [x] Parser/encoder ABP em JS com testes de paridade contra os vetores do `protocol.py`.
- [x] /demo no site reutiliza a mesma UI com fonte de áudio simulada.
- Gates: OK — `node --test apexaudio/web_client/tests/*.test.mjs` 11/11 (ABP 5 vetores byte-exatos contra o protocol.py + round-trip + rejeições + player/capturer/demo); Playwright no preview: iframe /web/index.html?demo=1 inicia em ONLINE (RTT ~12ms simulado, buffer 3/4), badge "Demonstração", sem pageerror, sem WebSocket em modo demo.

## Fase 3 — Host com HTTP + WebSocket em porta única
- [x] Servidor HTTP+WS :59900 servindo `web_client/` e `/ws` (substitui sockets TCP crus).
- [x] Reaproveitar pacing 10ms, heartbeat, dead-socket 3s, CONFIG_SYNC.
- [x] `adb_manager`: só `reverse tcp:59900`, re-aplicar ao re-plugar, abrir página no celular (RF4).
- [x] Localizar/baixar adb automaticamente (RF2); oferta de instalar VB-Cable (RF5).
- [x] Atualizar `docs/protocol.md` (Transporte WS) e AGENTS.md (porta única substitui regra D1).
- Gates: OK — suíte 35/35 unittest de `/dev-server` (21 legado + 8 WS: CONFIG_SYNC, ~100,66 frames/s, uplink no sink, RTT/PING, dead-socket 3,0028s, HTTP/404, múltiplos clientes, frame inválido + 6 adb mockado); TCP legado preservado para regressão (97,22 frames/s no CA1); docs/protocol.md com seção "Transporte WS"; AGENTS.md com regra D2-1.

## Próximo remix
Fase 4 (blocker externo: repositório GitHub conectado para o CI gerar o exe):
`ApexAudio.spec` PyInstaller + `.github/workflows/build-host.yml` + link do site para a release real.
Fase 5: arquivar `apexaudio/android_client/` + validação real em hardware (blocker: usuário).
Pronto para Fase 4: host WS completo e testado; web_client estático servível pelo exe.

## Fase 4 — Executável sem esforço do usuário
- [ ] `ApexAudio.spec` PyInstaller onefile com web_client embutido.
- [ ] `.github/workflows/build-host.yml` (windows-latest) → artefato + release em tag.
- [ ] Site aponta para a release mais recente.
- Gates: run do CI gera o exe (blocker externo: repositório GitHub conectado).

## Fase 5 — Limpeza e validação real
- [ ] Arquivar `apexaudio/android_client/` (fora da manutenção) e atualizar README.
- [ ] Teste real em hardware: latência medida, Discord recebendo voz (blocker externo: usuário).

## Próximo remix
Começar pela Fase 1 + Fase 2 (resolvem o preview vazio e já mostram o produto).
