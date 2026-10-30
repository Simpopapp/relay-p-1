# Avaliação — Stage 05 (etapa vigente; rodada N=1 ApexAudio, Fases 1–5)

**Data:** 2026-10-29
**Veredito:** parcial
**Confiança da avaliação:** alta para o host Python (testes e sonda executados nesta avaliação); média para o cliente Android (inspeção estática — sem toolchain Kotlin/Gradle na sandbox).

## Resumo executivo

As cinco fases têm artefatos reais no repositório e a Fase 1 está genuinamente verde (8/8 unittest reexecutados). O host Python importa limpo e o protocolo é coerente entre `protocol.py`, `docs/protocol.md` e `Protocol.kt`. Porém, a Fase 2 tem um defeito estrutural comprovado — o ramo de heartbeat do downlink é inalcançável, portanto o host nunca mede RTT (`rtt_ms` fica `None`) —, e as Fases 3–5, embora completas em arquivos, contêm dois defeitos que impedem uso real no celular: ausência total de pedido de permissão `RECORD_AUDIO` em runtime e uma segunda conexão que é um no-op silencioso (com risco de crash de foreground service). O roadmap não pode ser lido como "Fases 1–5 concluídas com gates"; é entrega de código completa com verificação de runtime pendente.

## Cobertura de requisitos

- **Atendido — Fase 1 (protocolo):** `protocol.py` com header `struct("<HBBIII")` de 16B, opcodes 0x01–0x04, canais 0x00/0x01, `feed_stream` contra fragmentação TCP; `config.py` centraliza 48 kHz/10 ms/1920B/960B; `docs/protocol.md` é contrato explicitamente subordinado ao Python. `tests/test_protocol.py` → **8/8 OK** reexecutado nesta avaliação. `ProtocolTest.kt` cobre 4 vetores byte-a-byte (`55 AA 02 00 …`, payload `80 BB 00 00 02 80 07`, 976/1936B, magic/truncado). Requisito do PRD §9-Fase 1 cumprido.
- **Atendido — Fase 2 (host), com uma lacuna:** os 7 módulos importam sem erro (reexecutado); captura com fallback silencioso explícito; sink com alerta de VB-Cable ausente; `network_server.py` faz CONFIG_SYNC, downlink TX, uplink RX com validação de 960B e contagem de drops; `adb_manager.py` usa `reverse` nas **duas** portas (Decisão D1), coerente com `AGENTS.md`.
- **Parcial — Fase 2 (heartbeat/RTT):** `docs/protocol.md` §2 e PRD §8.2 exigem ping a cada 1000 ms e latência no dashboard. `network_server.py:155-157` atualiza `last_sent` imediatamente antes de comparar `time.monotonic() - last_sent > 1.0`, logo o ramo é inalcançável; `_ping_pending` nunca é populado e `rtt_ms` permanece `None`. Sonda read-only executada nesta avaliação: 4 s de fonte seca → **0 PINGs enviados pelo host**, `rtt_ms: None`.
- **Parcial — Fase 3 (downlink Android):** todos os arquivos existem e seguem o PRD §5.1/§3.2 na forma, mas `CircularBuffer.isWatermarkReached` nunca é consultado por `AudioTrackPlayer` (o player escreve silêncio em vez de aguardar os 2 frames do watermark). Sem compilação verificável.
- **Parcial — Fase 4 (mic reverso):** ganho 0–2x com clamp e mute antes do TX estão corretos; fallback VOICE_COMMUNICATION→MIC está implementado. Mas não existe **nenhum** pedido de permissão em runtime (`rg requestPermissions|checkSelfPermission|ActivityResult` → zero ocorrências; só a declaração no manifest). Com `minSdk 30`, `AudioRecord.startRecording()` lança `SecurityException` e derruba o app no primeiro CONECTAR em aparelho real.
- **Parcial — Fase 5 (ADB/resiliência/UI):** `AudioBridgeService` tem foreground + WakeLock + WifiLock + notificação IMPORTANCE_LOW com RTT e ação Desconectar; a UI Compose cobre todos os itens do PRD §8.1 (host padrão `127.0.0.1`, toggle USB/LAN, botão único, status, RTT, taxa, buffer health, slider de ganho, mute). Contra: (a) `BridgeViewModel.kt:108` faz `service = null` ao desconectar e nunca volta a fazer bind, então o segundo CONECTAR não chama `connect()` — o botão fica morto; (b) `onStartCommand` (`AudioBridgeService.kt:182-187`) não chama `startForeground` quando o intent vem sem ação, e o segundo `startForegroundService` (ViewModel:93) tende a resultar em `ForegroundServiceDidNotStartInTimeException` em targetSdk 34.

