# Roadmap — ApexAudio 2 (N=2)

Derivado de `project2.md` + `prd-project2.md`. `[x]` só com evidência real (números dos gates).

## Fase 1 — Site visível no preview (vitrine)
- [ ] Home: proposta, 4 passos de uso, botão "Baixar para Windows" (link da última release).
- [ ] /ajuda: depuração USB passo a passo, microfone no Discord, problemas comuns, antivírus.
- [ ] head() próprio em cada rota; design próprio (sem visual genérico).
- Gates: preview renderiza as rotas sem erros de console (screenshot Playwright).

## Fase 2 — Página do celular (cliente web)
- [ ] `apexaudio/web_client/` estático (index.html, app.js, worklets, manifest, sw.js), sem build.
- [ ] Downlink: WS → AudioWorklet player com buffer adaptativo 2–4 frames.
- [ ] Uplink: getUserMedia → worklet → s16 mono 960B/frame, ganho e mute.
- [ ] Parser/encoder ABP em JS com testes de paridade contra os vetores do `protocol.py`.
- [ ] /demo no site reutiliza a mesma UI com fonte de áudio simulada.
- Gates: testes JS de paridade verdes; /demo funcional no preview.

## Fase 3 — Host com HTTP + WebSocket em porta única
- [ ] Servidor HTTP+WS :59900 servindo `web_client/` e `/ws` (substitui sockets TCP crus).
- [ ] Reaproveitar pacing 10ms, heartbeat, dead-socket 3s, CONFIG_SYNC.
- [ ] `adb_manager`: só `reverse tcp:59900`, re-aplicar ao re-plugar, abrir página no celular (RF4).
- [ ] Localizar/baixar adb automaticamente (RF2); oferta de instalar VB-Cable (RF5).
- [ ] Atualizar `docs/protocol.md` (Transporte WS) e AGENTS.md (porta única substitui regra D1).
- Gates: suíte Python verde de qualquer cwd; cliente WS de teste: CONFIG_SYNC + ~100 frames/s + uplink no sink.

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
