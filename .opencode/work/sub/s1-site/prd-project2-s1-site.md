# PRD — s1-site (site vitrine, N=2)

## Decisões técnicas já tomadas (siga sem reabrir)
- D2-5 do PRD central: o site é vitrine/demo/ajuda; **não transporta áudio**.
- Stack: TanStack Start v1 (React 19, roteamento por arquivos em `src/routes/`),
  Tailwind v4 com tokens OKLCH já definidos em `src/styles.css`, componentes
  shadcn/radix em `src/components/ui/*`, ícones `lucide-react`.
- Idioma: **pt-BR** em toda a copy. Marca: **ApexAudio**.
- Fontes já carregadas no `__root.tsx`: Space Grotesk (sans) e Fraunces (serif).
  Não adicione `<link>` de fonte nem edite `__root.tsx`.
- Tema escuro (`class="dark"` já no root); use os tokens (`bg-background`,
  `text-foreground`, `text-primary`, `border-border`…) — não hardcode cores.

## Contrato de design (do agente principal — obrigatório)
- Identidade: "hardware de áudio de precisão" — escuro, tipografia forte, acento
  âmbar (`--primary`), linhas finas, nada de gradiente roxo genérico de template.
- Brand block: ícone + "ApexAudio" à esquerda; nav à direita com `Início`,
  `Demo`, `Ajuda` (Links do router) e badge "para Windows".
- Home, seções em ordem:
  1. **Hero**: título forte ("O som do PC, no fone do celular — pelo cabo USB"),
     sub com a proposta de 2 vias (PC→fone, celular→PC), CTA primário
     "Baixar para Windows" + CTA secundário "Ver demonstração" (Link /demo).
  2. **Como funciona**: 4 passos numerados (timeline/grade): 1) ative Depuração USB,
     2) baixe e execute o ApexAudio.exe, 3) conecte o cabo e toque em Conectar,
     4) escolha "CABLE Output" como microfone no Discord/jogo.
  3. **As duas vias**: bloco explicando PC→fone (WASAPI loopback, 10ms) e
     celular→PC (microfone→VB-Cable), sem IP/Wi-Fi/firewall.
  4. **Download**: card final repetindo o botão com nota de requisitos (Windows 10/11,
     cabo USB, Chrome no celular).
- /ajuda, seções com âncoras e navegação lateral ou sumário:
  1. **Depuração USB** (passo a passo numerado, Android 10+).
  2. **Primeira conexão** (exe, cabo, Conectar).
  3. **Microfone no Discord** (escolher CABLE Output; teste de voz).
  4. **Problemas comuns** (tabela/accordion: celular não detectado, sem som,
     latency alta, página não abre).
  5. **Antivírus** (PyInstaller pode gerar falso positivo; explicação e o que fazer).
- Download button: `href="https://github.com/apexaudio/apexaudio/releases/latest"`
  (endereço provisório — registre no relatório; não invente número de versão).

## Requisitos de rota (TanStack Start — não viole)
- Cada rota: `createFileRoute("/ajuda")` etc., com `head()` próprio e completo:
  title único + description + og:title + og:description + og:type "website" +
  twitter:card "summary_large_image". Nada de "Lovable App" ou title genérico.
- Navegação interna só com `Link`/`useRouter` de `@tanstack/react-router`;
  **nunca** react-router-dom; âncoras internas via `href="#secao"`.
- Não crie `src/routes/_app/*` nem layout duplicando "/".
- Imports de componentes ui: `@/components/ui/*`; use Accordion para problemas
  comuns, Card, Badge, Button conforme fizer sentido — sem exagero.

## Estrutura de entrega (obrigatório)
- Escreva os arquivos completos em `/tmp/remix/s1-site/` espelhando o projeto:
  - `/tmp/remix/s1-site/src/routes/index.tsx`
  - `/tmp/remix/s1-site/src/routes/ajuda.tsx`
  - `/tmp/remix/s1-site/src/components/site/*.tsx`
  - Um `RELATORIO.md` na raiz do pacote.
- Imports entre seus arquivos: `@/components/site/<nome>` (o agente integra na
  mesma árvore, então os caminhos valem como se já estivessem no projeto).
- JSX válido e completo (sem `...`), sem dependência nova, sem CSS global novo.

## Escopo por fase e aceite
Ver `roadmap-proj2-s1-site.md`. Aceite mensurável:
- Home tem hero, 4 passos, duas vias, download — todos visíveis no código.
- Ajuda cobre os 5 blocos do contrato, com âncoras funcionando (`id=` corretos).
- Zero TODO/placeholder de copy; textos reais em pt-BR, tom direto e leigo-friendly.
- head() completo nas duas rotas, títulos distintos.

## Casos de borda / atenção
- Links para /demo existem como rota no projeto integrado — use `to="/demo"` normalmente.
- Mobile-first: nav compacta, passos empilham em 1 coluna (gate do Playwright será mobile).
- Sem `use client`, sem state desnecessário; páginas são estáticas.

## Proibições
- Não edite `__root.tsx`, `src/start.ts`, `vite.config.ts`, `styles.css`, `/demo`.
- Não instale dependências; não use imagens externas; ícones só lucide-react.
- Não toque em `apexaudio/` nem nos pilares centrais ou de outros subagentes.

## Registro de decisões (preencha, numerado)
- (vazio — o subagente registra aqui decisões de implementação)

## Tools recomendadas
- Leitura de referência: `src/routes/index.tsx` atual (a substituir) para ver
  convenções de head()/createFileRoute; componentes em `src/components/ui/`.
