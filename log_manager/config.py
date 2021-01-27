import logging
import logging.config
from settings import LOGS_DIR
from pathlib import Path

path_log_files = LOGS_DIR / 'main'
if not path_log_files.exists():
    path_log_files.mkdir()

path_log_files = LOGS_DIR / 'errors'
if not path_log_files.exists():
    path_log_files.mkdir()

LOGGING_CONFIG = {
        'version': 1,
        'formatters': {
            'detailed': {
                'class': 'logging.Formatter',
                'format': '%(asctime)s %(name)-15s %(levelname)-8s %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
            },
            'cli_log_file': {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename':  LOGS_DIR / 'main' / 'base.log',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'interval': 1,
                'when': 'midnight',
                'backupCount': 5
            },
            'errors': {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': LOGS_DIR / 'errors' / 'errors.log',
                'level': 'ERROR',
                'formatter': 'detailed',
                'interval': 1,
                'when': 'midnight',
                'backupCount': 5
            },
        },
        'loggers': {
            '': {
                'handlers': ['cli_log_file', 'console', 'errors'],
                'level': 'DEBUG',
                'propagate': False,
            }
        }
    }

logging.config.dictConfig(LOGGING_CONFIG)

