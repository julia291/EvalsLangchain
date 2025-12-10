import logging
from logging.config import dictConfig

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "standard": {
            "format": "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
        }
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "DEBUG"
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "standard",
            "level": "INFO",
            "filename": "app.log",
            "encoding": "utf-8"
        }
    },

    "root": {
        "handlers": ["console", "file"],
        "level": "DEBUG"
    }
}


def setup_logging():
    dictConfig(LOGGING_CONFIG)
