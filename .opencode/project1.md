A lógica prática do app se resume a criar um túnel direto de mão dupla que faz o
PC e o celular fingirem que estão fisicamente soldados um no outro, sem passar
por roteador, sem IPs e sem burocracia de rede.

1. As Duas Vias de Áudio (O que acontece a cada 10 milissegundos)

  - Via 1: PC ➔ Fone do Celular (Você escuta o PC)

    1.  O script no PC usa uma função nativa do Windows (WASAPI Loopback) para
        "clonar" exatamente o som que iria para a caixa de som.
    2.  Ele fatia esse som em pequenos pacotes brutos de 10 milissegundos.
    3.  Cospe esses pacotes pelo cabo USB direto para o fone do celular, sem
        conversão pesada, para o atraso ser imperceptível.

  - Via 2: Microfone do Celular ➔ PC (Você fala no Discord / Jogos)

    1.  O app no celular captura a sua voz do microfone físico em pedaços de 10
        milissegundos.
    2.  Joga esses pacotes de volta pelo cabo até o PC.
    3.  No PC, o script recebe essa voz e descarrega direto em um driver de
        microfone virtual (como o VB-Cable).
    4.  O Windows enxerga esse driver como se fosse um microfone físico de
        verdade plugado na placa-mãe.

2. O "Pulo do Gato" da Conexão (Por que não trava nem dá erro de IP)

Em vez de depender de Wi-Fi, antenas ou configurações de rede:

  - O app usa o comando adb pelo cabo USB. *(Atualização: a Decisão D1 do PRD §10
    mudou a topologia para `adb reverse` nas DUAS portas — 59900 e 59901 — porque o
    celular é o cliente TCP das duas; `adb forward` para 59900 não funcionaria. Siga o
    PRD, não este trecho original.)*
  - Isso cria uma porta virtual onde o celular e o PC conversam apontando para
    127.0.0.1 (localhost).
  - Resultado prático: O tráfego não passa pelo roteador, não bate nas regras de
    bloqueio do Firewall do Windows e opera com latência de cabo físico (menos
    de 20ms a 40ms no total).

3. A Experiência de Uso no dia a dia

1.  Você pluga o celular no PC com o cabo USB.
2.  Abre o executável no PC e clica em Start no app do celular.
3.  Coloca o fone de ouvido no celular.
4.  No Discord, jogo ou reunião, escolhe o microfone virtual. Pronto: você ouve
    tudo do computador pelo fone e fala normalmente pelo celular.
