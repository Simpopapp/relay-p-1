# Avaliação — Stage 06 (Fase 6: correções pós-avaliação, remix N=1)

**Data:** 2026-10-29 (rev. 3 — fecho da etapa após rodada 2.2)
**Veredito:** concluída
**Confiança da avaliação:** alta — host Python reexecutado por mim (suíte); Kotlin verificado por leitura do código real + dois espelhos executáveis independentes da lógica de `CircularBuffer`.

## Reavaliação final (rodada 2.2) — etapa fechada

As duas asserções do `CircularBufferTest.kt` foram corrigidas e conferem com a implementação:

- **overrun**: `assertEquals(4, buffer.usedFrames)` (6 writes, capacidade 4 → `writeIdx 6 − readIdx 2`), `drops == 2` e "primeiro vivo == frame 2" mantidos — `CircularBufferTest.kt:63-68`.
- **underrun**: `assertFalse(buffer.isWatermarkReached)` após drenar e escrever 1 frame, com comentário remetendo a política do player ao `AudioTrackPlayer` e a intenção anti-rearme expressa por `flushGeneration == 0` — `CircularBufferTest.kt:40-45`.

Provas que executei nesta revisão:

1. Leitura do teste final: as 5 funções conferem com a semântica de `CircularBuffer.kt` (capacidade 4, watermark 2, overrun descarta o mais antigo, flush avança geração e zera `usedFrames`), sem asserção órfã e com imports consistentes.
2. Espelho do builder (`/tmp/cb_mirror.py`): é um espelho real — reproduz `write`/`read`/`flush` com a checagem de tamanho de frame, não um carimbo — e passa **5/5**.
3. Espelho independente meu, escrito contra as asserções atuais (`/tmp/monitor/cb_mirror2.py`): **15 PASS, 0 FAIL**.
4. Suíte Python reexecutada: **14/14 OK em 5,016 s** (sem regressão pelas edições).
5. Registro conferido: `stage-06-status.md:29` documenta a correção como item 6 e o roadmap central reflete o gate provado por espelho (`.opencode/roadmap-proj1.md:48`).

Isto fecha os três conjuntos de apontamentos: os 5 da rodada 2.0, o defeito de `POST_NOTIFICATIONS` e as 2 asserções da rodada 2.1. Não resta nenhum item que eu consiga verificar como quebrado neste ambiente.

**Limites explícitos do veredito** (não são pendências do builder, são do ambiente): (a) nenhuma linha de Kotlin foi compilada — `CircularBufferTest` e as cinco mudanças Android só serão realmente executadas no primeiro `testDebugUnitTest` de fora da sandbox; (b) o teste end-to-end PC + celular + VB-Cable é externo por definição; (c) a dívida P2 (pacing do host, dead-socket, `IncompleteFrame` tipado, monkey-patch de prioridade) continua aberta e declarada, sem bloquear a Fase 6.

**Ajuste cosmético sugerido (não bloqueia):** `stage-06-status.md:21` ainda descreve o overrun como "6 writes → 2 usados, 2 drops" — foi exatamente essa ambiguidade que produziu a asserção errada. Trocar por "4 frames vivos, 2 descartados" evita a reincidência.

**Estado do ajuste cosmético (conferido):** a frase corrigida foi inserida em `stage-06-status.md:15` ("overrun com 6 writes/capacidade 4 → 4 frames vivos, 2 descartados"), mas o texto ambíguo original **permanece** em `stage-06-status.md:21` ("6 writes → 2 usados, 2 drops"), na seção que descreve o gate Kotlin — justamente onde alguém iria ler antes de mexer no teste. Não altera o veredito (documentação, não código), mas as duas frases convivem e a errada é a mais próxima do código.

---

## Reavaliação — correção dos 5 apontamentos (rodada 2.1)

Os 5 itens pedidos foram todos endereçados no código, e 4 estão limpos:

