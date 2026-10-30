# Avaliação — Stage 08

**Data:** 2026-10-30
**Veredito:** concluída (escopo Fases 1–3 do roadmap-proj2)
**Confiança da avaliação:** alta

## Resumo executivo

As três fases declaradas (site vitrine, página do celular, host HTTP+WS porta única) estão presentes no código e os gates foram reproduzidos de forma independente pelo monitor: **35/35 unittest Python (20,5s)** e **11/11 node --test (145ms)**, batendo com os números do status. O preview foi verificado pelo monitor em `/`, `/demo` e `/ajuda`: as três rotas renderizam com títulos `head()` distintos e **zero erros de console**. O veredito é concluída para o escopo da rodada, com duas observações de qualidade (bind `0.0.0.0` e RF8 parcial) que não bloqueiam, mas devem ser tratadas antes da Fase 4 gerar o exe público.

## Cobertura de requisitos

- **Atendido:**
  - **RF11 (site):** home com hero, 4 passos, duas vias e download (`src/routes/index.tsx`); `/ajuda` com os 5 blocos e âncoras (`src/routes/ajuda.tsx`); `/demo` reutilizando a UI real do cliente em iframe (`src/routes/demo.tsx`); `head()` próprio e títulos distintos nas três rotas (verificado no preview: "ApexAudio — O áudio do PC, pelo cabo USB" / "Demo — ApexAudio no celular" / "Ajuda ApexAudio — Do cabo à primeira conexão").
  - **RF6–RF8, RF10 (página):** botão único Conectar com gesto (`app.js` `start()`), downlink via AudioWorklet player com buffer 0–4 frames, uplink `getUserMedia` → capturer → s16 960B, ganho 0–2x e mute na UI (`index.html`), Wake Lock (`app.js` `lock()`), manifest + sw.js no `index.html`.
  - **RF9:** reconexão com backoff 500/1000/2000/5000ms implementada em `app.js` (linha 14) e documentada em `protocol.md`.
  - **RF2/RF3/RF4 (host):** `adb_manager.py` `locate()` com PATH → pasta local → download oficial do ZIP (com rejeição de path traversal no ZIP), reverse único `tcp:59900` re-aplicado ao re-plugar (comparação de serial em `poll()`), abertura da página via `am start` (RF4).
  - **RF5:** `offer_cable_install` chamado em `main.py`; downlink funciona sem VB-Cable (testado nos gates com fonte seca).
  - **D2-1:** porta única confirmada — `ws_server.py` serve HTTP estático + `/ws` em 59900; referências a 59901 restam apenas no legado (`config.py`, `network_server.py`), coerente com a regra do AGENTS.md (TCP legado só para regressão).
  - **Protocolo:** `apexaudio/docs/protocol.md` tem a seção "Transporte WS" (linha 47) com CONFIG_SYNC pós-upgrade, pacing 10ms, PING 1000ms, dead-socket 3000ms, backoff — tudo implementado em `ws_server.py` e confirmado pelos 8 testes WS.
  - **CA1/CA2/CA5:** reproduzidos pelo monitor (gates verdes; preview sem erros).
- **Parcial:**
  - **RF8 ("echoCancellation/noiseSuppression configuráveis"):** `app.js` fixa `echoCancellation:false, noiseSuppression:false, autoGainControl:false` sem toggle na UI. O default é sensato (voz sem processamento), mas o requisito fala em "configuráveis" — ou se adiciona toggle, ou se ajusta o wording do PRD.
  - **CA3 (metade real):** a parte "página abre via host e conecta em modo real" depende de hardware (Fase 5); a parte "/demo funciona no preview" está verificada.
- **Ausente / não evidenciado (fora do escopo desta rodada, correto):**
  - **CA4 (CI gera o exe)** — Fase 4, blocker externo (repositório GitHub).
  - **Validação em hardware real** — Fase 5, blocker externo (usuário).

## Qualidade do código

**Pontos fortes:**
- `ws_server.py` é enxuto (119 linhas) e fiel ao protocolo: valida 1 frame ABP por mensagem WS (`used != len(msg.data)` rejeita concatenação), valida uplink (canal 1, 960B), controla PING/PONG com dedupe por `(seq, ts)`, e protege o file server contra path traversal (`is_relative_to`).
- Pacing resiliente: ticks vencidos até 30ms são consumidos sem rajada; acima disso ressincroniza (linhas 111–117), exatamente como `protocol.md` descreve.
- `adb_manager.py` `locate()` valida o ZIP antes de extrair (rejeita entradas fora de `platform-tools/` e path traversal) — cuidado incomum e correto para download de binário.
- Cliente web sem build, JS puro, com 4 suítes de teste incluindo paridade byte-exata ABP contra `protocol.py`.
- Testes cobrem os comportamentos de contrato (CONFIG_SYNC, ~100,6 frames/s, dead-socket 3,00s nas duas vias, HTTP 404, frame inválido, múltiplos clientes).

