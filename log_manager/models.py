import logging
from logging.handlers import TimedRotatingFileHandler

from settings import LOGS_PATH


# depricated - удаление сразу после того как основной код перегрузим на нормальный логгер

def change_filename(filename):
    filename_parts = filename.rsplit('.', maxsplit=2)
    if filename_parts[-1] == 'log':
        return filename
    elif filename_parts[-2] == 'log':
        return filename_parts[0] + '.' + filename_parts[2] + '.log'
    else:
        print('Внутренняя ошибка: базовый файл логирования не заканчивается на ".log"')
        exit(-1)


def log_and_print(message, level=logging.DEBUG, print_need=True):
    """Loging and print message"""
    message_without_new_lines = message.replace('\n', ' ')
    data_messages = {
        logging.DEBUG: {
            'func': LOG.debug,
            'msg_prefix': ''},
        logging.INFO: {
            'func': LOG.info,
            'msg_prefix': ''},
        logging.WARNING: {
            'func': LOG.warning,
            'msg_prefix': 'Warning: '},
        logging.ERROR: {
            'func': LOG.error,
            'msg_prefix': 'Error: '},
        logging.CRITICAL: {
            'func': LOG.critical,
            'msg_prefix': 'Critical error: '}
    }

    if print_need:
        print(data_messages[level]['msg_prefix'] + message)

    data_messages[level]['func'](message_without_new_lines)


LOG = logging.getLogger('cli')

FORMATTER = \
    logging.Formatter('%(asctime)s - %(levelname)s -  %(name)s - %(message)s ')

ROTATION_LOGGING_HANDLER = \
    TimedRotatingFileHandler(
        LOGS_PATH, when='D', interval=1, backupCount=5, encoding='utf-8')
ROTATION_LOGGING_HANDLER.setFormatter(FORMATTER)
ROTATION_LOGGING_HANDLER.setLevel(logging.DEBUG)
ROTATION_LOGGING_HANDLER.namer = change_filename

LOG.addHandler(ROTATION_LOGGING_HANDLER)

LOG.setLevel(logging.DEBUG)