| # | Apontamento anterior | Estado | Evidência minha |
|---|---|---|---|
| 1 | `POST_NOTIFICATIONS` bloqueava o CONECTAR | **fechado** | `BridgeViewModel.kt:98-108` — `refreshPermissions` lê **só** `RECORD_AUDIO`, com comentário citando D4; D4 revisada no PRD §10 |
| 2 | `ADB_PORTS_*` sobreviviam em `config.py` | **fechado** | `rg "ADB_PORTS"` em `apexaudio/desktop_host/` → vazio (só menções textuais a "ADB Engine"/docstrings) |
| 3 | Sem teste JVM do jitter buffer | **fechado no arquivo, quebrado na prática** | `CircularBufferTest.kt` existe (5 testes), mas **2 falham** — ver abaixo |
| 4 | Gate dependente de `cwd` | **fechado como documentação** | `stage-06-status.md:18` fixa `/dev-server` como cwd e classifica o `ModuleNotFoundError` como não-regressão |
| 5 | `protocol.md` regra 2 atrás da D3 | **fechado** | Regra 2 reescrita: cadência desde o ÚLTIMO PING, independente de tráfego, com registro do instante de envio para o RTT |

Suíte Python reexecutada por mim agora: **14/14 OK em 5,016 s**. D4 revisada registra explicitamente que negar notificações não pode travar o app. Nada do que eu havia marcado como parcial voltou atrás.

**Bloqueio remanescente (novo, introduzido no item 3).** `app/src/test/java/com/apex/audio/CircularBufferTest.kt` não pode ter passado por `testDebugUnitTest` — duas asserções contradizem a implementação real de `CircularBuffer.kt`:

1. `overrun descarta o mais antigo e conta drop` espera `usedFrames == 2` após 6 writes. Com `CAPACITY_FRAMES = 4`, `usedFrames` é `writeIdx - readIdx` = `6 - 2` = **4** (só 2 foram descartados, 4 continuam vivos). `drops == 2` e "primeiro vivo == frame 2" estão corretos.
2. `underrun comum NAO rearma o watermark` termina com `assertTrue(buffer.isWatermarkReached)` após drenar e escrever 1 frame. `isWatermarkReached` é `usedFrames >= 2`; com 1 frame vale **`false`**. O teste confunde a política do *player* (que mantém o watermark liberado até um flush) com o estado de *enchimento* do buffer — que é justamente por isso que D2 introduziu `flushGeneration`. A asserção anterior (`flushGeneration == 0`) é a que captura a intenção e está certa.

Confirmei com um espelho executável da classe (mesma semântica de `write`/`read`/`flush`/overrun, em `/tmp/monitor/cb_mirror.py`): **8 asserções PASS, 2 FAIL**, exatamente as duas acima. Não há Gradle/Kotlin na sandbox, então a falha só apareceria na primeira execução do build externo — como gate vermelho, atrapalhando o teste de hardware.

**Correção mínima (3 linhas):** em (1), `assertEquals(4, buffer.usedFrames)` — ou melhor, `assertEquals(2, buffer.drops)` + `assertEquals(4, buffer.usedFrames)` com comentário do porquê; em (2), trocar o `assertTrue` final por `assertFalse` e dizer que o "não rearme" é responsabilidade do `AudioTrackPlayer` (que compara gerações), sugerindo um teste de player com sink fake se quiser cobrir a outra metade.

**Veredito desta revisão:** **parcial**, confiança alta — todos os 5 apontamentos anteriores seguem fechados, mas o artefato criado para fechar o item 3 é vermelho e irá falhar no primeiro `testDebugUnitTest`. Depois do ajuste das duas asserções, a Fase 6 fecha sem ressalvas de código (permanecem as pendências externas já declaradas: compilação Android e teste de hardware).

---

<sub>Avaliação inicial da rodada 2.0, mantida para rastreabilidade.</sub>

## Resumo executivo

Os cinco bloqueios da `stage-05-eval.md` foram atacados de frente e quatro estão de fato resolvidos: o heartbeat do host funciona (medido, não relatado), o gate da Fase 2 agora é um teste versionado e reproduzível (14/14 verde na minha execução), `adb_manager.py` migrou para `reverse` nas duas portas lendo as portas de `config`, e a reconexão/foreground foi corrigida nos dois arquivos certos. O quinto — permissões em runtime — está implementado, mas com um defeito de produto: o CONECTAR só habilita com `POST_NOTIFICATIONS` concedida, então negar notificações (comum no Android 13+) deixa o app permanentemente inutilizável com a mensagem errada. Além disso, uma das afirmações do status ("constantes `ADB_PORTS_*` removidas") não corresponde ao código, e as mudanças Android seguem sem compilação e sem nenhum teste — inclusive a lógica nova mais delicada (`flushGeneration`).

