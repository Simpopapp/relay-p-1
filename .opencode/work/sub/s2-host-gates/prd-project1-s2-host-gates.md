# PRD — subagente s2-host-gates (N=1)

O COMO do pacote de rede do host. Precedência: `project1-s2-host-gates.md` (o quê);
dúvida não coberta aqui → decida e registre na seção "Registro de decisões".

## Decisões técnicas já tomadas (siga sem reabrir)
- **D1 (central):** o celular é o cliente TCP das DUAS portas → `adb reverse tcp:59900 tcp:59900` e `adb reverse tcp:59901 tcp:59901`. Nunca reintroduzir `adb forward` para 59900.
- **Contratos fixos:** `apexaudio/desktop_host/config.py` e `protocol.py` não mudam. Constantes: `HEARTBEAT_INTERVAL_MS=1000`, `PORT_DOWNLINK=59900`, `PORT_UPLINK=59901`, `DOWNLINK_FRAME_BYTES=1920`, `UPLINK_FRAME_BYTES=960`, opcodes 0x01–0x04, header ABP de 16B little-endian (`struct("<HBBIII")` — note: timestamp é uint32 no host).
- **Estilo do projeto:** Python 3.10+, type hints, docstrings em PT-BR referenciando seções do PRD, testes unittest (padrão de `tests/test_protocol.py`), imports relativos `from . import config, protocol` (o pacote é `apexaudio.desktop_host`).

## Tarefa 1 — Heartbeat do downlink (`network_server.py`, `_serve_downlink`)
Estado atual com defeito (linhas ~129–161): `last_sent = time.monotonic()` é
re-atribuído a cada iteração imediatamente antes de `if time.monotonic() - last_sent > HEARTBEAT_INTERVAL_MS/1000`, então o ramo nunca dispara, `_ping_pending` fica vazio e `rtt_ms` permanece `None`.

Correção exigida:
- Separar `last_traffic` (áudio OU qualquer frame recebido) de `last_ping_sent`.
- Enviar PING (opcode 0x02, via `protocol.make_ping`) quando `time.monotonic() - last_ping_sent >= HEARTBEAT_INTERVAL_MS/1000.0`; registrar `self._ping_pending[seq] = time.monotonic()` ANTES de `sendall`; atualizar `last_ping_sent` no envio.
- Pong recebido (`_handle_control`, `PACKET_PONG`): calcular RTT contra o ts de envio e escrever `stats.rtt_ms` (round 1 casa). Já existe; verificar que funciona com o novo registro.
- Preservar: envio de áudio a cada iteração (fonte seca → silêncio 1920B), leitura não-bloqueante via `select` timeout 0, contagem de stats, desconexão silenciosa do cliente.
- Não introduzir `time.sleep` extra no caminho do áudio além do já existente no ramo de ping (0.01s ok lá).
- Detecção de dead-socket no host NÃO é exigida nesta fase (fica para depois); não invente.

## Tarefa 2 — Gate versionado: `tests/test_network_server.py` (NOVO)
Teste de integração unittest que sobe um `AudioServer` real em portas livres e
executa contra clientes socket reais. Requisitos:

1. **Handshake:** cliente conecta na porta downlink → primeiro frame recebido é CONFIG_SYNC (0x04) com payload decodificável: sample_rate=48000 (uint32 LE), channels=2 (uint8), frame_bytes=1920 (uint16 LE). Use `protocol.make_config_sync`/decode do próprio módulo como referência de formato.
2. **Downlink 1920B:** a seguir chegam frames AUDIO_DATA (0x01, canal 0x00) com payload de exatamente 1920 bytes; `feed_stream` deve defragmentar o stream TCP.
3. **Pong:** host recebe PING do cliente (0x02) → responde PONG (0x03) com mesmo sequence_num (via `_handle_control`).
4. **Uplink 960B:** cliente conecta na porta uplink, envia frame AUDIO_DATA canal 0x01 com payload de 960B → o sink (use um objeto fake com `write_frame` gravando chamadas) recebe o payload; `up_packets` sobe.
5. **Drop de frame inválido:** uplink com payload ≠ 960B → `stats.drops` incrementa, nada chega ao sink.
6. **Heartbeat/RTT:** com `chunk_source` retornando None (fonte seca) e cliente lendo por ≥ ~2,2s, o host envia ao menos 1 PING; o cliente responde PONG com o mesmo sequence_num e o timestamp original → `stats.snapshot()["rtt_ms"]` passa a ser um float ≥ 0 (não None).

Diretrizes de implementação:
- Bindar em portas efêmeras: como `AudioServer.start()` usa `config.PORT_*`, prefira testar contra as portas reais 59900/59901 (livres na sandbox) OU refactor mínimo aceito: permitir injetar portas — se refactorar, mantenha a assinatura existente compatível e registre a decisão. NÃO alterar `config.py`.
- `chunk_source` fake: callable que retorna None (fonte seca) ou um b"\0"*1920 fixo — não use áudio real.
- Threads daemon + `server.stop()` no tearDown/finally; timeouts duros nos sockets de teste (ex.: 5s) para não pendurar a suíte.
- Padrão de asserts: use `protocol.decode`/`feed_stream` para validar frames, e `HostStats.snapshot()` para telemetria.
- Nome de testes descritivo; sem dependências novas (só stdlib).

## Tarefa 3 — Higiene do `adb_manager.py`
- Docstring: descrever `adb reverse` nas DUAS portas (Decisão D1); remover menção a `adb forward` para 59900.
- Importar portas de `config` (`from . import config`) e usar `config.PORT_DOWNLINK`/`config.PORT_UPLINK` nas chamadas de reverse.
- Remover as constantes obsoletas do `config.py`? **Não** — `config.py` está fora do escopo; apenas pare de referenciar `ADB_PORTS_*` (ninguém usa). Se a remoção for necessária, registre no relatório para o agente principal decidir.
- `AdbStatus` e comportamento de fallback LAN permanecem.

## Casos de borda e testes esperados
- Cliente desconecta no meio do downlink → thread encerra limpa (sem exceção no log de teste).
- Pong de seq desconhecido → ignorado, sem crash.
- Teste inteiro < ~10s.

## Tools e skills recomendadas
- Bash para rodar `python3 -m unittest discover -s apexaudio/desktop_host/tests -v` a partir da raiz `/dev-server` (o pacote exige import como `apexaudio.desktop_host.*`).
- Ler `tests/test_protocol.py` antes de escrever o teste novo (estilo e helpers).
- `rg` para confirmar que ninguém mais usa `ADB_PORTS_*`.

## Registro de decisões do subagente
(vazio — preencha numerado: D-s2-1, D-s2-2, …)

## Proibições
- Não editar `config.py`, `protocol.py`, `audio_capture.py`, `audio_sink.py`, `main.py`, `docs/**`, nada em `apexaudio/android_client/**`, pilares centrais, roadmap central.
- Não instalar dependências novas; não usar ferramentas de IA; não spawnar outros agentes.
- Não perguntar ao usuário; não usar oc/monitor; não finalizar o remix.
