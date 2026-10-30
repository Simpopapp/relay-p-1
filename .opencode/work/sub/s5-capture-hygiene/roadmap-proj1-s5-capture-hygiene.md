# Roadmap — s5-capture-hygiene

## Fase A — Diagnóstico e cópia de validação
- [ ] Ler `audio_capture.py`, `adb_manager.py`, `main.py`.
- [ ] Copiar o projeto para `/tmp/work-s5/` e reproduzir o gate atual (14/14) na cópia.
- Gates: saída real da suíte na cópia registrada.

## Fase B — `LoopbackCapture` com inicializador de thread
- [ ] Parâmetro `thread_initializer` executado dentro da thread, exceções engolidas.
- [ ] `open_loopback_capture` sem monkey-patch (`rg "capture\._run ="` vazio).
- Gates: `tests/test_capture.py` verde na cópia (3 testes do PRD do recorte).

## Fase C — Rename honesto do ADB
- [ ] `AdbStatus.downlink_reverse_ok` em `adb_manager.py` + uso em `main.py`.
- Gates: `rg "forward_ok" apexaudio/desktop_host/` vazio; suíte 14/14 + captura verde na cópia.

## Fase D — Entrega
- [ ] Arquivos finais completos em `/tmp/remix/s5/` + relatório no formato do system prompt.
- Gates: todos os gates acima verdes na cópia; relatório com números reais.
