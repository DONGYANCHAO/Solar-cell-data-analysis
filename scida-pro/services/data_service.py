# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DataParameters, ConversionFactors, DataLabelFormat
from logger import get_logger, DataLoadError, EmptyDataSetError


class DataService:
    def __init__(self):
        self.logger = get_logger('DataService')
        self.datasets: Dict[int, pd.DataFrame] = {}
        self.label_format: int = DataLabelFormat.FORMAT_A.value
        
    def get_label_format(self) -> int:
        return self.label_format
    
    def set_label_format(self, format_id: int) -> None:
        self.label_format = format_id
        
    def get_label_columns(self) -> List[str]:
        return DataParameters.LABEL_FORMATS.get(self.label_format, DataParameters.LABEL_FORMATS[0])
    
    def get_internal_columns(self) -> List[str]:
        return DataParameters.LABEL_FORMATS[0]
    
    def add_dataset(self, dataset_id: int, dataframe: pd.DataFrame) -> None:
        self.datasets[dataset_id] = dataframe
        
    def remove_dataset(self, dataset_id: int) -> None:
        if dataset_id in self.datasets:
            del self.datasets[dataset_id]
            
    def clear_all_datasets(self) -> None:
        self.datasets.clear()
        
    def get_dataset(self, dataset_id: int) -> Optional[pd.DataFrame]:
        return self.datasets.get(dataset_id)
    
    def get_all_datasets(self) -> Dict[int, pd.DataFrame]:
        return self.datasets
    
    def get_dataset_count(self) -> int:
        return len(self.datasets)
    
    def get_next_dataset_id(self) -> int:
        if not self.datasets:
            return 0
        return max(self.datasets.keys()) + 1
    
    def apply_conversion(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        if self.label_format == DataLabelFormat.FORMAT_B.value:
            dataframe.loc[:, 'Eta'] *= ConversionFactors.PERCENTAGE_MULTIPLIER
            dataframe.loc[:, 'FF'] *= ConversionFactors.PERCENTAGE_MULTIPLIER
        elif self.label_format == DataLabelFormat.FORMAT_D.value:
            dataframe.loc[:, 'Eta'] *= ConversionFactors.PERCENTAGE_MULTIPLIER
        return dataframe
    
    def validate_and_clean_data(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        dataframe = dataframe.apply(pd.to_numeric, errors='coerce')
        dataframe = dataframe[dataframe > 0]
        dataframe = dataframe.dropna()
        return dataframe
    
    def rename_dataset(self, dataset_id: int, new_name: str) -> bool:
        if dataset_id not in self.datasets:
            return False
        
        keep_characters = (' ', '.', '_')
        valid_name = "".join(c for c in new_name if c.isalnum() or c in keep_characters).rstrip()
        
        if len(valid_name) > 0:
            self.datasets[dataset_id].index.name = valid_name[:ConversionFactors.DATASET_NAME_MAX_LENGTH - 1]
            return True
        return False
    
    def combine_datasets(self) -> Optional[pd.DataFrame]:
        if len(self.datasets) <= 1:
            return None
        
        combined = pd.concat(list(self.datasets.values()), ignore_index=True)
        combined.index.name = 'Combined data set'
        
        self.datasets.clear()
        self.datasets[0] = combined
        
        return combined
    
    def calculate_statistics(self, dataset_id: int) -> Optional[Dict]:
        if dataset_id not in self.datasets:
            return None
        
        data = self.datasets[dataset_id]
        
        stats = {
            'best_cell': data.iloc[data['Eta'].idxmax()],
            'median': data.median(),
            'mean': data.mean(),
            'std': data.std(),
            'count': len(data)
        }
        
        return stats
    
    def get_sorted_dataset_ids(self) -> List[int]:
        return sorted(self.datasets.keys())
    
    def dataset_exists(self, dataset_id: int) -> bool:
        return dataset_id in self.datasets
    
    def get_dataset_name(self, dataset_id: int) -> Optional[str]:
        if dataset_id in self.datasets:
            return self.datasets[dataset_id].index.name
        return None
    
    def get_dataset_cell_count(self, dataset_id: int) -> int:
        if dataset_id in self.datasets:
            return len(self.datasets[dataset_id])
        return 0
