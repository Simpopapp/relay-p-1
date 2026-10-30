# Avaliação — Stage 07

**Data:** 2026-10-30
**Veredito:** concluída
**Confiança da avaliação:** alta (host provado em execução; Android provado apenas estaticamente — limitação de ambiente declarada desde a Fase 3 e mantida nesta etapa)

## Resumo executivo

A Fase 7 fechou integralmente a dívida P2 deixada pelas avaliações de stage-05 e stage-06: pacing do downlink, dead-socket nas duas portas, suíte independente de cwd/porta, captura sem monkey-patch, `IncompleteFrame` tipado no Android e gradle wrapper versionado. Reproduzi os gates nesta avaliação: **21/21 unittest OK de três cwds** (`/dev-server`, `/tmp`, `apexaudio/desktop_host`), pacing medido (~92–96 frames/s, min_gap 6,1–9,0ms), dead-socket em ~3,04s nas duas portas. O status registrado pelo builder corresponde ao código; nenhuma discrepância material encontrada.

## Cobertura de requisitos

Itens da Fase 7 do roadmap (`.opencode/roadmap-proj1.md`) e da dívida P2 (stage-05-eval rec. 9 / stage-06-eval rec. 8):

- **Atendido e provado em execução (host):**
  - Pacing do downlink (D7) — `network_server.py:160-183`: primeiro frame imediato, ticks de `config.FRAME_MS` (10ms), atraso ≤3 ticks consome slots, >3 ticks ressincroniza; fonte seca envia silêncio na mesma cadência (`chunk is None` → zeros, linha 157-159). Gate `test_pacing_dry_source_is_throttled` (test_network_server.py:173) asserciona 90–120 frames/1,05s e min_gap ≥5ms. Minhas execuções: 97 frames/92,1/s (min_gap 6,26ms), 101/95,45 (6,10ms), 101/96,14 (8,98ms) — sem rajada, consistente com o claim de 96,5/s do status (variância de timing esperada).
  - Dead-socket nas duas portas (D7) — downlink: `last_received` só avança com frame **completo** recebido (PONG conta; áudio enviado pelo host e fragmentos não — linhas 146-148, 154, 174); uplink: linha 249. Gates `test_dead_socket_{downlink,uplink}_closes_session` medem ~3,04s (minhas execuções: 3,008/3,046; 3,042s uplink). PING do uplink ocioso reutiliza `_send_ping`/`_ping_pending` (linha 251-256) e `test_idle_uplink_ping_pong_populates_rtt` prova `rtt_ms` preenchido.
  - Suíte independente de cwd/porta (D10) — `tests/__init__.py` insere a raiz (`parents[3]`) no `sys.path`; shim `runpy` nos módulos de teste para discovery com `-s` absoluto; portas dinâmicas por teste. **Reproduzido por mim: 21/21 OK dos três cwds** (15,09s / 15,09s).
  - Captura sem monkey-patch — `audio_capture.py:86-91,97-101,152-165`: `thread_initializer` injetado e executado dentro da thread (`_run`), exceções engolidas (best-effort); `ImportError` de `pyaudiowpatch` cai no modo silencioso; `open_loopback_capture` injeta a prioridade win32 via closure, sem `capture._run = …`. `test_capture.py` (3 testes) prova o contrato, incluindo inicializador que falha sem derrubar a captura.
- **Atendido e verificado estaticamente (Android — sem toolchain, declarado):**
  - `IncompleteFrame` tipado (D8) — `Protocol.kt:21-23` (`ProtocolError` agora `open`, `IncompleteFrame : ProtocolError`); `decode` lança nos dois casos de incompletude (header truncado, linha 59; payload insuficiente **incluindo `size < 0`**, linha 70); `SocketManager.tryDecode` (linha 270-275) decide por tipo: `IncompleteFrame` → aguarda bytes, `ProtocolError` → ressincroniza. `ProtocolTest.kt` cobre os três cenários (linhas 65-91: header truncado, payload truncado, erro genérico ≠ IncompleteFrame). `rg 'contains\("incompleto"\)'` → vazio (conferido nesta avaliação).
  - Gradle wrapper (D9) — `gradlew` (executável, 8714B), `gradlew.bat`, `gradle/wrapper/gradle-wrapper.jar` (43453B, **zip íntegro — testado por mim com zipfile, 33 entradas**) e `gradle-wrapper.properties` com `distributionUrl=gradle-8.7-bin.zip`. README de build com JDK 17/SDK 34 e a matriz AGP 8.5.2→Gradle 8.7.
- **Atendido (docs/higiene):**
  - `AdbStatus.forward_ok` → `downlink_reverse_ok` (`adb_manager.py:24`; `main.py:35` condiciona o "Routed" do dashboard às duas flags). `rg 'forward_ok'` → vazio.
  - `apexaudio/docs/protocol.md` regras 2 e 5: heartbeat bidirecional (PING no uplink ocioso; dead-socket de 3000ms nas duas portas com a semântica exata "PONG conta, áudio do host e fragmentos não") e pacing (ticks de 10ms, consumo de ≤3 ticks, ressincronização acima disso).
  - `docs/planning/ROADMAP.md` segue como ponteiro estável, sem estado volátil (conferido).
- **Ausente / não evidenciado:** nada dentro do escopo da fase. Fora do escopo por definição de ambiente: compilação Kotlin/Gradle e teste end-to-end de hardware (PC + celular + VB-Cable) — ambos declarados no status e no roadmap ("Próximo remix").

