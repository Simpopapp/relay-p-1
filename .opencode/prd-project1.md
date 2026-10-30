# PRD: Real-Time Bidirectional USB/LAN Audio Bridge (ApexAudio)

**Documento:** Especificação Técnica de Produto (PRD) para Implementação Autônoma via Agente de I.A.  
**Versão:** 1.0.0-PROD  
**Alvo de Execução:** Cursor / Claude 3.5 Sonnet / Devin / Aider  
**Ambiente:** Windows 10/11 (Host) ⟷ Android 10+ (Client)  

---

## 1. Visão Geral e Arquitetura de Alto Nível

O **ApexAudio** é um sistema de transporte de áudio bidirecional de baixa latência em tempo real. O sistema estabelece dois fluxos síncronos simultâneos sobre sockets TCP (com suporte a encapsulamento ADB Tunnel ou LAN direta):

1. **Downlink (PC ➔ Celular):** Captura o fluxo de saída padrão do Windows via WASAPI Loopback, empacota os frames PCM e transmite para reprodução em baixa latência no fone conectado ao Android.
2. **Uplink (Celular ➔ PC):** Captura a voz do microfone físico do Android via subsistema de áudio de baixa latência, empacota os frames PCM, envia ao PC e os injeta em um driver virtual (VB-Audio Virtual Cable) para consumo por Discord, jogos ou ferramentas de comunicação.

```
       ┌────────────────────────────────────────────────────────┐
       │                   WINDOWS HOST (PC)                    │
       │                                                        │
       │  ┌──────────────────────┐    ┌──────────────────────┐  │
       │  │   WASAPI Loopback    │    │  VB-Audio Cable In   │  │
       │  │ (Default Render Dev) │    │  (Virtual Mic Sink)  │  │
       │  └──────────┬───────────┘    └──────────▲───────────┘  │
       │             │ PCM                       │ PCM          │
       │             ▼ Chunks                    │ Chunks       │
       │  ┌──────────────────────┐    ┌──────────┴───────────┐  │
       │  │ Downlink Streamer TX │    │  Uplink Receiver RX  │  │
       │  │    (Port 59900)      │    │    (Port 59901)      │  │
       │  └──────────┬───────────┘    └──────────▲───────────┘  │
       └─────────────┼───────────────────────────┼──────────────┘
                     │                           │
           TCP Stream (Port 59900)     TCP Stream (Port 59901)
     [ ADB Port Forward: 127.0.0.1  OU  Direct LAN Socket: IP:Port ]
                     │                           │
       ┌─────────────▼───────────────────────────┴──────────────┐
       │                 ANDROID CLIENT (PHONE)                 │
       │                                                        │
       │  ┌──────────────────────┐    ┌──────────────────────┐  │
       │  │ Downlink Receiver RX │    │  Uplink Streamer TX  │  │
       │  │    (Port 59900)      │    │    (Port 59901)      │  │
       │  └──────────┬───────────┘    └──────────▲───────────┘  │
       │             │ PCM                       │ PCM          │
       │             ▼ Packets                   │ Packets      │
       │  ┌──────────────────────┐    ┌──────────┴───────────┐  │
       │  │  AudioTrack Engine   │    │  AudioRecord Engine  │  │
       │  │ (FAST_TRACK / Music) │    │(VOICE_COMMUNICATION) │  │
       │  └──────────┬───────────┘    └──────────▲───────────┘  │
       │             │                           │              │
       │             ▼                           │              │
       │       [ Fone Físico ]             [ Microfone ]        │
       └────────────────────────────────────────────────────────┘
```

---

## 2. Especificação do Protocolo de Rede (Apex Binary Protocol - ABP)

Para garantir que a I.A. não utilize abordagens ingênuas que sofram de fragmentação de stream TCP, todo o transporte deve seguir uma estrutura de framing binário determinística.

### 2.1. Estrutura do Pacote de Dados (ABP Frame)
Cada frame transmitido em ambas as direções consiste em um cabeçalho fixo de **16 bytes** seguido pelo payload PCM bruto.

