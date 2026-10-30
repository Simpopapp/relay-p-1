# PRD — s6-android-contracts (o COMO do recorte)

Decisão central que você segue: D8 do PRD central (§10). Este arquivo detalha.

## 1. `Protocol.IncompleteFrame` (Protocol.kt)

- Dentro do `object Protocol`, ao lado de `ProtocolError`:
  `class IncompleteFrame(message: String) : ProtocolError(message)`.
- `decode` lança `IncompleteFrame` nos DOIS casos de incompletude:
  1. `length < HEADER_SIZE` ("buffer incompleto: …").
  2. `size < 0 || length - HEADER_SIZE < size` ("payload incompleto: …") — note que
     `size < 0` também é incompletude pelo contrato do parser (o buffer não contém
     o payload anunciado); mantenha as duas no mesmo tipo.
- `magic inválido` e qualquer outro erro permanecem `ProtocolError` comum.
- Atualize a KDoc de `decode` ("Levanta [IncompleteFrame] se o buffer não contém um
  frame completo; [ProtocolError] se magic/size forem inválidos").
- NENHUMA outra mudança em `Protocol.kt` (encode/parseConfigSync/etc. intactos).

## 2. `SocketManager.tryDecode` por tipo (SocketManager.kt)

```kotlin
private fun tryDecode(bb: ByteBufferReader): Pair<Protocol.Frame?, Int> {
    return try {
        Protocol.decode(bb.array, bb.offset, bb.size)
    } catch (e: Protocol.IncompleteFrame) {
        null to 0                       // aguarda mais bytes do socket
    } catch (e: Protocol.ProtocolError) {
        bb.reset()                      // corrompido: ressincroniza
        null to 0
    }
}
```

- `rg 'contains\("incompleto"\)'` no projeto → vazio (gate).
- Nenhuma mudança de comportamento além do mecanismo: incompleto continua
  aguardando, corrompido continua ressincronizando.

## 3. `ProtocolTest.kt` — testes do tipo novo (JUnit 4, JVM pura, sem SDK)

- `decode_truncated_header_throws_incomplete_frame`: buffer com menos de 16B →
  `IncompleteFrame` (assert com `assertFailsWith`-equivalente JUnit: try/catch +
  `assertTrue(e is Protocol.IncompleteFrame)`).
- `decode_truncated_payload_throws_incomplete_frame`: header válido + payload
  menor que o anunciado → `IncompleteFrame`.
- `decode_invalid_magic_is_not_incomplete`: magic errado → `ProtocolError` cujo
  `is Protocol.IncompleteFrame` é **false** (prova de que os tipos separaram).
- Reutilize os vetores existentes do arquivo para montar os buffers (não invente
  magic novo).

## 4. Gradle wrapper (proposta; binários ficam com o agente principal)

- O AGP do projeto é `com.android.application` 8.5.2 (raiz `build.gradle.kts`).
  Confirme via web a versão mínima de Gradle para AGP 8.5 (esperado: 8.7) e fixe
  `distributionUrl` para a release bin correspondente em
  `gradle/wrapper/gradle-wrapper.properties`
  (`distributionUrl=https\://services.gradle.org/distributions/gradle-<X.Y>-bin.zip`,
  mais `zipStoreBase/zipStorePath`/`distributionBase`/`distributionPath` padrão).
- `gradlew`/`gradlew.bat`: produza o conteúdo canônico da MESMA release do Gradle
  escolhida (fonte: repositório gradle/gradle na tag da release). Cite a fonte no relatório.
- `README.md` (novo, em `apexaudio/android_client/`): pré-requisitos (JDK 17, SDK 34,
  `local.properties`/`ANDROID_HOME`), comandos (`./gradlew assembleDebug`,
  `./gradlew testDebugUnitTest`), e nota de que os testes JVM (`ProtocolTest`,
  `CircularBufferTest`) rodam sem dispositivo.
- Justifique a versão no relatório com fonte; a prova de compilação segue externa
  (sem toolchain na sandbox — declarado).

## 5. Método de trabalho (obrigatório)

1. Leia os arquivos-alvo e o `ProtocolTest.kt` atual.
2. Copie o projeto para `/tmp/work-s6/` e aplique a proposta LÁ.
3. Verificação estática na cópia: `rg` dos gates acima + leitura linha a linha dos
   trechos alterados (não há toolchain Kotlin/Gradle nesta sandbox — declare isso
   no relatório; a prova de execução é o primeiro build externo).
4. Escreva os arquivos finais completos em `/tmp/remix/s6/` (caminhos relativos
   iguais aos do projeto).
5. NÃO escreva em `/dev-server` — você não tem permissão de escrita no projeto.

## Proibições

- Não editar nenhum Kotlin fora dos 3 arquivos listados; não tocar `desktop_host/**`
  nem pilares centrais; sem dependências novas.
- Não inventar números de versão: cite a matriz oficial AGP↔Gradle no relatório.
- Contrato errado? Não improvise: relate no relatório final.
