# -*- coding: utf-8 -*-
import os
import ntpath
import pickle
from typing import List, Tuple, Optional, Any

import pandas as pd

from config import FileExtensions, KEEP_CHARACTERS
from logger_config import setup_logger, handle_exceptions

logger = setup_logger(__name__)


class FileService:
    def __init__(self) -> None:
        self.previous_directory = ""

    @staticmethod
    def is_ascii_filename(filename: str) -> bool:
        try:
            filename.encode('ascii')
            return True
        except UnicodeEncodeError:
            logger.warning("Non-ASCII filename detected: %s", filename)
            return False

    @staticmethod
    def sanitize_filename(name: str) -> str:
        valid_filename = "".join(c for c in name if c.isalnum() or c in KEEP_CHARACTERS).rstrip()
        return valid_filename[:39]

    @staticmethod
    def get_basename_without_extension(filepath: str) -> str:
        return ntpath.splitext(ntpath.basename(filepath))[0]

    def update_previous_directory(self, filepath: str) -> None:
        self.previous_directory = ntpath.dirname(filepath)

    @handle_exceptions()
    def load_data_file(self, filepath: str, columns: List[str]) -> Optional[pd.DataFrame]:
        _, file_extension = ntpath.splitext(filepath)

        if file_extension.lower() == ".csv":
            return self._load_csv(filepath, columns)
        return self._load_excel(filepath, columns)

    @staticmethod
    def _load_csv(filepath: str, columns: List[str]) -> Optional[pd.DataFrame]:
        try:
            return pd.read_csv(filepath)[columns].dropna()
        except KeyError:
            try:
                return pd.read_csv(filepath, sep=';')[columns].dropna()
            except KeyError:
                logger.error("Failed to read CSV columns: %s", columns)
                raise

    @staticmethod
    def _load_excel(filepath: str, columns: List[str]) -> Optional[pd.DataFrame]:
        try:
            excel_file = pd.read_excel(filepath)
            return excel_file[columns].dropna()
        except KeyError:
            logger.error("Failed to read Excel columns: %s", columns)
            raise

    @handle_exceptions()
    def save_csv(self, dataframe: pd.DataFrame, filepath: str) -> None:
        dataframe.to_csv(filepath, index=False)
        logger.info("Saved CSV file: %s", filepath)

    @handle_exceptions()
    def load_filters(self, filepath: str) -> Optional[List[List[Any]]]:
        with open(filepath, 'rb') as file_handle:
            filters = pickle.load(file_handle)
        logger.info("Loaded filter settings from: %s", filepath)
        return filters

    @handle_exceptions()
    def save_filters(self, filters: List[List[Any]], filepath: str) -> None:
        with open(filepath, 'wb') as file_handle:
            pickle.dump(filters, file_handle)
        logger.info("Saved filter settings to: %s", filepath)

    @handle_exceptions()
    def load_custom_labels(self, filepath: str) -> List[str]:
        with open(filepath, 'rb') as file_handle:
            first_line = file_handle.readline()
        first_line = first_line.decode("utf-8")
        first_line = "".join(first_line.split())
        labels = first_line.split(",")
        logger.info("Loaded custom labels: %s", labels)
        return labels

    @staticmethod
    def check_overwrite(filepath: str) -> bool:
        return os.path.isfile(filepath)

    @staticmethod
    def get_save_path(directory: str, filename: str) -> str:
        if os.name == 'nt':
            return os.path.join(directory, filename)
        return os.path.join(directory, filename)

    @staticmethod
    def get_file_url(filepath: str) -> str:
        if not filepath.startswith('/'):
            return 'file:///' + filepath
        return 'file://' + filepath
