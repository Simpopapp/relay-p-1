# Planejamento — subagente s2-host-gates (N=1)

## Missão
Reparar e blindar a camada de rede do host Python do ApexAudio: fazer o heartbeat do
downlink funcionar de verdade (PING em ociosidade + RTT preenchido), versionar o gate
"vivo" da Fase 2 como teste automatizado e limpar o `adb_manager.py` para refletir a
Decisão D1. Isso devolve ao host a telemetria de latência exigida pelo PRD §8.2 e dá
rede de segurança permanente à Fase 2.

## Escopo (exclusivo)
- `apexaudio/desktop_host/network_server.py` — correção do heartbeat/RTT.
- `apexaudio/desktop_host/tests/test_network_server.py` — NOVO teste de integração.
- `apexaudio/desktop_host/adb_manager.py` — docstring, portas via `config`, remoção de constantes obsoletas.

## Fora do escopo
- Qualquer arquivo do cliente Android (pacote s3-android-lifecycle).
- `config.py`, `protocol.py`, `audio_capture.py`, `audio_sink.py`, `main.py`, `docs/protocol.md` (comportamento já correto; mudar contrato exige relatório).
- Pilares centrais em `.opencode/` e arquivos de outros subagentes.

## Por quê
O monitor provou (sonda: 0 PINGs em 4s, `rtt_ms: None`) que o ramo do heartbeat é
inalcançável — `last_sent` é atualizado antes da comparação. O gate da Fase 2 vivia em
`/tmp` e se perdeu; sem teste versionado, regressões passam desapercebidas. O docstring
do `adb_manager` ainda descreve `adb forward` para 59900, contrariando a Decisão D1.

## Fronteiras
- Recebe: `config.py` e `protocol.py` estáveis (contratos), PRD §2/§4/§6, avaliação do monitor em `docs/planning/reports/stage-05-eval.md`.
- Entrega: código corrigido + teste de integração verde + relatório final para o agente principal.
- Não fala com o usuário, não usa `oc`, não marca o roadmap central.
