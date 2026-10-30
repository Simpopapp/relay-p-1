# Planejamento — s6-android-contracts (recorte do projeto N=1)

## Missão
Fechar o acoplamento a texto de exceção no cliente Android: `SocketManager.tryDecode`
decide "buffer incompleto vs corrompido" por `message.contains("incompleto")` —
qualquer reescrita da mensagem quebra a ressincronização em silêncio. E deixar o
build externo menos incógnito: especificar o gradle wrapper (versão correta para o
AGP do projeto), cujos binários o agente principal versiona.

## Por quê
- Erro tipado (`IncompleteFrame`) é o padrão da Decisão D8: decisão por tipo sobrevive
  a reescrita de mensagens e torna o teste possível em JVM pura.
- O teste de hardware externo já tem incógnitas demais (permissões, VB-Cable);
  sem wrapper, "qual Gradle?" seria mais uma.

## Escopo (arquivos SEUS, via proposta em /tmp)
- `apexaudio/android_client/app/src/main/java/com/apex/audio/data/Protocol.kt` — tipo `IncompleteFrame`.
- `apexaudio/android_client/app/src/main/java/com/apex/audio/network/SocketManager.kt` — `tryDecode` por tipo.
- `apexaudio/android_client/app/src/test/java/com/apex/audio/ProtocolTest.kt` — testes do tipo novo.
- `apexaudio/android_client/gradle/wrapper/gradle-wrapper.properties` — conteúdo proposto.
- `apexaudio/android_client/README.md` (NOVO) — como compilar (JDK/SDK/Gradle).
- Textos de `gradlew`/`gradlew.bat` — consulte a versão canônica da mesma release do Gradle escolhida.

## Fora do escopo (de outros pacotes — não toque)
- Qualquer outro arquivo Kotlin (`CircularBuffer.kt`, `AudioTrackPlayer.kt`,
  `AudioRecordCapturer.kt`, `AudioBridgeService.kt`, `BridgeViewModel.kt`, `MainActivity.kt`).
- `desktop_host/**` → s4/s5. Pilares centrais. O JAR binário do wrapper fica para o
  agente principal — você entrega propriedades + scripts + justificativa.

## Fronteiras
- Recebe: `Protocol.kt` (única fonte de `ProtocolError`) e `SocketManager.kt` (único consumidor de `tryDecode`).
- Entrega: arquivos finais completos em `/tmp/remix/s6/` + relatório com a verificação estática.
