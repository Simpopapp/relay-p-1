# Registro de decisões de implementação
1. ESM nativo sem dependências; package.json apenas declara type=module para testes Node.
2. Endpoint WS relativo /ws, mesmo host/porta e wss sob HTTPS. Não há contrato de rota WS nos pilares fornecidos: hipótese explícita a confirmar pelo agente principal com s3; não altera framing ABP.
3. ONLINE após CONFIG_SYNC recebido e validado; cliente envia configuração canônica downlink conforme contrato, não inventa negociação de formatos.
4. Ganho/mute agem tanto na saída (incluindo demo) quanto na captura. Permissão de microfone negada preserva downlink.
5. Player inicia com 2 frames, sobe até 4 em underrun, reduz após aproximadamente 5 segundos estáveis. Overrun remove o mais antigo; áudio recebido antes de configuração é ignorado.
6. RTT modular u32 evita erro no wrap do timestamp. Reconexão por eventos e timers, sem polling de estado.
7. SW limitado aos assets conhecidos do próprio escopo, não captura /ws nem rotas do site. Ícones PNG 192/512 e SVG local; nenhuma CDN.
8. getUserMedia, AudioWorklet, PWA e Wake Lock requerem contexto seguro: localhost ou HTTPS. HTTP em IP LAN não equivale a localhost no telefone; TLS/túnel é responsabilidade de integração.
9. Pilares originais ficam intactos; registro PRD e execução do roadmap entregues como documentação dentro do recorte autorizado.