| Campo | Offset (Bytes) | Tamanho | Tipo | Descrição |
| :--- | :--- | :--- | :--- | :--- |
| `MAGIC_BYTE` | 0 | 2 Bytes | `uint16_t` | Identificador de protocolo constante: `0xAA55` |
| `PACKET_TYPE`| 2 | 1 Byte | `uint8_t` | `0x01`: Áudio PCM, `0x02`: Ping, `0x03`: Pong, `0x04`: Config Handshake |
| `CHANNEL_ID` | 3 | 1 Byte | `uint8_t` | `0x00`: Downlink (Stereo), `0x01`: Uplink (Mono) |
| `SEQUENCE_NUM`| 4 | 4 Bytes | `uint32_t` | Contador incremental para detecção de jitter/drops |
| `TIMESTAMP_US`| 8 | 4 Bytes | `uint32_t` | Timestamp local em microssegundos (medir latência round-trip) |
| `PAYLOAD_SIZE`| 12 | 4 Bytes | `uint32_t` | Tamanho exato em bytes do payload que sucede o cabeçalho |
| `PAYLOAD` | 16 | N Bytes | `uint8_t[]`| Dados brutos de áudio em PCM Linear |

### 2.2. Opcodes de Controle
* `0x01` (`AUDIO_DATA`): Contém o chunk de áudio PCM.
* `0x02` (`HEARTBEAT_PING`): Enviado a cada 1000ms se não houver tráfego ativo; payload = timestamp local.
* `0x03` (`HEARTBEAT_PONG`): Resposta imediata ao Ping para cálculo de latência de transporte.
* `0x04` (`CONFIG_SYNC`): Enviado durante o handshake contendo taxa de amostragem (`uint32`), canais (`uint8`) e tamanho de frame (`uint16`).

---

## 3. Especificação do Pipeline de Áudio

### 3.1. Parâmetros de Formatação

| Parâmetro | Fluxo Downlink (PC ➔ Fone) | Fluxo Uplink (Mic ➔ PC) |
| :--- | :--- | :--- |
| **Taxa de Amostragem** | 48.000 Hz | 48.000 Hz |
| **Formato de Amostra** | 16-bit Signed Integer (Little-Endian) | 16-bit Signed Integer (Little-Endian) |
| **Canais** | 2 Canais (Stereo Interleaved: L/R) | 1 Canal (Mono) |
| **Duração do Frame** | 10 ms (480 amostras/canal) | 10 ms (480 amostras/canal) |
| **Bytes por Frame** | 480 × 2 canais × 2 bytes = **1.920 Bytes** | 480 × 1 canal × 2 bytes = **960 Bytes** |
| **Taxa de Transferência**| 192.000 Bytes/s (~1,536 Mbps) | 96.000 Bytes/s (~0,768 Mbps) |

### 3.2. Estratégia de Buffering e Jitter
* **PC Capture Buffer:** Captura no modo WASAPI Loopback Shared com buffer de hardware alocado para 10ms.
* **Android Jitter Buffer (Ring Buffer Circular):**
  * Buffer circular thread-safe sem locks baseado em apontadores atômicos de leitura/escrita.
  * **Tamanho Máximo do Buffer:** 4 frames (40ms = 7.680 bytes).
  * **Threshold de Início (Watermark):** A reprodução inicia imediatamente após o preenchimento de 2 frames (20ms).
  * **Política de Overrun:** Se o buffer exceder 4 frames (drift de relógio), o frame mais antigo é descartado imediatamente para evitar acúmulo de atraso.
  * **Política de Underrun:** Se o buffer secar, injeta silêncio sintético (array de zeros) para evitar estouro de pilha no `AudioTrack`.

---

## 4. Módulo Host (Windows PC Server)

O subsistema do PC deve ser implementado preferencialmente em **Python 3.10+** (usando `pyaudiowpatch`, `sounddevice` e `asyncio` / `threading` de alto desempenho) ou **C# (.NET 8)** com `NAudio.Wasapi`. A especificação a seguir define a implementação em Python/C++ híbrido via bindings.

### 4.1. Camada de Captura (WASAPI Loopback)
* O módulo deve enumerar o dispositivo de saída ativo padrão via WASAPI.
* Se a taxa nativa do dispositivo for diferente de 48.000 Hz (ex: 44.100 Hz ou 96.000 Hz), o módulo deve executar reamostragem em tempo real utilizando algoritmo linear ou polinomial de alta velocidade (ex: `scipy.signal.resample_poly` ou `samplerate` nativo) antes do empacotamento.
* Deve capturar continuamente em uma thread dedicada de alta prioridade de tempo real (`win32process.REALTIME_PRIORITY_CLASS` ou thread com prioridade `THREAD_PRIORITY_TIME_CRITICAL`).

