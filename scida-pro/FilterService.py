# -*- coding: utf-8 -*-
from typing import List, Tuple, Any
import numpy as np
import pandas as pd

from config import FilterConfig, DataColumns
from logger_config import setup_logger

logger = setup_logger(__name__)


class Filter:
    def __init__(self, parameter: str, operator: str, value: float) -> None:
        self.parameter = parameter
        self.operator = operator
        self.value = value

    def __repr__(self) -> str:
        return f"{self.parameter}{self.operator}{self.value}"

    def get_mask(self, dataframe: pd.DataFrame) -> pd.Series:
        column = dataframe[self.parameter]
        if self.operator == ">":
            return column > self.value
        if self.operator == "<":
            return column < self.value
        raise ValueError(f"Unknown operator: {self.operator}")

    def count_loss(self, dataframe: pd.DataFrame) -> int:
        return int(self.get_mask(dataframe).sum())

    def apply(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        return dataframe[~self.get_mask(dataframe)]


class FilterService:
    def __init__(self) -> None:
        self.user_filters: List[Filter] = []
        self.user_filters_plain: List[List[Any]] = []

    @staticmethod
    def get_default_filters() -> List[List[Any]]:
        return FilterConfig.DEFAULT_FILTERS

    @staticmethod
    def is_valid_filter(parameter: str, operator: str, value: str) -> bool:
        if parameter not in DataColumns.STANDARD:
            return False
        if operator not in FilterConfig.FILTER_OPERATORS:
            return False
        try:
            float(value)
            return True
        except ValueError:
            return False

    @staticmethod
    def remove_whitespace(text: str) -> str:
        return text.replace(" ", "").replace("\t", "")

    def parse_filters_from_table_data(self, table_data: List[Tuple[str, str, str]]) -> None:
        self.user_filters = []
        for parameter, operator, value in table_data:
            param_clean = self.remove_whitespace(parameter)
            op_clean = self.remove_whitespace(operator)
            val_clean = self.remove_whitespace(value)

            if self.is_valid_filter(param_clean, op_clean, val_clean):
                self.user_filters.append(Filter(param_clean, op_clean, float(val_clean)))

    def get_filters_for_table(self) -> List[List[str]]:
        return [[f.parameter, f.operator, str(f.value)] for f in self.user_filters]

    def convert_to_plain_format(self) -> None:
        self.user_filters_plain = []
        for filter_obj in self.user_filters:
            filter_setting = [filter_obj.parameter, filter_obj.operator]
            if filter_obj.value % 1 == 0:
                filter_setting.append(int(filter_obj.value))
            else:
                filter_setting.append(filter_obj.value)
            self.user_filters_plain.append(filter_setting)

    def load_plain_filters(self, plain_filters: List[List[Any]]) -> None:
        self.user_filters = []
        for item in plain_filters:
            if len(item) == 3:
                self.user_filters.append(Filter(str(item[0]), str(item[1]), float(item[2])))
        self.user_filters_plain = plain_filters

    def apply_filters(self, dataframe: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        original_count = len(dataframe)
        columns = [f'Filter {i + 1}' for i in range(FilterConfig.MAX_FILTERS)]
        index = ['Filter', 'Loss count']
        yield_loss = pd.DataFrame(index=index, columns=columns)
        yield_loss.index.name = original_count

        for filter_idx, filter_obj in enumerate(self.user_filters):
            if filter_idx >= FilterConfig.MAX_FILTERS:
                break

            yield_loss.iloc[0, filter_idx] = repr(filter_obj)
            yield_loss.iloc[1, filter_idx] = filter_obj.count_loss(dataframe)
            dataframe = filter_obj.apply(dataframe)

        return dataframe, yield_loss

    @staticmethod
    def process_yield_loss(yield_loss: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
        original_count = int(yield_loss.index.name)

        if 'Total' not in yield_loss.columns:
            yield_loss['Total'] = np.nan
            yield_loss.iloc[1, 12] = yield_loss.iloc[1, :].sum()

        yield_loss.loc['Loss %'] = np.nan

        for col_idx in range(len(yield_loss.columns)):
            if not pd.isna(yield_loss.iloc[1, col_idx]):
                yield_loss.iloc[2, col_idx] = np.round(
                    100 * yield_loss.iloc[1, col_idx] / original_count,
                    decimals=2
                )

        yield_loss = yield_loss.dropna(1, 'all')
        yield_loss.index.name = 'Data property'
        yield_loss['Data set'] = f'{dataset_name} ({original_count} cells)'
        yield_loss = yield_loss.set_index('Data set', append=True).swaplevel(0, 1)

        return yield_loss

    def has_filters(self) -> bool:
        return len(self.user_filters) > 0