## Cobertura de requisitos

- **Atendido — heartbeat do host (bloqueio 1).** `network_server.py` agora separa `last_traffic` de `last_ping_sent`, registra `_ping_pending[seq]` **antes** do `sendall` e desfaz o registro se o envio falhar; PONG preenche `rtt_ms`. Sonda read-only reexecutada por mim (fonte seca, cliente sem responder pong): **3 PINGs em ~4 s**, antes 0. `test_dry_source_heartbeat_populates_rtt` responde pong e exige `rtt_ms` float ≥ 0 — passa.
- **Atendido — gate da Fase 2 versionado (bloqueio 2).** `apexaudio/desktop_host/tests/test_network_server.py` cobre handshake CONFIG_SYNC (48000, 2, 1920), downlink 1920B com leitura em blocos de 257 bytes (força remontagem TCP de verdade), pong casado, pong desconhecido ignorado sem alterar RTT, uplink 960B entregue ao sink, 3 payloads inválidos (0/959/961) descartados, heartbeat/RTT e desconexão no meio do downlink com nova sessão aceita. Executei `python3 -m unittest discover -s apexaudio/desktop_host/tests` a partir de `/dev-server`: **14/14 OK em 5,016 s** — número do status confere.
- **Atendido — `adb_manager.py` (bloqueio 3, parcialmente).** Docstring corrigida para `reverse` nas duas portas com a Decisão D1 citada; portas vêm de `config.PORT_DOWNLINK/PORT_UPLINK`. Ressalva: as constantes `ADB_PORTS_FORWARD`/`ADB_PORTS_REVERSE` **continuam** em `config.py:49-50` (ver Discrepâncias).
- **Parcial — permissões em runtime (bloqueio 4).** O fluxo existe e é correto na arquitetura: `PermissionsGate` com `rememberLauncherForActivityResult`, pedido em `LaunchedEffect`, reavaliação em callback e em `onResume`, `permissionsGranted` no UI state e `toggleConnect` com saída antecipada — o crash por `SecurityException` está de fato impedido. O defeito está na condição: `permissionsGranted` exige `RECORD_AUDIO` **e** `POST_NOTIFICATIONS` (`BridgeViewModel.kt:100-106`). Negar notificações — comportamento comum e legítimo, já que o FGS funciona sem elas — desabilita o CONECTAR para sempre, com o aviso "Permissão de microfone necessária" (`MainActivity.kt:192-194`), que aponta para a permissão errada e não oferece caminho para as configurações.
- **Atendido — reconexão e foreground (bloqueio 5).** `BridgeViewModel` não anula mais o binder na desconexão do usuário (`onServiceDisconnected` ainda solta a referência, o que é correto); `connectJob` dá idempotência e cancela no disconnect; `onStartCommand` promove `startForegroundWithNotification(currentState)` em todo comando sem `ACTION_DISCONNECT`. O caminho conectar → desconectar → conectar deixa de ser no-op e o risco de `ForegroundServiceDidNotStartInTimeException` no segundo start está coberto.
- **Atendido com lacuna de teste — watermark (item extra).** `CircularBuffer.flushGeneration` incrementa em `flush()`; `AudioTrackPlayer` rearma o watermark só quando a geração muda. A decisão D2 está bem justificada (underrun não pode virar rearme) e o encadeamento real fecha: player inicia → `SocketManager.connect()` dispara `onState(CONNECTING)` → `flush()` → geração muda → watermark reexigido. **Não há teste** para `flushGeneration`, embora `CircularBuffer` seja Kotlin puro e rode em JVM sem SDK.
- **Atendido — higiene.** Ponteiros `docs/planning/PRD.md`/`ROADMAP.md` presentes e apontando para os arquivos certos; trio `s1-android-client` marcado OBSOLETO no topo com instrução explícita de não executar; `__pycache__`/`*.py[cod]` no `.gitignore` e **0 `.pyc` versionados** (`git ls-files`); nota D1 em `project1.md`; D2–D6 no PRD §10 com origem e motivação.

## Qualidade do código

