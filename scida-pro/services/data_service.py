# -*- coding: utf-8 -*-
"""
数据服务模块 - 数据处理业务逻辑
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from config.constants import (
    LABEL_FORMATS,
    DATA_INDEX_COLUMNS,
    CONVERSION_FACTORS,
    NULL_DATA_VALUES,
    DATASET_NAME_MAX_LENGTH,
    SUMMARY_COLUMNS,
    SUMMARY_INDEX,
)
from utils.logger import get_logger
from utils.exceptions import DataLoadError, DataValidationError

logger = get_logger(__name__)


class DataService:
    """数据处理服务类"""
    
    def __init__(self):
        self.all_data: Dict[int, pd.DataFrame] = {}
        self.label_format: int = 0
        self.label_formats: Dict[int, List[str]] = LABEL_FORMATS.copy()
        
    def get_data(self) -> Dict[int, pd.DataFrame]:
        """获取所有数据"""
        return self.all_data
        
    def get_dataset(self, index: int) -> Optional[pd.DataFrame]:
        """获取指定数据集"""
        return self.all_data.get(index)
        
    def get_dataset_count(self) -> int:
        """获取数据集数量"""
        return len(self.all_data)
        
    def clear_data(self) -> None:
        """清空所有数据"""
        self.all_data.clear()
        logger.info("所有数据已清空")
        
    def set_label_format(self, format_index: int) -> None:
        """设置标签格式"""
        if format_index not in self.label_formats:
            raise ValueError(f"无效的标签格式索引: {format_index}")
        self.label_format = format_index
        logger.info(f"标签格式设置为: {format_index}")
        
    def get_current_label_format(self) -> List[str]:
        """获取当前标签格式"""
        return self.label_formats[self.label_format]
        
    def set_custom_label_format(self, labels: List[str]) -> None:
        """设置自定义标签格式"""
        self.label_formats[4] = labels
        self.label_format = 4
        logger.info(f"自定义标签格式设置: {labels}")
        
    def add_dataframe(self, dataframe: pd.DataFrame, name: str) -> int:
        """
        添加数据框
        
        Args:
            dataframe: 数据框
            name: 数据集名称
            
        Returns:
            数据集索引
        """
        index = len(self.all_data)
        dataframe.index.name = name[:DATASET_NAME_MAX_LENGTH]
        self.all_data[index] = dataframe
        logger.info(f"数据集 '{name}' 已添加，索引: {index}")
        return index
        
    def remove_dataset(self, index: int) -> bool:
        """移除指定数据集"""
        if index in self.all_data:
            del self.all_data[index]
            self._reindex_data()
            logger.info(f"数据集索引 {index} 已移除")
            return True
        return False
        
    def _reindex_data(self) -> None:
        """重新索引数据字典"""
        new_data = {}
        for i, (old_index, dataframe) in enumerate(self.all_data.items()):
            new_data[i] = dataframe
        self.all_data = new_data
        
    def combine_datasets(self) -> Optional[pd.DataFrame]:
        """
        合并所有数据集
        
        Returns:
            合并后的数据框，如果数据不足则返回 None
        """
        if len(self.all_data) <= 1:
            logger.warning("数据集不足，无法合并")
            return None
            
        combined = pd.concat(
            [self.all_data[i] for i in sorted(self.all_data.keys())],
            ignore_index=True
        )
        combined.index.name = 'Combined data set'
        
        self.all_data.clear()
        self.all_data[0] = combined
        
        logger.info(f"数据集已合并，共 {len(combined)} 行")
        return combined
        
    def rename_dataset(self, index: int, new_name: str) -> bool:
        """
        重命名数据集
        
        Args:
            index: 数据集索引
            new_name: 新名称
            
        Returns:
            是否成功
        """
        if index not in self.all_data:
            return False
            
        valid_name = "".join(
            c for c in new_name if c.isalnum() or c in (' ', '.', '_')
        ).rstrip()
        
        if valid_name:
            self.all_data[index].index.name = valid_name[:DATASET_NAME_MAX_LENGTH]
            logger.info(f"数据集 {index} 重命名为: {valid_name}")
            return True
        return False
        
    def process_loaded_data(
        self,
        dataframe: pd.DataFrame,
        label_format: int
    ) -> Optional[pd.DataFrame]:
        """
        处理加载的数据
        
        Args:
            dataframe: 原始数据框
            label_format: 标签格式
            
        Returns:
            处理后的数据框，无效则返回 None
        """
        try:
            target_columns = self.label_formats[0]
            dataframe.columns = target_columns
        except (KeyError, ValueError) as e:
            logger.error(f"列名映射失败: {e}")
            return None
            
        dataframe = dataframe.apply(pd.to_numeric, errors='coerce')
        dataframe = dataframe[dataframe > 0]
        
        if dataframe.empty:
            logger.warning("处理后数据为空")
            return None
            
        dataframe = self._apply_format_conversion(dataframe, label_format)
        
        return dataframe
        
    def _apply_format_conversion(
        self,
        dataframe: pd.DataFrame,
        label_format: int
    ) -> pd.DataFrame:
        """
        应用格式特定的转换
        
        Args:
            dataframe: 数据框
            label_format: 标签格式
            
        Returns:
            转换后的数据框
        """
        dataframe = dataframe.copy()
        
        if label_format == 1:
            if 'Eta' in dataframe.columns:
                dataframe.loc[:, 'Eta'] *= CONVERSION_FACTORS['eta_percent']
            if 'FF' in dataframe.columns:
                dataframe.loc[:, 'FF'] *= CONVERSION_FACTORS['ff_percent']
        elif label_format == 3:
            if 'Eta' in dataframe.columns:
                dataframe.loc[:, 'Eta'] *= CONVERSION_FACTORS['eta_percent']
                
        return dataframe
        
    def get_summary_statistics(self, index: int) -> Optional[pd.DataFrame]:
        """
        获取汇总统计信息
        
        Args:
            index: 数据集索引
            
        Returns:
            汇总统计数据框
        """
        if index not in self.all_data:
            return None
            
        dataframe = self.all_data[index]
        if dataframe.empty:
            return None
            
        summary = pd.DataFrame(index=DATA_INDEX_COLUMNS)
        
        for col in DATA_INDEX_COLUMNS:
            if col not in dataframe.columns:
                continue
                
            summary.loc[col, 'max'] = dataframe[col].max()
            summary.loc[col, 'median'] = dataframe[col].median()
            summary.loc[col, 'mean'] = dataframe[col].mean()
            
            if col in ['Uoc', 'Isc', 'FF', 'Eta']:
                summary.loc[col, 'std'] = dataframe[col].std()
            else:
                summary.loc[col, 'std'] = np.nan
                
        return summary
        
    def get_correlation_matrix(self, index: int) -> Optional[pd.DataFrame]:
        """
        获取相关性矩阵
        
        Args:
            index: 数据集索引
            
        Returns:
            相关性矩阵
        """
        if index not in self.all_data:
            return None
            
        dataframe = self.all_data[index]
        if len(dataframe) <= 1:
            return None
            
        corr = dataframe.corr().round(2)
        
        corr.iloc[:, 2:4] = np.nan
        corr.iloc[2:4, :] = np.nan
        corr.iloc[6, :] = np.nan
        corr.iloc[:, 6] = np.nan
        
        corr = corr.dropna(how='all').T.dropna(how='all')
        
        return corr
        
    def fill_empty_dataset(self, index: int) -> None:
        """
        填充空数据集
        
        Args:
            index: 数据集索引
        """
        if index in self.all_data and len(self.all_data[index]) == 0:
            self.all_data[index].loc[0] = NULL_DATA_VALUES
            logger.warning(f"数据集 {index} 为空，已填充默认值")