## Qualidade do código

**Pontos fortes:**
- A lógica de pacing é correta e defensiva: `deadline = max(base + tick*interval, last_audio_sent + interval)` garante intervalo mínimo entre envios reais mesmo após ressincronização; o consumo de ticks vencidos (`tick = max(tick, int((now-base)/interval))`) evita rajada sem acumular atraso.
- Dead-socket com semântica precisa: `last_received` distingue pacote completo recebido de tráfego de saída; `_send_ping` poda pendências antigas (`cutoff`), evitando crescimento do dict com clientes mudos.
- Testes novos medem comportamento, não implementação: pacing por intervalos observados, dead-socket por tempo até o contador de clientes zerar, RTT por efeito colateral observável.
- Bootstrap de testes resolve o caso real de discovery com `-s` absoluto (que não executa `__init__` de pacote) com shim explícito e documentado no próprio arquivo.

**Pontos de atenção (nenhum bloqueia a fase):**
1. **Semântica de `size < 0` no Kotlin (D8):** `Protocol.kt:70` lança `IncompleteFrame` para tamanho negativo. Um size negativo é **corrupção de stream**, não buffer incompleto — o caminho `IncompleteFrame` faz o cliente esperar bytes que nunca completarão o frame, em vez de ressincronizar. O impacto é limitado (dead-socket de 3s → reconexão), mas `ProtocolError` seria o tipo correto. Nota de paridade: o host Python não tem o problema na prática (`feed_stream` pré-checa tamanhos e nunca chama `decode` com prefixo incompleto), mas o `decode` Python aceitaria size negativo como payload vazio — assimetria inofensiva hoje, relevante se alguém reutilizar `decode` direto.
2. `test_capture.py:49-53` testa via `capture._put` (método privado) — aceitável para provar a política de overrun, mas acopla o teste à interna.
3. O gate de pacing asserciona `min_gap ≥ 5ms` enquanto o status cita 8,05ms — a folga é intencional (timing de scheduler), mas vale registrar que o número do status é uma amostra, não um invariante.

## Discrepâncias

Nenhuma material. Todos os números do status foram reproduzidos nesta avaliação (21/21 nos três cwds; pacing ~92–96/s; dead-socket ~3,04s; greps vazios; wrapper íntegro). Única variação: min_gap de pacing observado entre 6,1ms e 9,0ms nas minhas execuções vs. 8,05ms no status — dentro da asserção do teste e esperado por variância de agendamento.

## Riscos para as próximas etapas

1. **Kotlin continua sem execução real** — `IncompleteFrame`, `tryDecode` e o wrapper só serão provados no primeiro `./gradlew testDebugUnitTest` externo. O wrapper agora versionado reduz o atrito, mas a prova segue pendente (risco herdado, não criado nesta fase).
2. **Teste end-to-end de hardware** (PC Windows + Android + VB-Cable) permanece externo — o pacing a 96,5 frames/s e o dead-socket em 3s precisam ser confirmados com o túnel USB real e o cliente de verdade.
3. **`size < 0` → `IncompleteFrame`** (atenção 1 acima): se um stream corromper um header, o cliente stall-a até o dead-socket em vez de ressincronizar imediatamente — degradação aceitável, mas é o primeiro candidato a ajuste se o hardware real mostrar reconexões lentas após corrupção.

## Recomendações

- **P3 (não bloqueia):** trocar `IncompleteFrame` por `ProtocolError` no caso `size < 0` de `Protocol.kt:70` (corrupção ≠ incompletude) e adicionar o caso ao `ProtocolTest.kt`. Pode entrar na próxima onda de dívida ou no ajuste pós-primeiro build externo.
- **P3:** no `decode` Python, rejeitar `size < 0` explicitamente (hoje produziria payload vazio) para paridade defensiva com o contrato documentado em `protocol.md`.
- Nenhuma ação P1/P2 pendente desta fase. O roadmap central está concluído; o próximo passo declarado ("Próximo remix") é externo à sandbox e não gera etapa de código.

## Evidências consultadas

- `docs/planning/PRD.md` (ponteiro) → `.opencode/prd-project1.md` (§2.2, §6, §10 D1/D6/D7–D11)
- `docs/planning/ROADMAP.md` (ponteiro) → `.opencode/roadmap-proj1.md` (Fase 7, "Próximo remix")
- `docs/planning/stages/stage-07-status.md`; `docs/planning/reports/stage-05-eval.md` (rec. 5–9) e `stage-06-eval.md` (rec. 8, atenção 3–4)
- Código inspecionado: `apexaudio/desktop_host/{network_server,audio_capture,adb_manager,main,config,protocol}.py`, `tests/{__init__,test_capture,test_network_server,test_protocol}.py`
- Android (estático): `data/Protocol.kt`, `network/SocketManager.kt`, `app/src/test/java/com/apex/audio/ProtocolTest.kt`, `gradle/wrapper/*`, `gradlew*`, `README.md`
- `apexaudio/docs/protocol.md` (regras 2 e 5)
- Execuções nesta avaliação: `python3 -m unittest discover -s apexaudio/desktop_host/tests` de `/dev-server`, `/tmp` e `apexaudio/desktop_host` (21/21 OK em cada); `zipfile` sobre `gradle-wrapper.jar` (íntegro); `rg 'contains\("incompleto"\)|forward_ok|capture\._run =' apexaudio/` → vazio; `git status --short` → limpo.