## Qualidade do código

**Pontos fortes:** fronteira host/cliente bem desenhada e docstring ↔ código coerentes na maior parte; recusa explícita de degradar (fallback de captura, sink ausente, LAN mode) em vez de crashar; framing TCP com buffer deslizante nos dois lados; `config.py` como fonte única no host; decisão D1 documentada no PRD e no roadmap, não só no código.

**Pontos de atenção:**
1. `network_server.py:155-157` — heartbeat morto (acima). Também não há detecção de dead-socket no host, embora o PRD §6 diga "ambas as pontas".
2. `network_server.py` não tem *pacing* próprio: o ritmo depende inteiramente de `chunk_source()` bloquear. Sonda com fonte seca gerou **75.321 frames de áudio em ~4 s** (~2 Mbps fora de especificação). Em produção `read_chunk` bloqueia 0,1 s, mas qualquer fonte que retorne rápido satura o túnel USB.
3. `audio_capture.py:open_loopback_capture` faz *monkey-patch* de `capture._run` para injetar prioridade — funciona, mas é frágil e esconde a lógica de thread.
4. `adb_manager.py` ainda documenta `adb forward` para 59900 no docstring (linhas 4–5) enquanto o código usa `reverse` nas duas; e **hardcoda** 59900/59901 em vez de importar `config`, contrariando o próprio `config.py` ("nunca hardcode local"). Os constantes `ADB_PORTS_FORWARD`/`ADB_PORTS_REVERSE` ficaram obsoletos e errados — ninguém os usa.
5. `SocketManager.tryDecode` decide "buffer incompleto vs corrompido" por `message.contains("incompleto")` — acoplamento a texto de exceção; qualquer reescrita de mensagem quebra a ressincronização.
6. `AudioRecordCapturer` reutiliza um único `ByteArray` e o devolve ao chamador quando ganho = 1x; hoje é seguro (escrita síncrona no socket), mas vira bug no dia em que o frame for enfileirado.
7. `AudioTrackPlayer` tem `AudioManager.PROPERTY_OUTPUT_LATENCY` e `TAG` declarados e não usados (código morto).
8. Higiene de repositório: **9 arquivos `__pycache__/*.pyc` versionados** em `apexaudio/desktop_host/` e `tests/`; `.gitignore` não cobre Python.

## Discrepâncias

1. **Localização do planejamento:** `docs/planning/` contém apenas `stages/`. `PRD.md` e `ROADMAP.md` — as fontes canônicas do monitor (Skill 15 §15.3.2) — existem em `.opencode/prd-project1.md`, `.opencode/roadmap-proj1.md` e `.opencode/project1.md`. Não é "arquivo faltando" (o conteúdo existe e está coerente), mas o caminho canônico está vazio.
2. **Dois roadmaps contraditórios:** `.opencode/work/sub/s1-android-client/roadmap-proj1-s1-android-client.md` lista Fases A–D todas como `[ ]`, enquanto o roadmap central lista Fases 1–5 como `[x]`. Modelos de fase diferentes e estados opostos convivem no repositório.
3. **Evidência de gate não reprodutível:** o gate "vivo" da Fase 2 (`/tmp/test_fase2_server.py`) **não existe mais** em `/tmp` e não foi versionado. O que resta é o texto do status. Não há nenhum teste automatizado de `network_server.py` no repositório — só `test_protocol.py`.
4. **Status x código na Fase 2:** o status diz "pong round-trip" e o roadmap afirma RTT no dashboard. O round-trip medido no gate foi cliente→host (host responde pong); o **host** nunca inicia ping, então a telemetria de latência do host (PRD §8.2) nunca é preenchida. As duas afirmações não são falsas, mas juntas sugerem uma capacidade que o código não entrega.
5. **Status x código nas Fases 3–5:** os status já anotam "verificação estática", o que é honesto; mas o roadmap marca `[x]` com "Gates: OK (estático)" sem que exista compilação, e os dois defeitos bloqueantes da UI/serviço acima não aparecem em nenhum status.
6. **Roadmap em Unicode:** `project1.md` descreve `adb forward` como "pulo do gato"; a Decisão D1 muda a topologia para `reverse` nas duas portas. A decisão está documentada (bom), mas o documento de origem não foi anotado, então quem ler só `project1.md` implementa errado.

## Riscos para as próximas etapas