**Pontos fortes:** as decisões ficaram registradas onde pertencem (D2/D3 explicam *por que* a implementação anterior era morta, não só o que mudou); o teste de rede testa comportamento e não implementação (blocos de 257 bytes, seq desconhecido, desconexão no meio); tratamento de erro no envio do PING remove o `_ping_pending` órfão, evitando RTT fantasma; o `else` do `onStartCommand` é a defesa certa para targetSdk 34, no lugar certo.

**Pontos de atenção:**
1. `BridgeViewModel.kt:100-106` — `POST_NOTIFICATIONS` tratada como bloqueante (acima). É a única regressão funcional introduzida nesta fase.
2. Gate não é independente do diretório: rodando `cd apexaudio/desktop_host && python3 -m unittest discover -s tests` o import falha (`ModuleNotFoundError: No module named 'apexaudio'`) porque `test_network_server.py` importa `apexaudio.desktop_host`. O status registra o comando sem `cwd`; quem repetir de outro diretório vê vermelho e conclui que o gate quebrou.
3. Suíte usa portas fixas 59900/59901 e a mesma instância de `AudioServer` por teste: funciona em série, mas colide com o host rodando na máquina ou com execução paralela.
4. `test_client_ping_gets_matching_pong` afirma `rtt_ms is None` enquanto corre contra um servidor que agora pinga a cada 1 s — se a leitura demorar ~1 s, o heartbeat pode preencher o RTT e o teste falha. Janela estreita, mas é flakiness estrutural.
5. `main.py` continua usando `AdbStatus.forward_ok` para a primeira porta de `reverse` — nome herdado que agora mente sobre o que representa.
6. Dívida P2 intacta e confirmada por mim: sem *pacing* no host (sonda gerou **73.297 frames de áudio em ~4 s**), sem dead-socket no host, `SocketManager.tryDecode` ainda decide por `message.contains("incompleto")`, monkey-patch de `_run` em `audio_capture.py`, sem gradle wrapper.

## Discrepâncias

1. **Status: "constantes `ADB_PORTS_*` obsoletas removidas"** — falso no código atual: `config.py:49-50` ainda as define, e com comentários que descrevem o desenho antigo (`forward` para 59900). O `rg` citado no status foi escopado a `adb_manager.py`, não ao projeto. Continuam sem uso, então é dívida cosmética — mas a afirmação não se sustenta.
2. **`docs/planning/ROADMAP.md` (ponteiro): "Fase 6 … em execução"** — contradiz `stage-06-status.md` ("concluída") e o roadmap central, que já tem a Fase 6 inteira `[x]`. É o arquivo que o monitor lê primeiro; hoje ele informa o estado errado.
3. **`docs/protocol.md` §Regras de transporte 2** ainda diz "ping a cada 1000ms **sem tráfego**", enquanto D3 e o código pingam a cada 1 s independentemente do tráfego. O contrato canônico ficou atrás da decisão — e é o documento que o cliente Android segue.
4. **Evidência de heartbeat**: o status cita "2 PINGs em 2,5s" (sonda do builder); a minha sonda deu 3 PINGs em ~4 s. Compatível, não contraditório — registro para deixar claro que a cadência é ~1/s e não um número fixo.
5. **Android "verificado estaticamente (5 arquivos, cenários a–e)"**: os cenários foram conferidos por leitura, mas nenhum teste automatizado cobre as mudanças — `ProtocolTest.kt` não menciona `flushGeneration`, `permissionsGranted` nem `POST_NOTIFICATIONS` (`rg` vazio em `app/src/test/`). "Verificado" aqui significa "lido", e o status diz isso, mas convém não deixar a palavra ambígua na próxima rodada.

## Riscos para as próximas etapas

1. **O teste de hardware pode morrer na porta de entrada**: negar notificações bloqueia o CONECTAR com mensagem enganosa. É a primeira coisa que qualquer pessoa faz ao instalar no Android 13+.
2. **Nenhuma linha de Kotlin foi compilada**: as cinco mudanças Android (permissões, `connectJob`, `onStartCommand`, `flushGeneration`, watermark) entram no teste de hardware sem prova de compilação. Um erro de compilação só aparece na máquina de teste, junto com a falta de wrapper.
3. **A lógica mais sutil da fase não tem teste**: rearme do watermark por geração é exatamente o tipo de código que passa na leitura e falha em campo (áudio mudo após reconnect, ou rajadas de latência). É testável em JVM hoje, sem SDK.
4. **Pacing do host**: 73 mil frames em 4 s com fonte seca mostra que o ritmo continua 100% dependente de `chunk_source()` bloquear. No cabo USB, isso vira saturação e atraso acumulado — o oposto do objetivo de 20–40 ms.
5. **Gate frágil a `cwd` e a portas fixas** reduz a chance de a próxima rodada reproduzir o 14/14 e aumenta a chance de "regressão fantasma".

