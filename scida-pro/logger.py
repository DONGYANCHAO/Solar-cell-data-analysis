# -*- coding: utf-8 -*-
import logging
import sys
from typing import Optional
from pathlib import Path

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

_logger: Optional[logging.Logger] = None

def get_logger(name: str = 'SCiDA') -> logging.Logger:
    global _logger
    if _logger is None:
        _logger = logging.getLogger(name)
        _logger.setLevel(logging.DEBUG)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        _logger.addHandler(console_handler)
        
    return _logger

def set_log_file(log_path: str) -> None:
    logger = get_logger()
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(file_handler)

class SCiDAError(Exception):
    pass

class DataLoadError(SCiDAError):
    pass

class FileReadError(SCiDAError):
    pass

class FileSaveError(SCiDAError):
    pass

class FilterError(SCiDAError):
    pass

class ReportGenerationError(SCiDAError):
    pass

class NonASCIIFilenameError(SCiDAError):
    pass

class EmptyDataSetError(SCiDAError):
    pass

class UnsupportedFormatError(SCiDAError):
    pass

def validate_ascii_filename(filename: str) -> bool:
    try:
        filename.encode('ascii')
        return True
    except UnicodeEncodeError:
        return False

def handle_exception(exc: Exception, logger: logging.Logger = None) -> str:
    if logger is None:
        logger = get_logger()
    
    logger.error(f"Exception occurred: {type(exc).__name__}: {str(exc)}")
    return str(exc)
