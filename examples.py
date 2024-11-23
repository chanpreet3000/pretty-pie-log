import logging

from pie_logger import PieLogger

logger = PieLogger('Logger')


logger.debug('This is a debug message', {'key': 'value'}, colorful=False)
logger.info('This is an info message', {'key': 'value'}, colorful=False)
logger.warning('This is a warning message', {'key': 'value'}, colorful=False)
logger.error('This is an error message', {'key': 'value'}, colorful=False)
logger.critical('This is a critical message', {'key': 'value'}, colorful=True)


@logger.log_execution(print_args_at_start=True, print_result_at_end=True, start_message="Starting my task",
                      start_message_log_level=logging.DEBUG, end_message_log_level=logging.INFO)
def main(str):
    logger.info("This is an info message")
    return True


main('here')
