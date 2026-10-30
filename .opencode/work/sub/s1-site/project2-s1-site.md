# Planejamento — s1-site (site vitrine, N=2)

## Missão
Construir a vitrine pública do ApexAudio 2 (Fase 1 do roadmap central): a home que
explica o produto em 4 passos com botão de download, e a página /ajuda. Ela serve ao
objetivo central (PRD §1): um leigo entende o produto e chega ao primeiro áudio —
a vitrine é a porta de entrada e precisa convencer e orientar sem jargão.

## Escopo
- `src/routes/index.tsx` — home: proposta, 4 passos de uso, botão "Baixar para Windows",
  links para /demo e /ajuda.
- `src/routes/ajuda.tsx` — depuração USB passo a passo, microfone no Discord,
  problemas comuns, antivírus.
- `src/components/site/*` — identidade e blocos compartilhados das duas páginas
  (cabeçalho/navegação, rodapé, blocos de passo, etc.).
- Design próprio e coerente entre as duas rotas (Fase 1, gate de design).

## Fora do escopo
- `/demo` e o cliente web (`apexaudio/web_client/`) — pacote s2-webclient.
- Servir arquivos estáticos e o plugin de cópia — agente principal.
- `__root.tsx`, `src/start.ts`, configs — agente principal.
- Qualquer lógica de áudio ou host Python — pacote s3-host-ws.

## Por quê
- Preview vazio/genérico = produto inexistente para o usuário; a Fase 1 é a primeira
  impressão e valida a proposta antes do cliente web existir.
- Risco a evitar: visual genérico de template (gate explícito do roadmap) e head()
  faltando em alguma rota (gate de metadata).

## Fronteiras
- Recebe do agente principal: contrato de design (tokens/fonts/brand), contrato de
  rotas (`/`, `/ajuda`, `/demo` já referenciável por Link) e caminho de entrega.
- Entrega ao agente principal: arquivos JSX prontos para integração no projeto.

## Dono exclusivo de
- `src/routes/index.tsx`, `src/routes/ajuda.tsx`, `src/components/site/` (inteiros).
