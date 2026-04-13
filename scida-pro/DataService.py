# -*- coding: utf-8 -*-
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from config import LabelFormat, DataColumns, NULL_DATA_ROW, Converters
from logger_config import setup_logger

logger = setup_logger(__name__)


class DataService:
    def __init__(self) -> None:
        self.datasets: Dict[int, pd.DataFrame] = {}
        self.next_index = 0

    def has_data(self) -> bool:
        return bool(self.datasets)

    def get_dataset_count(self) -> int:
        return len(self.datasets)

    def add_dataset(self, dataframe: pd.DataFrame, name: str) -> None:
        self.datasets[self.next_index] = dataframe
        self.datasets[self.next_index].index.name = name
        self.next_index += 1
        logger.info("Added dataset '%s' with %d rows", name, len(dataframe))

    def get_dataset(self, index: int) -> Optional[pd.DataFrame]:
        return self.datasets.get(index)

    def get_dataset_name(self, index: int) -> str:
        if index in self.datasets:
            return str(self.datasets[index].index.name)
        return ""

    def rename_dataset(self, index: int, new_name: str) -> None:
        if index in self.datasets:
            self.datasets[index].index.name = new_name
            logger.info("Renamed dataset %d to '%s'", index, new_name)

    def clear_all(self) -> None:
        self.datasets.clear()
        self.next_index = 0
        logger.info("Cleared all datasets")

    @staticmethod
    def to_numeric(dataframe: pd.DataFrame) -> pd.DataFrame:
        return dataframe.apply(pd.to_numeric, errors='coerce')

    @staticmethod
    def filter_positive_values(dataframe: pd.DataFrame) -> pd.DataFrame:
        return dataframe[dataframe > 0].dropna()

    def is_empty_dataset(self, index: int) -> bool:
        return index in self.datasets and self.datasets[index].empty

    def remove_dataset(self, index: int) -> None:
        if index in self.datasets:
            self.datasets.pop(index)
            logger.info("Removed dataset %d", index)

    def apply_label_format_conversion(self, index: int, label_format: LabelFormat) -> None:
        if index not in self.datasets:
            return

        if label_format == LabelFormat.B:
            self.datasets[index].loc[:, 'Eta'] *= 100
            self.datasets[index].loc[:, 'FF'] *= 100
        elif label_format == LabelFormat.D:
            self.datasets[index].loc[:, 'Eta'] *= 100

        self.datasets[index].columns = DataColumns.STANDARD
        logger.info("Applied label format %s to dataset %d", label_format.name, index)

    def fill_empty_dataset(self, index: int) -> None:
        if index in self.datasets and len(self.datasets[index]) == 0:
            self.datasets[index].loc[0] = NULL_DATA_ROW

    def combine_datasets(self) -> None:
        if self.get_dataset_count() <= 1:
            return

        dataset_list = [self.datasets[i] for i in sorted(self.datasets.keys())]
        combined = pd.concat(dataset_list, ignore_index=True)
        combined.index.name = 'Combined data set'

        self.datasets.clear()
        self.datasets[0] = combined
        self.next_index = 1
        logger.info("Combined %d datasets into one", len(dataset_list))

    def get_parameter_data(self, dataset_index: int, parameter: str) -> pd.Series:
        dataset = self.get_dataset(dataset_index)
        if dataset is None:
            raise ValueError(f"Dataset {dataset_index} not found")

        if parameter == 'Voc*Isc':
            return dataset['Uoc'] * dataset['Isc']
        if parameter == 'RserLfDfIEC':
            return dataset[parameter] * Converters.RSER_MULTIPLIER
        if parameter == 'Rsh':
            return dataset[parameter] / Converters.RSH_DIVISOR
        return dataset[parameter]

    def get_all_dataset_names(self) -> List[str]:
        return [self.get_dataset_name(i) for i in sorted(self.datasets.keys())]

    def get_all_datasets(self) -> List[pd.DataFrame]:
        return [self.datasets[i] for i in sorted(self.datasets.keys())]

    def calculate_summary(self, dataset_index: int) -> pd.DataFrame:
        from config import SummaryConfig
        dataset = self.get_dataset(dataset_index)
        if dataset is None:
            raise ValueError(f"Dataset {dataset_index} not found")

        summary = pd.DataFrame(index=SummaryConfig.INDEX, columns=SummaryConfig.COLUMNS)
        summary.index.name = 'Data property'
        dataset_name = self.get_dataset_name(dataset_index)
        summary['Data set'] = f'{dataset_name} ({len(dataset)} cells)'
        summary = summary.set_index('Data set', append=True).swaplevel(0, 1)

        for col_idx, _ in enumerate(dataset.columns):
            summary.iloc[0, col_idx] = dataset.iloc[dataset['Eta'].idxmax(), col_idx]
            summary.iloc[1, col_idx] = dataset.median()[col_idx]
            summary.iloc[2, col_idx] = dataset.mean()[col_idx]

            if col_idx in [0, 1, 4, 5]:
                summary.iloc[3, col_idx] = dataset.std()[col_idx]
            else:
                summary.iloc[3, col_idx] = np.nan

        summary = summary.apply(pd.to_numeric)
        summary.iloc[:, 2] *= Converters.RSER_MULTIPLIER
        summary.iloc[:, 3] /= Converters.RSH_DIVISOR

        for col_idx, rounding in enumerate(SummaryConfig.ROUNDING):
            summary.iloc[:, col_idx] = np.round(
                summary.iloc[:, col_idx].astype(np.double),
                decimals=rounding
            )

        return summary

    def calculate_correlation(self, dataset_index: int) -> pd.DataFrame:
        dataset = self.get_dataset(dataset_index)
        if dataset is None or len(dataset) <= 1:
            raise ValueError(f"Dataset {dataset_index} is invalid or too small")

        correlation = np.round(dataset.corr(), decimals=2)
        correlation.iloc[:, 2:4] = np.nan
        correlation.iloc[2:4, :] = np.nan
        correlation.iloc[6, :] = np.nan
        correlation.iloc[:, 6] = np.nan

        correlation = correlation.dropna(0, 'all').T.dropna(0, 'all')
        correlation.index.name = 'Data property'
        dataset_name = self.get_dataset_name(dataset_index)
        correlation['Data set'] = f'{dataset_name} ({len(dataset)} cells)'
        correlation = correlation.set_index('Data set', append=True).swaplevel(0, 1)

        return correlation

    def reset_dataset_index(self, index: int) -> None:
        if index in self.datasets:
            name = self.datasets[index].index.name
            self.datasets[index] = self.datasets[index].reset_index(drop=True)
            self.datasets[index].index.name = name
