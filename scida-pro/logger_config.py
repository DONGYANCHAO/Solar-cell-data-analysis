# -*- coding: utf-8 -*-
import logging
import sys
from functools import wraps
from typing import Callable, Any
from PyQt5 import QtWidgets

from config import LoggingConfig


def setup_logger(name: str = __name__) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(LoggingConfig.FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, LoggingConfig.LEVEL))
    return logger


logger = setup_logger(__name__)


def handle_exceptions(parent: Any = None) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except UnicodeEncodeError as e:
                logger.error("Non-ASCII filename error: %s", str(e))
                if parent and hasattr(parent, 'tr'):
                    _show_error(parent, parent.tr("Warning"), parent.tr(ExceptionMessages.NON_ASCII_FILENAME))
                return None
            except FileNotFoundError as e:
                logger.error("File not found: %s", str(e))
                if parent and hasattr(parent, 'tr'):
                    _show_error(parent, parent.tr("Warning"),
                                parent.tr(ExceptionMessages.FILE_NOT_FOUND.format(e.filename)))
                return None
            except KeyError as e:
                logger.error("Key error in data processing: %s", str(e))
                if parent and hasattr(parent, 'tr'):
                    _show_error(parent, parent.tr("Warning"), parent.tr(ExceptionMessages.READ_ERROR))
                return None
            except ValueError as e:
                logger.error("Value error: %s", str(e))
                return None
            except PermissionError as e:
                logger.error("Permission error: %s", str(e))
                return None
            except Exception as e:
                logger.exception("Unexpected error in %s: %s", func.__name__, str(e))
                return None
        return wrapper
    return decorator


def _show_error(parent: QtWidgets.QWidget, title: str, message: str) -> None:
    QtWidgets.QMessageBox.about(parent, title, message)


class ExceptionMessages:
    NON_ASCII_FILENAME = "Filenames with non-ASCII characters were found.\n\nThe application currently only supports ASCII filenames."
    READ_ERROR = "Error while reading data files.\n\nData labels were perhaps not recognized."
    EMPTY_DATA = "Empty data sets were found.\n\nThe application only accepts data entries with a value for Voc, Isc, FF, Eta, Rser, Rsh and Irev. All values also need to be non-negative."
    FILE_NOT_FOUND = "Could not read file \"{}\""
    FILE_SAVE_ERROR = "Could not save file \"{}\""
    NO_DATA = "Please load data files"
