import pathlib

FILE_DB = pathlib.Path(__file__).parent / 'database.sqlite'
FILE_TEST_DB = pathlib.Path(__file__).parent / 'db_test.sqlite'
LOGS_PATH = pathlib.Path.cwd() / 'logs' / 'common.log'
LOGS_DIR = pathlib.Path.cwd() / 'logs'

TIME_SESSION_CLOSE = 15 * 60  # дефолтное время в секундах, отведенное на длительность сессии

if not LOGS_PATH.parent.exists():
    LOGS_PATH.parent.mkdir(parents=True)
    LOGS_PATH.touch()
