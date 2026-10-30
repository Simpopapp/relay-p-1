# ApexAudio — cliente Android

## Pré-requisitos

- JDK 17, com `JAVA_HOME` apontando para sua instalação.
- Android SDK com Android SDK Platform 34 e Build Tools 34.0.0; licenças aceitas.
- Configure o SDK por `ANDROID_HOME` ou crie `local.properties` nesta pasta
  com `sdk.dir=/caminho/para/Android/Sdk` (não versione esse arquivo local).
- Acesso à internet no primeiro build para baixar Gradle e dependências.

O projeto usa AGP 8.5.2 e Gradle **8.7**, versão mínima/default da
[matriz oficial do AGP 8.5](https://developer.android.com/build/releases/agp-8-5-0-release-notes).
Os scripts canônicos vêm da tag `v8.7.0` do Gradle:
[gradlew](https://github.com/gradle/gradle/blob/v8.7.0/gradlew) e
[gradlew.bat](https://github.com/gradle/gradle/blob/v8.7.0/gradlew.bat).

## Build e testes

Execute nesta pasta:

```sh
./gradlew assembleDebug
./gradlew testDebugUnitTest
```

No Windows, use `gradlew.bat assembleDebug` e `gradlew.bat testDebugUnitTest`.
Em Unix, caso o checkout perca a permissão executável, use `chmod +x gradlew`.
O APK debug será gerado em `app/build/outputs/apk/debug/app-debug.apk`.

`ProtocolTest` e `CircularBufferTest` são testes JVM locais: não precisam de
aparelho nem emulador. A tarefa Android de testes ainda requer JDK/SDK e
as dependências de build acima.

## Integração do wrapper

Esta proposta entrega scripts e propriedades; o agente principal precisa
versionar também `gradle/wrapper/gradle-wrapper.jar` oficial do Gradle 8.7.
Sem esse JAR, os comandos do wrapper não funcionam. O binário não faz parte
deste pacote s6. Após integrá-lo, execute os dois comandos acima em ambiente
com toolchain Android. Nenhuma compilação Kotlin/Gradle foi executada na sandbox;
a validação deste pacote é estática, não uma prova de build.
