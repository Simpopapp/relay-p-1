# Planejamento — s2-webclient (página do celular, N=2)

## Missão
Construir a página que roda no Chrome do celular (Fase 2 do roadmap central): cliente
web estático do ApexAudio 2 que recebe o áudio do PC (downlink) e envia o microfone
ao PC (uplink) por WebSocket, com modo demonstração para o site. Serve ao objetivo
central: zero instalação no celular — só abrir `localhost:59900`.

## Escopo
- `apexaudio/web_client/` inteiro: `index.html`, `app.js`, `abp.js`, worklets
  (`player-worklet.js`, `capturer-worklet.js`), `demo-source.js`, CSS,
  `manifest.webmanifest`, `sw.js`.
- Implementação ABP em JS byte-exata com o `protocol.py` (contrato em
  `apexaudio/docs/protocol.md`), com testes de paridade.
- Modo demonstração (`?demo=1`): mesma UI, fonte de áudio simulada, sem WS —
  consumido pelo /demo do site.

## Fora do escopo
- Rotas do site (`/demo` do TanStack) — agente principal.
- Servidor/host Python (HTTP+WS :59900) — pacote s3-host-ws.
- Integração no preview (pasta `public/`, plugin de cópia) — agente principal.

## Por quê
- Fase 2 é o coração do produto (cliente real); a paridade ABP garante interop
  com o host — qualquer desvio de framing quebra o túnel inteiro.
- O modo demo desacopla o site do host: a vitrine mostra o produto sem hardware.

## Fronteiras
- Recebe: contrato ABP (vetores byte-exatos do agente principal), contrato do
  modo demo (`?demo=1`), formato dos worklets.
- Entrega: web_client completo + testes que rodam com `node --test` +
  relatório com evidências.

## Dono exclusivo de
- `apexaudio/web_client/` (inteiro) e `apexaudio/web_client/tests/`.
