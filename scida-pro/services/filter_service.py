# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FilterConfig, FilterOperator, DataParameters
from logger import get_logger, FilterError


class DataFilter:
    def __init__(self, parameter: str, operator: str, value: float):
        self.parameter = parameter
        self.operator = operator
        self.value = value
        
    def to_list(self) -> List:
        return [self.parameter, self.operator, self.value]
    
    def to_plain_list(self) -> List:
        if self.value % 1 == 0:
            return [self.parameter, self.operator, int(self.value)]
        return [self.parameter, self.operator, self.value]
    
    def __str__(self) -> str:
        return f"{self.parameter}{self.operator}{self.value}"


class FilterService:
    def __init__(self):
        self.logger = get_logger('FilterService')
        self.filters: List[DataFilter] = []
        self.yield_loss_tables: List[pd.DataFrame] = []
        
    def get_default_filters(self) -> List[List]:
        return FilterConfig.DEFAULT_FILTERS.copy()
    
    def clear_filters(self) -> None:
        self.filters = []
        self.yield_loss_tables = []
        
    def add_filter(self, parameter: str, operator: str, value: str) -> bool:
        parameter = self._remove_whitespace(parameter)
        operator = self._remove_whitespace(operator)
        value = self._remove_whitespace(value)
        
        if (parameter in DataParameters.INTERNAL_NAMES and 
            operator in [FilterOperator.GREATER_THAN.value, FilterOperator.LESS_THAN.value] and
            self._is_number(value)):
            self.filters.append(DataFilter(parameter, operator, float(value)))
            return True
        return False
    
    def set_filters_from_table(self, table_data: List[List[str]]) -> int:
        self.filters = []
        valid_count = 0
        
        for row in table_data:
            if len(row) >= 3 and row[0] and row[1] and row[2]:
                if self.add_filter(str(row[0]), str(row[1]), str(row[2])):
                    valid_count += 1
        
        return valid_count
    
    def get_filters(self) -> List[DataFilter]:
        return self.filters
    
    def get_filters_as_list(self) -> List[List]:
        return [f.to_list() for f in self.filters]
    
    def get_filters_plain(self) -> List[List]:
        return [f.to_plain_list() for f in self.filters]
    
    def apply_filters(self, datasets: Dict[int, pd.DataFrame]) -> Dict[int, pd.DataFrame]:
        self.yield_loss_tables = []
        
        if not self.filters:
            return datasets
        
        for dataset_id in sorted(datasets.keys()):
            dataframe = datasets[dataset_id]
            original_count = len(dataframe)
            
            yield_loss_df = self._create_yield_loss_dataframe(original_count)
            dataframe, yield_loss_df = self._apply_filters_to_dataset(
                dataframe, yield_loss_df
            )
            
            dataset_name = dataframe.index.name
            dataframe = dataframe.reset_index(drop=True)
            dataframe.index.name = dataset_name
            datasets[dataset_id] = dataframe
            
            self.yield_loss_tables.append(yield_loss_df)
        
        datasets = self._handle_empty_datasets(datasets)
        return datasets
    
    def _create_yield_loss_dataframe(self, original_count: int) -> pd.DataFrame:
        columns = [f'Filter {i+1}' for i in range(FilterConfig.MAX_FILTERS)]
        index = ['Filter', 'Loss count']
        df = pd.DataFrame(index=index, columns=columns)
        df.index.name = str(original_count)
        return df
    
    def _apply_filters_to_dataset(
        self, 
        dataframe: pd.DataFrame, 
        yield_loss_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        for filter_idx, data_filter in enumerate(self.filters):
            if filter_idx >= FilterConfig.MAX_FILTERS:
                break
            
            yield_loss_df.iloc[0, filter_idx] = str(data_filter)
            
            try:
                if data_filter.operator == FilterOperator.GREATER_THAN.value:
                    loss_count = (dataframe[data_filter.parameter] > data_filter.value).sum()
                    dataframe = dataframe[dataframe[data_filter.parameter] <= data_filter.value]
                else:
                    loss_count = (dataframe[data_filter.parameter] < data_filter.value).sum()
                    dataframe = dataframe[dataframe[data_filter.parameter] >= data_filter.value]
                
                yield_loss_df.iloc[1, filter_idx] = loss_count
            except (KeyError, ValueError) as e:
                self.logger.warning(f"Filter error for {data_filter.parameter}: {str(e)}")
        
        return dataframe, yield_loss_df
    
    def _handle_empty_datasets(self, datasets: Dict[int, pd.DataFrame]) -> Dict[int, pd.DataFrame]:
        null_data = [-1, -1, -1, -1, -1, -1, -1]
        
        for dataset_id in datasets:
            if len(datasets[dataset_id]) == 0:
                datasets[dataset_id].loc[0] = null_data
        
        return datasets
    
    def get_yield_loss_tables(self) -> List[pd.DataFrame]:
        return self.yield_loss_tables
    
    def get_yield_loss_output(self, datasets: Dict[int, pd.DataFrame]) -> List[pd.DataFrame]:
        output = []
        
        for idx, yield_loss_df in enumerate(self.yield_loss_tables):
            processed_df = self._process_yield_loss_table(yield_loss_df, datasets, idx)
            output.append(processed_df)
        
        return output
    
    def _process_yield_loss_table(
        self, 
        yield_loss_df: pd.DataFrame, 
        datasets: Dict[int, pd.DataFrame],
        idx: int
    ) -> pd.DataFrame:
        yield_loss_df = yield_loss_df.copy()
        
        yield_loss_df['Total'] = np.nan
        yield_loss_df.iloc[1, FilterConfig.MAX_FILTERS] = yield_loss_df.iloc[1, :].sum()
        
        yield_loss_df.loc['Loss %'] = np.nan
        original_count = int(yield_loss_df.index.name)
        
        for col_idx in range(len(yield_loss_df.columns)):
            loss_value = yield_loss_df.iloc[1, col_idx]
            if pd.notna(loss_value) and loss_value != '':
                try:
                    yield_loss_df.iloc[2, col_idx] = np.round(
                        100 * float(loss_value) / original_count, 
                        decimals=2
                    )
                except (ValueError, TypeError):
                    pass
        
        yield_loss_df = yield_loss_df.dropna(axis=1, how='all')
        yield_loss_df.index.name = 'Data property'
        
        sorted_keys = sorted(datasets.keys())
        if idx < len(sorted_keys):
            dataset = datasets[sorted_keys[idx]]
            yield_loss_df['Data set'] = f"{dataset.index.name} ({original_count} cells)"
            yield_loss_df = yield_loss_df.set_index('Data set', append=True).swaplevel(0, 1)
        
        return yield_loss_df
    
    def _remove_whitespace(self, text: str) -> str:
        return str(text).replace(" ", "").replace("\t", "")
    
    def _is_number(self, value: str) -> bool:
        try:
            float(value)
            return True
        except ValueError:
            return False
