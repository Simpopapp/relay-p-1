# PRD — s2-webclient (página do celular, N=2)

## Decisões técnicas já tomadas (siga sem reabrir)
- D2-2/D2-5: página estática servida em `http://localhost:59900` pelo host; JS puro
  **sem build step** (nada de bundler/TS). ES Modules nativos (`type="module"`).
- Áudio: Web Audio + AudioWorklet (RF7/RF8). Downlink estéreo 48kHz s16, 1920B/frame
  (10ms); uplink mono 48kHz s16, 960B/frame (10ms). Buffer adaptativo 2–4 frames.
- WS binário: cada mensagem = 1 frame ABP completo (header 16B LE + payload).
- Contrato canônico: `apexaudio/docs/protocol.md` — leia antes de codar.
- PWA instalável (RF10): manifest + service worker; Wake Lock quando disponível.

## Contrato ABP em JS (`abp.js`) — obrigatório
- ESM; exporte: `MAGIC=0xAA55`, `PACKET_AUDIO=0x01`, `PACKET_PING=0x02`,
  `PACKET_PONG=0x03`, `PACKET_CONFIG_SYNC=0x04`, `CHANNEL_DOWNLINK=0x00`,
  `CHANNEL_UPLINK=0x01`, `HEADER_SIZE=16`, `FRAME_BYTES_DOWNLINK=1920`,
  `FRAME_BYTES_UPLINK=960`, e funções:
  - `encode(packetType, channelId, seq, payload(Uint8Array), tsUs?) -> Uint8Array`
    (header `<HBBIII`: magic u16, type u8, channel u8, seq u32, ts u32, size u32 —
    little-endian em TODO campo; ts default `performance.now()*1000` truncado u32).
  - `decode(buf) -> {packetType, channelId, seq, tsUs, payload} | null` (null se
    incompleto; **throw** em magic inválido).
  - `feedStream(buf) -> {frames: [...], rest: Uint8Array}` (defesa contra fragmentação).
  - `makeConfigSync(sampleRate, channels, frameBytes, seq) -> Uint8Array`
    (payload `<IBH`: u32 rate, u8 channels, u16 frameBytes = 7 bytes).
  - `parseConfigSync(frame) -> {sampleRate, channels, frameBytes}`.
- Uso de DataView/`Uint32` SEM sinal em todos os campos (>>> 0).

## Vetores de paridade (byte-exatos — os testes devem asserir exatamente)
- PING   seq=1 ts=1000: `55 aa 02 00 01 00 00 00 e8 03 00 00 00 00 00 00`
- PONG   seq=1 ts=1000: `55 aa 03 00 01 00 00 00 e8 03 00 00 00 00 00 00`
- CONFIG_SYNC sample=48000 ch=2 fb=1920 seq=7 ts=1000:
  `55 aa 04 00 07 00 00 00 e8 03 00 00 07 00 00 00 80 bb 00 00 02 80 07`
- ÁUDIO downlink seq=42 ts=0, payload 1920 bytes: header
  `55 aa 01 00 2a 00 00 00 00 00 00 00 80 07 00 00` + 1920 bytes.
- ÁUDIO uplink seq=1 ts=0, payload 960 zero bytes: header
  `55 aa 01 01 01 00 00 00 00 00 00 00 c0 03 00 00` + 960 bytes.
- `feedStream` com 2 frames concatenados decodifica os 2 e o resto volta vazio;
  com frame truncado devolve `rest` = bytes recebidos e nenhum frame;
  magic inválido → throw.
- Testes em `apexaudio/web_client/tests/abp.test.mjs`, roda com `node --test`
  (sem dependências). Asserções: byte-a-byte contra os vetores acima + ida-e-volta
  encode→decode + rejeição de magic/truncado.

## Modo demonstração (contrato com o site — obrigatório)
- `index.html?demo=1`: `app.js` não abre WS; `demo-source.js` gera áudio estéreo
  simulado (tom senoidal leve ~440Hz com leve vibrato, frames de 1920B) injetado
  no mesmo caminho do player, e o RTT mostra valor simulado (~12ms) com leve variação.
- UI mostra badge "Demonstração" e o botão vira "Iniciar demo / Parar".
- Sem microfone no modo demo (não pede permissão); slider de ganho e mute visíveis
  e funcionais sobre o sinal simulado (aplicam no caminho de áudio).

## UI da página (RF6/RF9)
- Botão único Conectar (verde)/Desconectar (vermelho), exige gesto do usuário.
- Status: OFFLINE / CONECTANDO / ONLINE; RTT (via PING/PONG, a cada 1000ms);
- Saúde do buffer (verde/amarelo/vermelho por nível do ring 2–4 frames);
  slider de ganho 0.0–2.0; botão mute; info `48,000 Hz | 16-bit PCM`.
- Reconexão automática com backoff 500/1000/2000→5000ms (flush no reconnect).
- Visual próprio, coeso com a marca ApexAudio (escuro, acento âmbar), viewport
  mobile; página funciona também em desktop para o /demo do site.

## Estrutura de entrega (obrigatório)
- Escreva tudo em `/tmp/remix/s2-webclient/apexaudio/web_client/` espelhando o
  projeto + `RELATORIO.md` na raiz do pacote. Arquivos mínimos:
  `index.html`, `app.js`, `abp.js`, `player-worklet.js`, `capturer-worklet.js`,
  `demo-source.js`, `style.css`, `manifest.webmanifest`, `sw.js`, `tests/abp.test.mjs`.
- Worklets: cada um num arquivo próprio carregado via `audioWorklet.addModule`;
  player consome frames via ring buffer em mensagem, capturer emite s16 mono 960B.
- s16: conversão float→int16 no capturer (clamp ±32767) e int16→float no player.

## Gates (números reais, sem eles não marque [x])
- `node --test apexaudio/web_client/tests/abp.test.mjs` — todos verdes (conte N).
- Página abre sem erros de console quando servida como arquivo estático simples
  (se tiver como servir, prove com Playwright; senão declare e entregue o método).
- /demo: o gate final roda no preview integrado — responsabilidade do agente
  principal; sua parte é o `?demo=1` completo e funcional.

## Proibições
- Não toque em `apexaudio/desktop_host/`, `apexaudio/android_client/`, `src/`,
  nem nos pilares centrais ou de outros subagentes.
- Sem dependências npm; sem CDN; sem build step; sem variáveis de ambiente.

## Registro de decisões (preencha, numerado)
- (vazio — registre aqui decisões de implementação)
