# Planejamento — s4-host-realtime (recorte do projeto N=1)

## Missão
Fechar a dívida de tempo-real do host Python: o downlink precisa de pacing
explícito (um frame de 10ms por tick, nunca rajada) e o host precisa detectar
socket morto nas DUAS portas (PRD §6 diz "ambas as pontas"). De bônus obrigatório,
o gate de rede passa a ser reprodutível em qualquer cwd e com portas dinâmicas.

## Por quê
- Sonda do monitor provou 73.297 frames em ~4s com fonte rápida: hoje o ritmo
  depende 100% de `chunk_source()` bloquear — em cabo USB isso satura o túnel e
  acumula atraso, o oposto dos 20–40ms do PRD.
- Sem dead-socket no host, um cliente que morre sem fechar o TCP ocupa a sessão
  para sempre (`downlink_clients`/`uplink_clients` nunca voltam a 0).
- O gate 14/14 só passa de `/dev-server` e em portas fixas: quem reproduzir de
  outro diretório vê vermelho fantasma (stage-06-eval, atenção 3–4).

## Escopo (arquivos SEUS, via proposta em /tmp)
- `apexaudio/desktop_host/network_server.py` — pacing + dead-socket.
- `apexaudio/desktop_host/tests/test_network_server.py` — portas dinâmicas + gates novos.
- `apexaudio/desktop_host/tests/__init__.py` — independência de cwd.
- `apexaudio/docs/protocol.md` — SOMENTE se o contrato de transporte precisar refletir dead-socket/pacing (registre a mudança).

## Fora do escopo (de outros pacotes — não toque)
- `audio_capture.py`, `adb_manager.py`, `main.py`, `tests/test_capture.py` → s5-capture-hygiene.
- `Protocol.kt`, `SocketManager.kt`, `ProtocolTest.kt`, wrapper Gradle → s6-android-contracts.
- Pilares centrais, `config.py` (as constantes que você precisa já existem: `FRAME_MS`, `DEAD_SOCKET_TIMEOUT_MS`, `HEARTBEAT_INTERVAL_MS`).

## Fronteiras
- Recebe: comportamento atual de `network_server.py` + os 6 testes de rede existentes (nenhum deles pode quebrar).
- Entrega: arquivos finais completos em `/tmp/remix/s4/` + relatório com evidência de suíte rodada em cópia.
