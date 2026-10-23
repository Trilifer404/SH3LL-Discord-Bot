import logging
import os


class Sh3llFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[90m",
        logging.INFO: "\033[36m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[1;31m",
    }
    RESET = "\033[0m"
    COMPONENTS = {
        "sh3ll.bot": "BOT",
        "sh3ll.llm": "LLM",
        "sh3ll.tools": "TOOLS",
        "sh3ll.storage": "STORAGE",
    }

    def __init__(self, use_color: bool = False) -> None:
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(component)-7s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        record.component = self.COMPONENTS.get(record.name, record.name.upper())
        formatted = super().format(record)
        color = self.COLORS.get(record.levelno)
        if self.use_color and color:
            return f"{color}{formatted}{self.RESET}"
        return formatted


def configure_logging() -> None:
    requested_level = os.getenv("SH3LL_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, requested_level, None)
    invalid_level = not isinstance(level, int)
    if invalid_level:
        level = logging.INFO

    handler = logging.StreamHandler()
    handler.setFormatter(Sh3llFormatter(use_color=bool(getattr(handler.stream, "isatty", lambda: False)())))
    logging.basicConfig(level=level, handlers=[handler], force=True)

    logging.getLogger("discord.gateway").setLevel(logging.ERROR)
    logging.getLogger("discord.http").setLevel(logging.WARNING)
    for logger_name in ("urllib3", "requests", "chromadb", "langchain", "httpcore"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    if invalid_level:
        logging.getLogger("sh3ll").warning(
            "SH3LL_LOG_LEVEL inválido (%s); usando INFO.", requested_level
        )