### 4.2. Camada de Injeção de Microfone (Virtual Cable Sink)
* O servidor deve escanear as saídas de áudio disponíveis e buscar por string matching: `CABLE Input` ou `VB-Audio Virtual Cable`.
* Se o driver não for detectado, o console do servidor deve alertar claramente a dependência ausente, mas manter a escuta ativa para conexão manual.
* Os dados recebidos da porta `59901` (Mono PCM) são abertos em um stream de saída exclusivo ou compartilhado para o dispositivo virtual, permitindo que o Discord/Windows o selecione como dispositivo de entrada padrão.

### 4.3. Gerenciamento de Túnel ADB Automático
O servidor deve conter um subprocesso que detecta o ambiente Android:
1. Executa `adb devices`.
2. Se detectar um dispositivo em estado `device`, executa automaticamente:
   ```bash
   adb forward tcp:59900 tcp:59900
   adb reverse tcp:59901 tcp:59901
   ```
3. Se o ADB não estiver acessível no PATH ou nenhum dispositivo estiver plugado via USB, o servidor recai automaticamente para escuta de sockets em `0.0.0.0:59900` e `0.0.0.0:59901`, exibindo o IP local do PC no console para conexão via Wi-Fi.

---

## 5. Módulo Cliente (Android Mobile App)

Construído nativamente em **Android SDK (Kotlin)** com alvo em **API 30+ (Android 11 a 14)**.

### 5.1. Engine de Reprodução (Downlink - AudioTrack)
* **Classe:** `android.media.AudioTrack`.
* **Configuração de Áudio:**
  ```kotlin
  AudioAttributes.Builder()
      .setUsage(AudioAttributes.USAGE_MEDIA)
      .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
      .setFlags(AudioAttributes.FLAG_LOW_LATENCY)
      .build()
  ```
* **Modo de Transferência:** `AudioTrack.MODE_STREAM`.
* **Desempenho:** Performance mode `AudioTrack.PERFORMANCE_MODE_LOW_LATENCY`.
* **Buffer:** O tamanho do buffer interno deve ser configurado como o dobro do `getMinBufferSize()` para habilitar o caminho *Fast Track* do mixer de áudio do Android (evita o mixer de software do sistema).

### 5.2. Engine de Captura (Uplink - AudioRecord)
* **Classe:** `android.media.AudioRecord`.
* **AudioSource:** `MediaRecorder.AudioSource.VOICE_COMMUNICATION` (ativa cancelamento de eco acústico por hardware - AEC, se disponível) com opção de fallback para `MediaRecorder.AudioSource.MIC` (áudio não processado).
* **Buffer de Leitura:** Lê blocos estritos de 960 bytes por iteração e despacha imediatamente para a fila do socket TCP.

### 5.3. Gerenciamento de Ciclo de Vida e Background Execution
* **Serviço de Primeiro Plano (Foreground Service):**
  * O app deve implementar um `ForegroundService` persistente (`AudioBridgeService`).
  * Tipos de Foreground Service declarados no `AndroidManifest.xml`:
    * `android:foregroundServiceType="microphone|mediaPlayback"`
  * Notificação contínua e silenciosa com prioridade mínima (`IMPORTANCE_LOW`) contendo apenas:
    * Título: "ApexAudio Bridge Ativo"
    * Texto: "Transmitindo áudio via USB/LAN | RTT: XX ms"
    * Ação rápida: Botão "Desconectar".
* **Locks de Sistema:**
  * Alocar `PowerManager.WakeLock` (`PARTIAL_WAKE_LOCK`) enquanto o stream estiver conectado para evitar que a CPU entre em modo deep sleep.
  * Alocar `WifiManager.WifiLock` (`WIFI_MODE_FULL_LOW_LATENCY`) se conectado via rede sem fio.

---

## 6. Diagrama de Estados e Máquina de Conexão

Ambas as pontas devem implementar uma máquina de estados finitos (FSM) rigorosa:

```
               ┌────────────────┐
               │  DISCONNECTED  │
               └───────┬────────┘
                       │ Event: User Clicks Connect / Auto-ADB
                       ▼
               ┌────────────────┐
        ┌─────►│   CONNECTING   ├─────┐
        │      └───────┬────────┘     │
        │              │ Success      │ Timeout / Socket Error
        │              ▼              │
        │      ┌────────────────┐     │
        │      │   HANDSHAKE    │     │
        │      └───────┬────────┘     │
        │              │ Ack Recv     │
        │              ▼              │
        │      ┌────────────────┐     │
        │      │   STREAMING    │     │
        │      └───┬────────▲───┘     │
        │          │        │         │
Connection Lost    │        │ Health  │
(Drop / Unplug)    ▼        │ OK      │
        │      ┌────────────────┐     │
        └──────┤  RECONNECTING  │◄────┘
               └────────────────┘
```

