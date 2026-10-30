# Roadmap — s4-host-realtime

## Fase A — Diagnóstico e cópia de validação
- [ ] Ler `network_server.py`, `tests/test_network_server.py`, `docs/protocol.md` (trechos de transporte/heartbeat).
- [ ] Copiar o projeto para `/tmp/work-s4/` e reproduzir o gate atual (14/14) na cópia.
- Gates: saída real da suíte na cópia registrada.

## Fase B — Pacing do downlink
- [ ] Pacer monotônico de 10ms com política de recuperação/ressincronização (PRD do recorte §1).
- [ ] Primeiro frame pós-handshake sem espera de tick.
- Gates: `test_pacing_dry_source_is_throttled` verde na cópia (~100 frames/s, sem par < 5ms).

## Fase C — Dead-socket nas duas portas
- [ ] Downlink: sessão encerra sem tráfego recebido por 3000ms.
- [ ] Uplink: sessão encerra sem tráfego recebido por 3000ms + PING do host quando ocioso.
- [ ] `docs/protocol.md` atualizado se o contrato mudar (registre).
- Gates: `test_dead_socket_downlink_closes_session` e `test_dead_socket_uplink_closes_session` verdes na cópia.

## Fase D — Suíte independente de cwd/porta
- [ ] `tests/__init__.py` com raiz no `sys.path`.
- [ ] Portas dinâmicas em `setUp` com restauração no cleanup.
- Gates: suíte completa verde da raiz da cópia E de outro diretório (evidência dos dois comandos).

## Fase E — Entrega
- [ ] Arquivos finais completos em `/tmp/remix/s4/` + relatório no formato do system prompt.
- Gates: todos os gates acima verdes na cópia; relatório com números reais.
