import sys
from loguru import logger


MAX_TIMEOUT: int = 2147483647
logger.remove(0)
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | {extra[id]} | <level>{level}</level>: <level>{message}</level>"
)
