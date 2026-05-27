"""Configuração centralizada de logging com Loguru.

Fornece logger configurado com:
- Saída em stdout (colorida, filtrada)
- Persistência em arquivo (rotação diária, retenção de 30 dias)
"""

from loguru import logger
import sys
from pathlib import Path

# Remove o handler padrão do Loguru
logger.remove()

# Define diretório de logs na raiz do projeto
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "zapunlocked_{time:YYYY-MM-DD}.log"


def _filter_lid_logs(record):
    """Filtra mensagens de migração de LID (ruído do Neonize)."""
    return "Migrated to LID encryption" not in record["message"]


# Handler para console (stdout) com filtro
logger.add(
    sys.stdout,
    filter=_filter_lid_logs,
    level="DEBUG",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
)

# Handler para arquivo com rotação diária e retenção de 30 dias
logger.add(
    str(LOG_FILE),
    rotation="1 day",
    retention="30 days",
    level="INFO",
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)