### Regras de Transição e Tolerância a Falhas
1. **Heartbeat Timeout:** Se nenhum pacote (áudio ou ping) for recebido no período de **3.000 ms**, o socket é considerado morto (`DEAD_SOCKET`).
2. **Auto-Reconnect Loop:** Ao detectar queda do socket, o cliente entra em `RECONNECTING`.
   * Tenta reconectar imediatamente na primeira tentativa.
   * Aplica backoff exponencial simples: 500ms, 1000ms, 2000ms até um teto de 5000ms.
   * Não fecha a interface nem emite avisos audíveis; reconecta silenciosamente.
3. **Flushing no Reconnect:** Ao reestabelecer conexão, todos os buffers de áudio locais (PC e Android) devem ser limpos com `flush()` para impedir que áudio antigo residual seja reproduzido após a reconexão.

---

## 7. Estrutura de Diretórios e Arquivos do Projeto

O agente de I.A. deve estruturar o repositório rigorosamente conforme o layout abaixo:

```text
apexaudio/
├── desktop_host/
│   ├── requirements.txt            # Dependências (pyaudiowpatch, sounddevice, numpy)
│   ├── config.py                   # Constantes de áudio, portas (59900/59901), buffer
│   ├── protocol.py                 # Serialização/Deserialização binária do protocolo ABP
│   ├── adb_manager.py              # Detecção automática do dispositivo e port forward
│   ├── audio_capture.py            # WASAPI Loopback capture engine
│   ├── audio_sink.py               # Injeção no VB-Audio Virtual Cable
│   ├── network_server.py           # Sockets TCP de baixa latência (Downlink/Uplink)
│   └── main.py                     # Entry point e orquestrador multi-thread
│
└── android_client/
    ├── app/
    │   ├── build.gradle.kts
    │   └── src/main/
    │       ├── AndroidManifest.xml # Permissões de Áudio, Rede, Foreground Service
    │       ├── java/com/apex/audio/
    │       │   ├── data/
    │       │   │   ├── Protocol.kt           # Parser binário ABP idêntico ao host
    │       │   │   └── CircularBuffer.kt     # Lock-free Ring Buffer implementation
    │       │   ├── engine/
    │       │   │   ├── AudioTrackPlayer.kt   # Engine de reprodução de baixa latência
    │       │   │   └── AudioRecordCapturer.kt# Engine de captura de microfone
    │       │   ├── service/
    │       │   │   └── AudioBridgeService.kt # Foreground service com WakeLock
    │       │   ├── network/
    │       │   │   └── SocketManager.kt      # Gerenciador TCP com reconexão automática
    │       │   └── ui/
    │       │       ├── MainActivity.kt       # Interface Jetpack Compose
    │       │       └── BridgeViewModel.kt    # Gerenciador de estado da UI
```

---

## 8. Especificação de Interface de Usuário (UI/UX)

A interface deve ser minimalista, monocromática (Dark Theme), focada puramente em telemetria técnica e controle operacional.

### 8.1. Interface Android (Jetpack Compose)
* **Painel de Conexão:**
  * Campo de texto com o Host: Padrão preenchido como `127.0.0.1` (para uso via cabo USB/ADB).
  * Checkbox/Toggle: "Modo USB (ADB)" vs "Modo LAN (Wi-Fi)".
  * Botão de Estado Único:
    * `CONECTAR` (Verde suave / Estado desconectado).
    * `DESCONECTAR` (Vermelho / Estado ativo).
* **Painel de Telemetria em Tempo Real:**
  * Indicador de Status: `ONLINE` / `CONNECTING` / `OFFLINE`.
  * RTT (Round Trip Time) medido via pacotes Ping/Pong em milissegundos (ex: `Latency: 4.2 ms`).
  * Taxa de amostragem ativa: `48,000 Hz | 16-bit PCM`.
  * Buffer Health: Barra linear indicando a ocupação do Ring Buffer (verde = saudável, amarelo = sob pressão, vermelho = drops).
* **Controles Rápidos:**
  * Slider de Ganho de Microfone: de 0.0x a 2.0x (multiplicador digital de PCM).
  * Toggle Switch: "Mudo (Microfone)".