**Pontos de atenção:**
1. **`main.py` linha 72: bind `0.0.0.0`.** O PRD D2-6 coloca LAN fora do escopo, e o servidor WS não tem autenticação. O comentário no código justifica ("replug sem rebind"), mas o efeito é expor o túnel de áudio e o file server a toda a rede local. É uma decisão de segurança que merece ser explícita (documentar no protocol.md/ajuda ou voltar a `127.0.0.1` com re-bind no replug).
2. **`ws_server.py` linha 29:** `site._server.sockets[0]` usa internals privados do aiohttp — frágil entre versões (requirements pinam `aiohttp>=3.9,<4`, o que mitiga).
3. **`ws_server.py` linha 49:** `self.stats._bump(...)` acessa método privado de `HostStats` — acoplamento menor.
4. **`adb_manager.py` linhas 43–48:** imports no meio do ficheiro (`shutil`, `os`, `urllib.request`, etc.) — dívida de estilo, funcional.
5. **`app.js` é denso** (linhas longas, lógica inline) — aceitável para o objetivo "sem build", mas qualquer evolução de UI vai custar mais do que custaria com módulos menores.

## Discrepâncias

Entre o status registrado e o código, **não há divergências materiais**: todos os artefatos declarados existem, os números dos gates batem (35/35 em 20,5s vs "20,6s" declarado; 11/11 em 145ms vs "143ms"), e as regras D2-1 estão em código, protocol.md e AGENTS.md. Duas imprecisões menores do status:
- O status diz "RF8 ... ganho e mute" sem mencionar que EC/NS estão fixos (ver parcial acima).
- O status afirma verificação Playwright do demo ONLINE (RTT ~12ms, buffer 3/4). O monitor não conseguiu reproduzir o clique dentro do iframe com a tool de screenshot MCP (o clique atingiu o elemento iframe, não o botão interno — limitação da tool, não do app). O estado interativo fica coberto pela suíte JS (`demo.test.mjs`) e pela verificação Playwright declarada do builder; anotado como fronteira de verificação, não como falha.

## Riscos para as próximas etapas

1. **Bind `0.0.0.0` no exe público (Fase 4):** se seguir assim para release, qualquer pessoa na rede local pode consumir o áudio do usuário. Decidir/documentar antes do primeiro exe.
2. **URL provisória de release:** o download do site aponta para `github.com/apexaudio/apexaudio/releases/latest` — repositório ainda não conectado (blocker da Fase 4). Se a Fase 4 atrasar, o botão principal do site fica morto; considerar estado de "em breve" ou confirmar o repo cedo.
3. **PyInstaller + aiohttp (D2-4):** o spec da Fase 4 precisa embutir `web_client/` como data files e o aiohttp aumenta o exe; sem teste do exe gerado, o risco é descobrir falta de assets só no hardware real (Fase 5).
4. **Legado 59901 vivo em `config.py`/`network_server.py`:** intencional (regressão), mas o dashboard de `main.py` ainda referencia `config.PORT_DOWNLINK` do legado na linha de status — conferir que a Fase 5 de limpeza não quebra os 21 testes legados preservados.

## Recomendações

1. **Antes da Fase 4:** decidir o bind (`127.0.0.1` + re-bind no replug, ou manter `0.0.0.0` documentando a exposição LAN no protocol.md e na /ajuda). Prioridade média-alta por tocar segurança do exe público.
2. **Fase 4:** no `ApexAudio.spec`, incluir `web_client/` como datas e validar o exe gerado abrindo `http://localhost:59900` localmente antes de publicar a release.
3. **Baixa prioridade:** mover os imports de `adb_manager.py` para o topo; substituir `site._server.sockets[0]` por leitura da porta configurada; resolver o "configuráveis" do RF8 (toggle ou rewording do PRD).
4. **Rastreabilidade:** o status stage-08 está legível e com números reais; manter o padrão nas próximas etapas.

## Evidências consultadas

- `docs/planning/stages/stage-08-status.md`
- `.opencode/roadmap-proj2.md` (Fases 1–3 marcadas com gates; Fases 4–5 pendentes)
- `.opencode/prd-project2.md` (RF1–RF11, D2-1…D2-6, CA1–CA5)
- Gates reproduzidos pelo monitor: `python3 -m unittest discover -s apexaudio/desktop_host/tests -t /dev-server` → 35/35 OK (20,5s); `node --test apexaudio/web_client/tests/*.test.mjs` → 11/11 OK (145ms)
- Código inspecionado: `apexaudio/desktop_host/ws_server.py`, `adb_manager.py`, `main.py`, `requirements.txt`; `apexaudio/docs/protocol.md` (seção "Transporte WS"); `apexaudio/web_client/` (app.js, index.html, tests/); `src/routes/{index,ajuda,demo}.tsx`, `src/components/site/site-shell.tsx`
- Preview verificado no browser (monitor): `/`, `/demo`, `/ajuda` — render corretos, títulos distintos, console sem erros; clique dentro do iframe da demo não alcançável pela tool MCP (limitação anotada)
- `/tmp/observability/` — build-errors.log ("build OK"), runtime-errors.log e console-logs.log vazios
