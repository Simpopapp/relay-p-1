"""Bootstrap independente de cwd.

A raiz está três pais acima de tests/__init__.py. Discovery com -s absoluto
importa testes como módulos soltos; test_network_server carrega este bootstrap
explicitamente nesse caso. Caminhos relativos de -s são relativos ao cwd.
"""
from pathlib import Path
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))