### 8.2. Interface Windows (Console CLI Dashboard)
O `main.py` do Windows deve utilizar formatação ANSI limpa via terminal:
```text
============================================================
 [ApexAudio Host Server v1.0.0] - STATUS: RUNNING
============================================================
 [ADB Engine]    : Device detected (SM-G991B) -> Ports 59900/59901 Routed.
 [Capture]       : WASAPI Loopback Active (Speakers - Realtek Audio) [48kHz Stereo]
 [Mic Sink]      : Virtual Cable Found (CABLE Input - VB-Audio Cable)
 [Downlink TX]   : 192.0 KB/s | Pkts: 14202 | Drops: 0
 [Uplink RX]     : 96.0 KB/s  | Pkts: 14200 | Latency: 3.8ms
============================================================
 [Ctrl+C] Encerrar o servidor
```

---

## 9. Roteiro Passo a Passo de Implementação para o Agente de I.A.

Ao iniciar a codificação, o agente deve executar o desenvolvimento nas 5 fases estritas abaixo:

### Fase 1: Protocolo Comum e Estruturas de Dados
* Implementar `protocol.py` e `Protocol.kt`.
* Criar funções unitárias de teste que validem que um byte array gerado pelo Python é lido identicamente pelo Kotlin, garantindo o correto alinhamento Little-Endian dos inteiros de 16 e 32 bits.

### Fase 2: Host Windows (Captura e Envio)
* Criar o script de captura WASAPI Loopback em `audio_capture.py` garantindo extração estrita de chunks de 1.920 bytes.
* Implementar o servidor de socket em `network_server.py` escutando na porta `59900`.
* Testar a geração contínua do stream sem estouro de memória ou bloqueio de thread.

### Fase 3: Cliente Android (Recepção e Reprodução)
* Implementar `AudioTrackPlayer.kt` com Ring Buffer thread-safe.
* Estabelecer o socket TCP conectando a `127.0.0.1:59900`.
* Conectar fones de ouvido no celular, rodar o script no PC, tocar um vídeo no YouTube do computador e verificar reprodução límpida, sem estalos e sem atraso perceptível.

### Fase 4: Microfone Reverso (Android ➔ PC)
* Implementar `AudioRecordCapturer.kt` no Android coletando mono a 48kHz em blocos de 960 bytes.
* Criar o receptor em `audio_sink.py` no PC que escuta na porta `59901` e escreve as amostras diretamente no dispositivo `CABLE Input`.
* Testar gravação no Gravador de Som do Windows ou teste de microfone do Discord.

### Fase 5: ADB Automation e Resiliência
* Integrar `adb_manager.py` para rodar os comandos de port-forwarding no startup.
* Implementar reconexão automática resiliente com flushing de buffer em ambas as pontas.
* Finalizar a UI do Jetpack Compose com os seletores de mute e indicadores de latência.

---

## 10. Registro de decisões do builder (remix N=1)

**D1 — Topologia ADB:** o celular é o cliente TCP das DUAS portas (59900 e 59901), então o
túnel usa `adb reverse tcp:59900 tcp:59900` e `adb reverse tcp:59901 tcp:59901` — e não
`adb forward` para 59900 como indicado em §4.3 (forward só serviria conexões iniciadas
pelo PC). Ajustado em `desktop_host/adb_manager.py`; o fluxo do PRD §6 permanece válido.
Origem: observação técnica do subagente s1-android-client, validada pelo builder.

**D2 — Geração de flush no jitter buffer (Fase 6):** `CircularBuffer` ganhou
`flushGeneration` (contador atômico incrementado em `flush()`), porque
`usedFrames == 0` não distingue underrun de flush. O `AudioTrackPlayer` re-exige o
watermark somente quando a geração muda (reconnect); underrun comum nunca rearma.
Origem: avaliação do monitor (stage-05-eval.md) + subagente s3; decisão do builder.

**D3 — Cadência de heartbeat independente do tráfego (Fase 6):** o downlink envia PING
quando `HEARTBEAT_INTERVAL_MS` se passou desde o ÚLTIMO PING (não desde o último
envio de áudio), com `_ping_pending[seq]` registrado antes do `sendall`; o PONG
preenche `rtt_ms`. Motivo: a implementação anterior era código morto (0 PINGs,
`rtt_ms: None` — provado por sonda). Gate versionado em
`desktop_host/tests/test_network_server.py` (14/14 unittest).

