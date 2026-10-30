# PRD — ApexAudio 2 (project2): uso prático sem etapas de desenvolvimento

## 1. Objetivo
Entregar o mesmo túnel de áudio bidirecional PC⇄celular via USB do project1, eliminando
toda etapa de build/instalação técnica do lado do usuário. Critério-mestre: **um usuário
leigo chega ao primeiro áudio em < 5 minutos, sem instalar SDK, IDE, Python ou compilar.**

## 2. Escopo
- IN: host Windows em executável único; cliente do celular como página web (PWA) servida
  pelo próprio host; site público (este app TanStack) com download, demo e ajuda; build
  automático do exe por CI (GitHub Actions).
- OUT: app Android nativo, Play Store, iOS, contas/login, backend em nuvem, multi-dispositivo.

## 3. Arquitetura
```text
[Windows]                                         [Android / Chrome]
ApexAudio.exe                                      http://localhost:59900
 ├─ WASAPI loopback ─┐                             ├─ página PWA (HTML/JS estático)
 ├─ VB-Cable sink ◄──┤  WebSocket /ws (binário)    ├─ AudioWorklet player (downlink)
 ├─ HTTP+WS :59900 ──┴──── adb reverse tcp:59900 ──┤─ getUserMedia + Worklet (uplink)
 └─ adb embutido (auto)                            └─ UI: Conectar, RTT, ganho, mute
```
- Porta única 59900 (HTTP + WebSocket). Substitui o par 59900/59901 do project1 (D2-1).
- Reaproveita do project1: `protocol.py` (framing ABP dentro de mensagens WS binárias),
  `audio_capture.py`, `audio_sink.py`, `adb_manager.py`, pacing 10ms, testes.
- Descartado do project1: `apexaudio/android_client/` inteiro (fica arquivado, não mantido).

## 4. Requisitos funcionais
- RF1 Host: duplo clique abre console/bandeja com status (celular detectado, túnel, áudio).
- RF2 Host: localiza adb (PATH → pasta local → download automático do platform-tools oficial).
- RF3 Host: `adb reverse tcp:59900 tcp:59900` automático e re-aplicado ao re-plugar.
- RF4 Host: tenta abrir a página no celular: `adb shell am start -a android.intent.action.VIEW -d http://localhost:59900`.
- RF5 Host: se VB-Cable ausente, oferece instalar (download oficial + instalador, com aviso);
  sem VB-Cable o downlink continua funcionando.
- RF6 Página: botão único Conectar/Desconectar; exige gesto do usuário (política de autoplay).
- RF7 Página: downlink 48kHz estéreo s16 em frames de 10ms → AudioWorklet com buffer 20–40ms.
- RF8 Página: uplink microfone (echoCancellation/noiseSuppression configuráveis) → s16 mono
  48kHz, 960B/frame, ganho 0–2x e mute.
- RF9 Página: RTT via PING/PONG, saúde do buffer, reconexão automática com backoff.
- RF10 Página: PWA instalável (manifest + service worker), Wake Lock de tela quando disponível.
- RF11 Site público: home (4 passos + download), /demo (UI do celular em modo simulado),
  /ajuda (depuração USB, troubleshooting, escolha de microfone no Discord).

## 5. Requisitos não funcionais
- Latência ponta-a-ponta alvo ≤ 60ms (aceitável ≤ 80ms em navegador).
- Zero dependências instaladas pelo usuário além do exe (e opcionalmente VB-Cable).
- Exe gerado por CI a cada tag; publicado em GitHub Releases; o site linka a última release.
- Página do celular: arquivos estáticos sem build (JS puro), embutidos no exe.

## 6. Protocolo
- WS binário; cada mensagem = 1 frame ABP do project1 (header 16B LE + payload). Handshake
  CONFIG_SYNC enviado pelo host logo após o upgrade. Heartbeat 1000ms; 3000ms sem tráfego = morto.
- Contrato canônico continua em `apexaudio/docs/protocol.md`, com seção nova "Transporte WS".

## 7. Riscos e mitigação
- Autoplay/suspensão de áudio em segundo plano no Chrome → Wake Lock + aviso "mantenha a tela
  ligada"; aceito como limitação.
- Latência do AudioWorklet varia por aparelho → buffer adaptativo 2–4 frames.
- Antivírus marcando exe PyInstaller → assinar não está no escopo; documentar na ajuda.
- Depuração USB é um passo inevitável sem app nativo → guia ilustrado na /ajuda.

## 8. Critérios de aceite
- CA1 Testes Python do host (protocolo + WS + pacing) verdes de qualquer cwd.
- CA2 Teste de integração: cliente WS de teste recebe CONFIG_SYNC, frames 1936B a ~100/s, envia
  uplink 976B entregue ao sink.
- CA3 Página do celular abre via host e conecta em modo real; /demo funciona no preview.
- CA4 Workflow de CI gera `ApexAudio.exe` (artefato verificado no run).
- CA5 Preview do site mostra home, demo e ajuda sem erros de console.

## 9. Decisões
- D2-1 Porta única HTTP+WS (59900): um só `adb reverse`, menos pontos de falha.
- D2-2 Cliente = página web em localhost (contexto seguro ⇒ microfone liberado sem HTTPS).
- D2-3 Exe via PyInstaller em GitHub Actions (Windows runner): o usuário nunca compila.
- D2-4 Servidor HTTP/WS com `aiohttp` (ou `websockets` + http embutido) — escolher o de menor
  tamanho no exe, mantendo threads de áudio fora do event loop.
- D2-5 O site TanStack é vitrine/demo/ajuda; não transporta áudio.
- D2-6 Modo LAN fora do escopo inicial (exigiria HTTPS para o microfone).
