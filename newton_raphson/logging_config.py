import logging


def initialize_logging(*, parent_logger_name, log_level) -> None:
    if not parent_logger_name:
        raise ValueError("parent_logger_name cannot be empty or None")
    parent_logger = logging.getLogger(parent_logger_name)

    parent_logger.setLevel(log_level)

    handler = logging.StreamHandler()

    formatter = logging.Formatter('[%(levelname)s] [%(asctime)s] [%(name)s:%(lineno)d] [%(funcName)s]  %(message)s')

    handler.setFormatter(formatter)

    parent_logger.addHandler(handler)
