# Status — Stage 07 (Fase 7: fecho da dívida P2 e higiene de gates)

**Data:** 2026-10-30 · **Rodada:** remix N=1, rodada 3 · **Builder:** agente principal + enxame (s4/s5/s6)

## Escopo executado
Fecho integral da dívida Prioridade 2 declarada em `stage-05-eval.md` e
`stage-06-eval.md`, executado em onda paralela com 3 subagentes
(`.opencode/work/sub/s{4,5,6}-*/`, entregas em `/tmp/remix/s{4,5,6}`, aplicação e
verificação pelo builder — Decisões D6/D11 do PRD §10).

## Entregas

1. **Pacing do downlink (D7)** — `network_server.py`: primeiro frame pós-handshake
   imediato; seguintes em ticks monotônicos de 10ms (`config.FRAME_MS`), intervalo
   mínimo entre envios; atraso ≤ 3 ticks consome os slots vencidos (sem rajada),
   atraso maior ressincroniza a base. Fonte seca envia silêncio na mesma cadência.
2. **Dead-socket nas duas portas (D7)** — sessão encerra após
   `config.DEAD_SOCKET_TIMEOUT_MS` (3s) sem pacote completo RECEBIDO do cliente
   (PONG conta; áudio enviado pelo host e fragmentos não). Uplink ocioso: host
   envia PING no canal do uplink, reutilizando `_ping_pending`/RTT; PING/PONG
   responde no canal da conexão.
3. **Suíte reprodutível (D10)** — `tests/__init__.py` insere a raiz no `sys.path`;
   shims de bootstrap nos módulos de teste (discovery com `-s` absoluto não roda
   `__init__` de pacote); portas dinâmicas por teste (bind 0, restauradas no
   cleanup); `test_capture.py` novo (3 testes).
4. **Captura sem monkey-patch** — `LoopbackCapture(thread_initializer=…)` executado
   dentro da thread (best-effort, exceções engolidas); `open_loopback_capture`
   injeta a prioridade win32 sem `capture._run = …`. Ausência de `pyaudiowpatch`
   agora cai no modo silencioso (ImportError ≈ CaptureUnavailable).
5. **ADB honesto** — `AdbStatus.forward_ok` → `downlink_reverse_ok` (resultado do
   `adb reverse` do downlink, D1); `main.py` ajustado.
6. **Erro tipado no Android (D8)** — `Protocol.IncompleteFrame : ProtocolError`
   (`ProtocolError` agora `open`); `decode` lança `IncompleteFrame` nos dois casos
   de incompletude (header e payload, incluindo `size < 0`); `SocketManager.tryDecode`
   decide por tipo; `ProtocolTest.kt` +3 testes (13 no total).
7. **Gradle wrapper (D9)** — `gradlew`/`gradlew.bat`/`gradle/wrapper/*` versionados,
   Gradle **8.7** (mínimo oficial do AGP 8.5.2, matriz citada no README);
   scripts canônicos da tag `v8.7.0`; `README.md` de build no client.
8. **Docs** — `docs/protocol.md` regras 2 e 5 (heartbeat bidirecional + pacing);
   ponteiro `docs/planning/ROADMAP.md` agora sem estado volátil.

## Gates (números reais)
- Suíte unittest: **21/21 OK em ~15,1s** de TRÊS cwds (`/dev-server`, `/tmp`,
  `apexaudio/desktop_host`) — 8 protocolo + 10 rede + 3 captura.
- Pacing (gate no teste): **102 frames / 1,0572s = 96,5 frames/s**, menor
  intervalo entre frames **8,05ms** (antes: 73.297 frames em ~4s sem pacing).
- Dead-socket: sessão encerra em **3,044s (downlink)** e **3,039s (uplink)**;
  PING/PONG do uplink ocioso preenche `rtt_ms` (teste novo).
- `rg 'contains("incompleto")|forward_ok|capture\._run =' apexaudio/` → vazio.
- Wrapper: `gradle-wrapper.jar` (43.453B, zip íntegro), `distributionUrl`
  `gradle-8.7-bin.zip`, `gradlew` executável, scripts idênticos à tag `v8.7.0`.

## Limitações declaradas (ambiente)
- Sem toolchain Kotlin/Gradle na sandbox: mudanças Android verificadas
  estaticamente (rg + leitura); prova de execução no primeiro build externo.
- Teste end-to-end de hardware (PC + celular + VB-Cable) permanece externo.

## Adendo pós-avaliação do monitor (stage-07-eval.md)
- **P3 (1) aplicado:** `Protocol.kt` — `size < 0` agora lança `ProtocolError`
  comum (corrupção → ressincroniza) em vez de `IncompleteFrame`; teste novo
  `decode_negative_size_is_not_incomplete` em `ProtocolTest.kt` (14 testes).
  D8 revisada no PRD central §10.
- **P3 (2) dispensado com justificativa:** no host Python o size é `uint32`
  (`struct.Struct("<HBBIII")`) — um tamanho negativo é impossível no fio, e
  bytes altíssimos já produzem `ProtocolError` ("payload incompleto") em
  `decode` e em `feed_stream`. Paridade já garantida pela estrutura.
- Atenção 2 (`_put` privado no teste) e atenção 3 (folga do min_gap) aceitas
  como registradas — nenhuma ação.
