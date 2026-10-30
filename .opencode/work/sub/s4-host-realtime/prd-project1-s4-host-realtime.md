# PRD — s4-host-realtime (o COMO do recorte)

Decisões centrais que você segue: D1 (reverse nas duas portas), D3 (cadência de
heartbeat desde o ÚLTIMO PING), D7 e D10 do PRD central (§10) — leia-as no pilar
central. Este arquivo detalha o recorte.

## 1. Pacing do downlink (D7)

- Tick monotônico: `time.monotonic()`; intervalo de tick = `config.FRAME_MS` (10ms).
- Loop atual de `_serve_downlink`: mantenha a estrutura (select 0.0 → recv →
  chunk_source → sendall → heartbeat), mas o envio de áudio passa a obedecer ao tick:
  - A cada iteração, calcule o próximo tick `deadline = base + n * FRAME_MS/1000`.
  - Se `now < deadline`, durma `deadline - now` (sleep fino; preferir
    `time.sleep()` com a sobra — não precisa de busy-wait).
  - Se o host atrasou ≤ ~30ms (3 ticks), NÃO pule frames: envie no momento em que
    acordar e avance o contador de ticks pelo número de ticks consumidos — isso
    recupera atraso a um frame por tick, sem rajada.
  - Se atrasou > ~30ms (fonte travou, GC), ressincronize: `base = now`, descarte os
    ticks perdidos (sem rajada) e siga do tick atual. Registre a política em comentário.
- O primeiro frame pós-handshake NÃO espera tick (latência de entrada mínima);
  o tick passa a valer do segundo frame em diante.
- Heartbeat (D3) permanece: cadência desde o último PING, `_ping_pending` populado
  antes do `sendall`. Com pacing, a iteração dura ~10ms e a condição
  `last_traffic - last_ping_sent >= 1s` continua correta — não reaproveite
  `last_traffic` para o PING (D3 usa o instante do último PING).
- `last_traffic` continua sendo atualizado por recv E por envio de áudio (é o que
  os testes atuais esperam), mas o dead-socket (item 2) usa um marcador próprio
  de tráfego RECEBIDO do cliente — separe as duas noções com clareza.

## 2. Dead-socket nas duas portas (D7)

- Downlink: se nenhum pacote RECEBIDO do cliente por `config.DEAD_SOCKET_TIMEOUT_MS`
  (3000ms) → encerre a sessão (`return`; o `finally` do chamador fecha o socket).
  PONG do cliente conta como tráfego recebido. Áudio enviado pelo host NÃO conta.
- Uplink: mesma regra — sem pacote do cliente por 3000ms → encerre a sessão.
- Uplink ocioso: o host envia PING quando ocioso > `HEARTBEAT_INTERVAL_MS`
  (PRD §2.2 — "a cada 1000ms se não houver tráfego ativo"), no canal
  `config.CHANNEL_UPLINK`, reutilizando a mecânica de `_ping_pending`/RTT do
  downlink (o PONG do uplink também pode preencher `rtt_ms` — mesmo canal de
  controle do cliente). O cliente Android já responde PING→PONG no leitor do
  uplink; nenhuma mudança no cliente é necessária.
- Estados: nenhuma mudança na FSM — o cliente é quem reconecta (PRD §6).

## 3. Suíte independente de cwd e de porta (D10)

- `tests/__init__.py` (novo): insere a raiz do repositório no `sys.path`
  (`Path(__file__).resolve().parents[3]` — confirme a profundidade) para que
  `python3 -m unittest discover -s apexaudio/desktop_host/tests` funcione de
  qualquer diretório. Documente no docstring.
- `test_network_server.py`: em `setUp`, aloque DUAS portas livres
  (`socket.bind(("127.0.0.1", 0))`), sobrescreva `config.PORT_DOWNLINK`/`PORT_UPLINK`
  e restaure os valores originais no cleanup. Os clientes conectam nas portas
  sobrescritas (os testes já leem `config.PORT_*` — só garantir que leiam DEPOIS
  do override).

## 4. Gates novos (aceite mensurável)

- `test_pacing_dry_source_is_throttled`: fonte seca (`lambda: None`), leia frames
  de áudio por ~1.05s de relógio → contagem entre 90 e 120 frames (~100/s), e
  NENHUM par de frames consecutivos com intervalo < 5ms (prova de não-rajada).
  PINGs contam para o relógio, não para a contagem de áudio.
- `test_dead_socket_downlink_closes_session`: cliente conecta, lê o handshake e
  NUNCA responde → `downlink_clients` volta a 0 em ≤ 4.5s (deadline do teste).
- `test_dead_socket_uplink_closes_session`: cliente conecta no uplink e envia
  nada → `uplink_clients` volta a 0 em ≤ 4.5s (o PING do host não salva a sessão
  porque o cliente não responde).
- Os 6 testes de rede existentes continuam verdes, SEM mudança de semântica
  (ajustes mecânicos de porta são permitidos; asserts não).

## 5. Método de trabalho (obrigatório)

1. Leia `network_server.py`, `tests/test_network_server.py`, `docs/protocol.md`.
2. Copie o projeto para `/tmp/work-s4/` e valide sua proposta LÁ: aplique as
   mudanças na cópia, rode
   `python3 -m unittest discover -s apexaudio/desktop_host/tests -v` da raiz da
   cópia E de outro diretório (prova de cwd), registre a saída real.
3. Escreva os arquivos finais completos em `/tmp/remix/s4/` (mesmos caminhos
   relativos ao projeto) — o agente principal aplica no projeto.
4. NÃO escreva em `/dev-server` — você não tem permissão de escrita no projeto.

## Proibições

- Não editar `config.py`, `audio_capture.py`, `adb_manager.py`, `main.py`,
  qualquer `.kt`, pilares centrais ou arquivos de outros subagentes.
- Sem dependências novas; só stdlib + numpy (já presentes).
- Contrato errado? Não improvise: relate no relatório final.
