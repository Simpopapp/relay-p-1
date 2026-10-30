# PRD — s5-capture-hygiene (o COMO do recorte)

## 1. `LoopbackCapture` com inicializador de thread

- Novo parâmetro no construtor:
  `def __init__(self, max_queue: int = 64, thread_initializer: Callable[[], None] | None = None)`.
- O inicializador é executado DENTRO da thread de captura, no início de `_run`,
  antes do primeiro chunk; exceções são engolidas (mesmo `try/except Exception: pass`
  de hoje — prioridade é best-effort, nunca derruba a captura). Comentário explica o porquê.
- `_run` volta a ser o método canônico: NENHUMA atribuição `capture._run = ...`
  pode restar no arquivo (gate: `rg "capture\._run ="` vazio).
- `open_loopback_capture()`:
  1. Detecta `win32process` (try/except ImportError — como hoje).
  2. Se disponível, define `_raise_priority()` que chama
     `win32api.GetCurrentThread()` + `win32process.SetThreadPriority(handle,
     win32process.THREAD_PRIORITY_TIME_CRITICAL)` (mesma semântica atual, inclusive
     o `except Exception: pass` interno).
  3. Constrói `LoopbackCapture(thread_initializer=_raise_priority if _raise else None)`.
- Comportamento observável PRESERVADO: fila com overrun descartando o mais antigo,
  `read_chunk(timeout)`, `silent_mode`, modo silencioso com quadros de zeros a cada
  `FRAME_MS`. Nada disso muda.

## 2. `tests/test_capture.py` (NOVO — sem WASAPI na sandbox)

Rode em qualquer cwd (os imports são `apexaudio.desktop_host.*`; o `tests/__init__.py`
da suíte s4 cuida do `sys.path` — não dependa dele no SEU arquivo: escreva imports
absolutos `from apexaudio.desktop_host...` e deixe o gate rodar pela discover padrão).

- `test_thread_initializer_runs_inside_capture_thread`: initializer grava
  `threading.current_thread().name` em uma lista; `start()`; aguarda ≤ 2s até a
  lista ter 1 item; assertion: nome == `"apex-audio-capture"` (prova de que roda na
  thread de captura, não na principal); `stop()` limpo.
- `test_initializer_exception_is_swallowed`: initializer que levanta `RuntimeError`;
  captura entra em modo silencioso e a fila continua recebendo quadros de zeros
  (`silent_mode is True` após ≤ 2s, `read_chunk` retorna 1920B de zeros).
- `test_overrun_drops_oldest`: encha a fila com `max_queue=2` chamando `_put` 3x
  com valores distintos; `read_chunk` retorna o 2º e depois o 3º (o mais antigo
  caiu) — testável sem thread, chamando `_put` diretamente.
- Testes de rede/captura não podem abrir áudio real: nada de `pyaudiowpatch` nos
  testes (a sandbox não tem; o modo silencioso é o caminho).

## 3. Rename em `adb_manager.py` / `main.py`

- `AdbStatus.forward_ok: bool` → `downlink_reverse_ok: bool` (é o resultado do
  primeiro `adb reverse`, o do downlink 59900 — Decisão D1).
- `detect_device()`: ajuste o construtor; docstring/comentário citando D1 permanecem.
- `main.py` `render_dashboard`: `adb.available and adb.downlink_reverse_ok and adb.reverse_ok`.
- `rg "forward_ok" apexaudio/desktop_host/` → vazio (gate).

## 4. Método de trabalho (obrigatório)

1. Leia os 3 arquivos-alvo.
2. Copie o projeto para `/tmp/work-s5/`, aplique a proposta LÁ e rode
   `python3 -m unittest discover -s apexaudio/desktop_host/tests -v` da raiz da
   cópia (os testes de rede existentes NÃO podem quebrar) — registre a saída real.
3. Escreva os arquivos finais completos em `/tmp/remix/s5/` (caminhos relativos
   iguais aos do projeto).
4. NÃO escreva em `/dev-server` — você não tem permissão de escrita no projeto.

## Proibições

- Não editar `network_server.py`, `tests/test_network_server.py`, `tests/__init__.py`,
  `config.py`, `protocol.py`, qualquer `.kt`, pilares centrais.
- Sem dependências novas (win32/win32api são opcionais por import — mantenha assim).
- Contrato errado? Não improvise: relate no relatório final.
