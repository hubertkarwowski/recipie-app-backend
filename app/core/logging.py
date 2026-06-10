from loguru import logger
from app.config import settings


def setup_logging():
    logger.add(
        "logs/app.log",
        rotation="1 day",
        retention="7 days",
        format="<red>{time}</red> | <blue>{level}</blue> | <green>{message}</green>",
        colorize=False,
        diagnose=settings.DEBUG,
    )
