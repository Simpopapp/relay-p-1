# Roadmap — s6-android-contracts

## Fase A — Diagnóstico
- [ ] Ler `Protocol.kt`, `SocketManager.kt`, `ProtocolTest.kt`, `build.gradle.kts` (raiz e app).
- Gates: trecho do `tryDecode` atual citado no relatório (evidência do acoplamento).

## Fase B — Tipo `IncompleteFrame`
- [ ] `Protocol.kt`: subclasse + 2 pontos de lançamento + KDoc.
- [ ] `ProtocolTest.kt`: 3 testes novos (header truncado, payload truncado, magic ≠ incompleto).
- Gates: `rg "IncompleteFrame"` mostra os 3 pontos; asserções conferem com a implementação por leitura.

## Fase C — `SocketManager.tryDecode` por tipo
- [ ] catch por tipo (`IncompleteFrame` → aguarda; `ProtocolError` → `bb.reset()`).
- Gates: `rg 'contains\("incompleto"\)'` vazio no projeto.

## Fase D — Gradle wrapper (especificação)
- [ ] Versão do Gradle confirmada na matriz AGP↔Gradle oficial (fonte citada).
- [ ] `gradle-wrapper.properties`, `gradlew`, `gradlew.bat` (canônicos da release) e `README.md` de build.
- Gates: `distributionUrl` coerente com a versão justificada; scripts citam a fonte.

## Fase E — Entrega
- [ ] Arquivos finais completos em `/tmp/remix/s6/` + relatório no formato do system prompt.
- Gates: verificação estática registrada; limitação "sem toolchain Kotlin" declarada.
