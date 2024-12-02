# Collection of functions common to many workflows and not requiring datacube
import logging
import sys

# No relevant test
def get_logger(name: str, level:int = logging.INFO) -> logging.Logger:
    """Return a logger"""
    # Default logger
    #   log.hasHandlers() = False
    #   log.getEffectiveLevel() = 30 = warning
    #   log.propagate = True
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not len(logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(CustomFormatter())
        logger.addHandler(handler)
    logger.propagate = False  # Do not propagate up to root logger, which may have other handlers
    return logger

class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    green = "\x1b[32;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: green + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