**D4 — Permissões em runtime (Fase 6):** `MainActivity` pede `RECORD_AUDIO` (+
`POST_NOTIFICATIONS` em SDK 33+) uma vez por entrada na tela, via
`rememberLauncherForActivityResult`; `BridgeUiState.permissionsGranted` bloqueia o
CONECTAR (botão desabilitado + aviso) até a concessão. Negação não crasha nem
re-dispara o launcher automaticamente (reavaliação só em callback/onResume).
**Revisão (2ª avaliação do monitor):** o gate do CONECTAR considera SOMENTE
`RECORD_AUDIO` — negar notificações não pode travar o app (o FGS funciona sem
elas); `POST_NOTIFICATIONS` segue sendo pedido, mas é facultativo.

**D5 — Reconexão e foreground (Fase 6):** o `BridgeViewModel` nunca anula a referência
do binder na desconexão do usuário (o reconectar reusa e chama `connect()`;
`connectJob` garante idempotência); `AudioBridgeService.onStartCommand` promove
`startForeground` em todo comando sem `ACTION_DISCONNECT` (defesa
targetSdk 34 contra `ForegroundServiceDidNotStartInTimeException`).

**D6 — Delegação em enxame (rodada 2):** os subagentes (`s2-host-gates`,
`s3-android-lifecycle`) executam com os 3 pilares centrais + 3 próprios
(`.opencode/work/sub/`), mas não têm permissão de escrita no projeto nesta sandbox:
entregam proposta validada em cópia/patch e o builder aplica e reproduz os gates antes
de marcar `[x]` no roadmap central.

**D7 — Pacing e dead-socket no host (Fase 7):** o downlink envia um frame por tick
monotônico de 10ms (`config.FRAME_MS`); atraso pequeno recupera um frame por tick,
atraso grande (> ~3 ticks) ressincroniza em vez de rajadar. Dead-socket nas duas
portas: sem pacote do cliente por `config.DEAD_SOCKET_TIMEOUT_MS` encerra a sessão;
o host envia PING no uplink quando ocioso (PRD §2.2) e o cliente responde PONG.
Motivo: sonda provou 73k frames em ~4s com fonte rápida (satura o túnel USB) e o
PRD §6 exige tolerância a queda nas duas pontas. Origem: dívida P2
(stage-05-eval rec. 8 / stage-06-eval rec. 8).

**D8 — Erro tipado de framing no Android (Fase 7; rev. stage-07-eval P3):**
`Protocol.IncompleteFrame` (subclasse de `ProtocolError`, que passa a `open`)
sinaliza buffer incompleto; `SocketManager.tryDecode` decide por tipo
(`IncompleteFrame` → aguarda mais bytes; `ProtocolError` genérico → ressincroniza),
sem `contains("incompleto")`. **Revisão:** `size < 0` é CORRUPÇÃO de stream, não
incompletude — lança `ProtocolError` comum (o host Python lê size como uint32 e
trata bytes altíssimos como erro; paridade de semântica). Motivo: acoplamento a
texto de exceção quebra a ressincronização com qualquer reescrita de mensagem.

**D9 — Gradle wrapper fixado (Fase 7):** o client ganha wrapper versionado
(`gradlew`, `gradlew.bat`, `gradle/wrapper/*`) fixado no Gradle mínimo compatível
com o AGP do projeto (8.5.2 → Gradle 8.7); a prova de compilação segue externa
(sem toolchain na sandbox).

**D10 — Suíte do host independente de cwd/porta (Fase 7):** `tests/__init__.py`
insere a raiz do repositório no `sys.path` e cada teste aloca portas dinâmicas
sobrescrevendo `config.PORT_*` em `setUp` (restauradas no cleanup). Motivo: o gate
só passava de `/dev-server` e em portas fixas (stage-06-eval, atenção 3–4).

**D11 — Entrega de pilares por caminho (Fase 7):** no harness desta sandbox, os
subagentes `spawn_agent` são read-only e recebem planejamento/roadmap centrais
íntegros no system prompt; o PRD central (longo) é lido do disco como PASSO ZERO
obrigatório e os pilares do recorte vão íntegros no prompt. Entregas em
`/tmp/remix/s{K}` (arquivos completos, validados em cópia em `/tmp/work-s{K}`) e o
builder aplica e reproduz os gates no projeto. Onda 3: s4-host-realtime,
s5-capture-hygiene, s6-android-contracts — Fase 7 fechada com 21/21 gates verdes.