1. **O teste externo de hardware vai falhar no primeiro toque**, por falta de permissão `RECORD_AUDIO` — e vai mascarar todos os outros achados. Corrigir antes de mandar o app para o PC/celular.
2. **Segunda conexão quebrada** (`service = null`) + `START_STICKY` sem `startForeground` = crash provável do foreground service em Android 12+; é o caminho que qualquer teste manual percorre (conectar → desconectar → conectar).
3. **Sem gradle wrapper** (`gradlew`, `gradle/wrapper/` ausentes): o build externo depende de Gradle 8.5.2 + JDK 17 + SDK 34 instalados na máquina de teste; sem isso o passo "rodar assembleDebug" vira uma segunda incógnita.
4. **Latência do host sem telemetria** inviabiliza o critério de aceitação central do produto (20–40 ms) na dashboard — sem RTT no host, o teste end-to-end não tem como provar o número.
5. **Ausência de teste de integração do host** deixa heartbeat, dead-socket, drops e handshake sem rede de segurança; o gate que existia já se perdeu uma vez.
6. **Duplicidade de planejamento** (trios em `.opencode/` e em `.opencode/work/sub/`) garante que a próxima rodada leia o roadmap errado.

## Recomendações

Prioridade 1 — bloqueiam o teste end-to-end:
1. Pedir `RECORD_AUDIO` (e `POST_NOTIFICATIONS`) em runtime em `MainActivity` antes de conectar; bloquear o CONECTAR até a permissão estar concedida.
2. `BridgeViewModel`: não anular `service` em `disconnect()`; reutilizar o binder e chamar `service.connect(...)` no reconectar (ou desbind/rebind explícito). Em `onStartCommand`, chamar `startForeground` defensivamente quando não houver ação.
3. Corrigir o heartbeat do host: registrar o instante do **último envio antes** do envio (ou separar `last_audio_sent`/`last_traffic`), enviar PING quando ocioso e preencher `rtt_ms`; adicionar teste automatizado.
4. Comitar o gate da Fase 2 como teste em `apexaudio/desktop_host/tests/` (handshake + frame 1920B + pong + uplink 960B + drop de frame inválido + heartbeat) e adicionar `gradle wrapper` ao `android_client/`.

Prioridade 2 — dívida que já custa:
5. Mover `project1.md`, `prd-project1.md` e `roadmap-proj1.md` para `docs/planning/PRD.md` e `docs/planning/ROADMAP.md` (ou symlink/ponteiro), e remover ou marcar como obsoleto o trio de `work/sub/` para eliminar o roadmap contraditório.
6. `adb_manager.py`: corrigir o docstring (reverse nas duas portas), importar as portas de `config` e remover `ADB_PORTS_FORWARD`/`ADB_PORTS_REVERSE`.
7. `AudioTrackPlayer`: usar `isWatermarkReached` para iniciar a reprodução (PRD §3.2) e limitar a contagem de underruns a eventos por segundo, não por iteração.
8. `.gitignore` + remoção dos `__pycache__` versionados.
9. `SocketManager`: trocar o `contains("incompleto")` por um erro tipado (`IncompleteFrame`).

## Evidências consultadas

- `/dev-server/.opencode/project1.md`, `/dev-server/.opencode/prd-project1.md`, `/dev-server/.opencode/roadmap-proj1.md`
- `/dev-server/docs/planning/stages/stage-01-status.md` … `stage-05-status.md`
- `/dev-server/.opencode/work/sub/s1-android-client/{project1,prd-project1,roadmap-proj1}-s1-android-client.md`
- `/dev-server/apexaudio/docs/protocol.md`
- `/dev-server/apexaudio/desktop_host/{config,protocol,network_server,adb_manager,audio_capture,audio_sink,main}.py`, `tests/test_protocol.py`
- `/dev-server/apexaudio/android_client/app/src/main/**` (Protocol.kt, CircularBuffer.kt, AudioTrackPlayer.kt, AudioRecordCapturer.kt, SocketManager.kt, AudioBridgeService.kt, BridgeViewModel.kt, MainActivity.kt, AndroidManifest.xml, build.gradle.kts) e `app/src/test/.../ProtocolTest.kt`
- Execuções nesta avaliação: `python3 -m unittest discover` (8/8 OK); import dos 7 módulos do host (todos OK); sonda read-only `/tmp/monitor/probe_host.py` (0 PINGs em 4 s, `rtt_ms: None`, 75.321 frames de áudio)
- `"$__LOVABLE_REAL_GIT" ls-files apexaudio` (9 `.pyc` versionados); ausência de `gradlew`/`gradle/wrapper`; ausência de `/tmp/test_fase2_server.py`
