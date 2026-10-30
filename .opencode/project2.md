ApexAudio 2 — "pluga e usa", sem Android Studio, sem compilar nada.

A ideia continua a mesma do project1 (PC ➔ fone do celular e microfone do celular ➔ PC
pelo cabo USB, com latência de cabo), mas o caminho até o uso real fica mínimo:

1. O que some em relação ao project1

  - Some o app Android nativo (Kotlin, Gradle, Android Studio, APK, assinatura).
    O "app do celular" vira uma página web aberta no Chrome do próprio celular.
  - Some a instalação de Python, pip e VB-Cable feita na mão. O PC recebe um único
    executável pronto (gerado automaticamente na nuvem, o usuário só baixa).
  - Some a instalação manual do ADB. O executável traz/baixa o ADB sozinho.

2. Por que isso funciona (o "pulo do gato" novo)

  - O executável no PC liga um pequeno servidor local e faz `adb reverse` da porta dele.
  - No celular, o Chrome abre `http://localhost:59900`. Para o navegador, "localhost" é
    um endereço seguro — então ele LIBERA o microfone sem precisar de certificado/HTTPS.
  - A página usa recursos nativos do navegador: microfone (getUserMedia) e reprodução
    de baixa latência (Web Audio / AudioWorklet). O áudio viaja por WebSocket dentro do
    mesmo túnel USB, sem roteador, sem IP, sem firewall.

3. A experiência de uso no dia a dia

  1. Primeira vez: no celular, ativa "Depuração USB" (único passo técnico, 1 vez só).
  2. Baixa o ApexAudio.exe no site do projeto e dá dois cliques.
     - Na 1ª execução ele oferece instalar o microfone virtual (VB-Cable) com um clique.
  3. Pluga o cabo. O exe detecta o celular e abre a página sozinho no Chrome do celular
     (via adb), ou mostra "abra localhost:59900 no celular".
  4. Toca em "Conectar" na página (e "Adicionar à tela inicial" para virar ícone).
  5. No Discord/jogo escolhe "CABLE Output" como microfone. Pronto.

4. O site do projeto (o que aparece no preview)

  - Página inicial explicando o produto em 4 passos, com botão de download do exe.
  - Uma demo da tela do celular (mesma interface da página do celular) que funciona
    no próprio preview em modo demonstração, para o usuário ver como fica.
  - Página de ajuda: depuração USB, problemas comuns, como escolher o microfone.

5. O que fica de fora de propósito

  - Loja de apps, contas, nuvem, escalabilidade, multiusuário, iPhone (Safari não
    permite o mesmo truque de forma confiável) — não servem ao uso prático.
