# Roadmap — s2-webclient (N=2, pacote página do celular)

## Fase A — Contrato ABP em JS
- [ ] `abp.js` completo (encode/decode/feedStream/config-sync) conforme prd-s2.
- [ ] `tests/abp.test.mjs` com os 5 vetores byte-exatos + round-trip + rejeições.
- Gates: `node --test` verde (N testes, números reais no relatório).

## Fase B — Downlink e player
- [ ] `player-worklet.js` com ring buffer 2–4 frames, underrun=silêncio,
      overrun descarta o mais antigo.
- [ ] `app.js`: WS binário, feedStream, handshake CONFIG_SYNC, PING/PONG 1000ms,
      reconexão com backoff.
- Gates: fluxo de estado OFFLINE→CONECTANDO→ONLINE implementado; sem polling.

## Fase C — Uplink e captura
- [ ] `capturer-worklet.js`: getUserMedia → float→s16 mono 960B, ganho 0–2x, mute.
- [ ] Envio como frames ABP canal 0x01.
- Gates: clamp ±32767 provado no teste unitário do capturer (se possível) ou no
  code review do relatório.

## Fase D — Modo demo
- [ ] `demo-source.js` + integração `?demo=1` (sem WS, sem microfone, badge "Demonstração").
- Gates: demo produz áudio simulado pelo mesmo caminho do player.

## Fase E — PWA e polimento
- [ ] `manifest.webmanifest` + `sw.js` (cache dos assets); Wake Lock quando disponível.
- [ ] UI final: status, RTT, buffer health, ganho, mute, botão único.
- Gates: checklist RF6/RF9/RF10 conferido no relatório.