## Recomendações

> Nota da revisão 2.1: os itens 1, 2, 5 e 6 desta lista foram executados; o item 4 foi resolvido como documentação (cwd obrigatório), não como independência. Restam 3, 7 e 8, mais o acerto das duas asserções do `CircularBufferTest.kt` descrito na Reavaliação.

Prioridade 1 — antes do teste de hardware:
1. `BridgeViewModel.refreshPermissions`: gatear o CONECTAR **apenas** em `RECORD_AUDIO`; tratar `POST_NOTIFICATIONS` como aviso não bloqueante. Corrigir o texto ("Permissão de microfone necessária" só quando o mic faltar) e oferecer "Abrir configurações" quando a permissão estiver negada permanentemente.
2. Adicionar teste JVM para `CircularBuffer.flushGeneration` (rearme após flush, **não** rearme após underrun comum) — roda sem SDK e cobre a Decisão D2.
3. Adicionar `gradle wrapper` (ou fixar por escrito Gradle 8.5.2 + JDK 17 + SDK 34 no `README`) para que o build externo não seja uma segunda incógnita.
4. Tornar a suíte independente de `cwd` (inserir a raiz no `sys.path` no `tests/__init__.py`) e permitir portas por variável de ambiente.

Prioridade 2 — dívida que já custou uma rodada:
5. Remover `ADB_PORTS_FORWARD`/`ADB_PORTS_REVERSE` de `config.py` e renomear `AdbStatus.forward_ok` → `downlink_reverse_ok` (ou equivalente) para o dashboard não mentir.
6. Atualizar `docs/protocol.md` (regra 2) para refletir D3 — o contrato tem de acompanhar a decisão.
7. Corrigir o texto do ponteiro `docs/planning/ROADMAP.md` (Fase 6 concluída) e evitar estado volátil dentro de um arquivo que deveria ser só redirecionamento.
8. Fechar a P2 remanescente: pacing explícito no downlink, dead-socket no host, `IncompleteFrame` tipado, remover o monkey-patch de prioridade em `audio_capture.py`.

## Evidências consultadas

- `/dev-server/docs/planning/stages/stage-06-status.md`, `/dev-server/docs/planning/PRD.md`, `/dev-server/docs/planning/ROADMAP.md`
- `/dev-server/.opencode/roadmap-proj1.md` (§Fase 6, gates), `/dev-server/.opencode/prd-project1.md` §10 (D1–D6), `/dev-server/.opencode/project1.md`
- `/dev-server/.opencode/work/sub/s1-android-client/roadmap-proj1-s1-android-client.md` (marcação de obsolescência)
- `/dev-server/apexaudio/desktop_host/network_server.py` (`_serve_downlink`, `_handle_control`), `adb_manager.py`, `config.py`
- `/dev-server/apexaudio/desktop_host/tests/test_network_server.py`, `tests/test_protocol.py`
- `/dev-server/apexaudio/android_client/app/src/main/java/com/apex/audio/{ui/MainActivity.kt,ui/BridgeViewModel.kt,service/AudioBridgeService.kt,engine/AudioTrackPlayer.kt,data/CircularBuffer.kt}`, `app/src/test/java/com/apex/audio/ProtocolTest.kt`
- Execuções nesta avaliação: `python3 -m unittest discover -s apexaudio/desktop_host/tests` → **14/14 OK em 5,016 s** (de `/dev-server`); mesmo comando de `apexaudio/desktop_host` → `ModuleNotFoundError` (gate dependente de `cwd`); sonda `/tmp/monitor/probe_host.py` → 3 PINGs, `rtt_ms: None` sem pong do cliente, **73.297** frames de áudio em ~4 s; `git ls-files | grep pycache` → 0; `rg "ADB_PORTS|adb forward" apexaudio/` → 2 ocorrências remanescentes em `config.py`.
