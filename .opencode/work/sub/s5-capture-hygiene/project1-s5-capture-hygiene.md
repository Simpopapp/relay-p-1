# Planejamento — s5-capture-hygiene (recorte do projeto N=1)

## Missão
Eliminar o monkey-patch de `_run` em `audio_capture.py` (a injeção de prioridade
time-critical esconde a lógica de thread e é frágil) e corrigir a mentira do
dashboard: `AdbStatus.forward_ok` descreve um `reverse`, herança do desenho
antigo que o monitor já apontou duas vezes.

## Por quê
- Monkey-patch (`capture._run = _runner`) quebra se `_run` for renomeado/tipado e
  esconde onde a prioridade é aplicada; a forma limpa é um inicializador de thread
  injetado no construtor.
- O dashboard decide "Device detected" por `adb.available and adb.forward_ok and
  adb.reverse_ok` — com o rename, a leitura fica honesta (`downlink_reverse_ok`).

## Escopo (arquivos SEUS, via proposta em /tmp)
- `apexaudio/desktop_host/audio_capture.py` — construtor com inicializador de thread.
- `apexaudio/desktop_host/tests/test_capture.py` — NOVO arquivo de teste.
- `apexaudio/desktop_host/adb_manager.py` — rename do campo.
- `apexaudio/desktop_host/main.py` — ajuste ao rename.

## Fora do escopo (de outros pacotes — não toque)
- `network_server.py`, `tests/test_network_server.py`, `tests/__init__.py` → s4-host-realtime.
- `config.py`, qualquer `.kt`, wrapper Gradle, pilares centrais.

## Fronteiras
- Recebe: `LoopbackCapture` atual (fila, `_put` com descarte do mais antigo, modo silencioso) e `open_loopback_capture` com o monkey-patch.
- Entrega: arquivos finais completos em `/tmp/remix/s5/` + relatório com evidência.
