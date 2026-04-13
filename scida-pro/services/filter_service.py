# -*- coding: utf-8 -*-
"""
过滤服务模块 - 数据过滤业务逻辑
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from utils.logger import get_logger
from utils.validators import is_number, remove_whitespace
from utils.exceptions import FilterError
from config.constants import (
    FILTER_TABLE_ROWS,
    VALID_FILTER_OPERATORS,
    DATA_INDEX_COLUMNS,
    YIELD_LOSS_COLUMNS,
    YIELD_LOSS_INDEX,
)

logger = get_logger(__name__)


@dataclass
class FilterCondition:
    """过滤条件数据类"""
    parameter: str
    operator: str
    value: float
    
    def __str__(self) -> str:
        return f"{self.parameter}{self.operator}{self.value}"


class FilterService:
    """过滤服务类"""
    
    def __init__(self):
        self.filter_conditions: List[FilterCondition] = []
        self.yield_loss_data: Dict[int, pd.DataFrame] = {}
        
    def parse_filter_row(
        self,
        parameter: str,
        operator: str,
        value: str
    ) -> Optional[FilterCondition]:
        """
        解析单行过滤条件
        
        Args:
            parameter: 参数名
            operator: 操作符
            value: 值
            
        Returns:
            过滤条件对象，无效则返回 None
        """
        param_clean = remove_whitespace(parameter)
        operator_clean = remove_whitespace(operator)
        value_clean = remove_whitespace(value)
        
        if not param_clean or param_clean not in DATA_INDEX_COLUMNS:
            return None
            
        if operator_clean not in VALID_FILTER_OPERATORS:
            return None
            
        if not is_number(value_clean):
            return None
            
        return FilterCondition(
            parameter=param_clean,
            operator=operator_clean,
            value=float(value_clean)
        )
        
    def parse_filter_table(
        self,
        table_data: List[List[str]]
    ) -> List[FilterCondition]:
        """
        解析过滤表数据
        
        Args:
            table_data: 表格数据 [[param, op, value], ...]
            
        Returns:
            过滤条件列表
        """
        conditions = []
        
        for row in table_data:
            if len(row) >= 3:
                condition = self.parse_filter_row(row[0], row[1], row[2])
                if condition:
                    conditions.append(condition)
                    
        self.filter_conditions = conditions
        logger.info(f"解析到 {len(conditions)} 个过滤条件")
        return conditions
        
    def apply_filters(
        self,
        dataframe: pd.DataFrame,
        conditions: Optional[List[FilterCondition]] = None
    ) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """
        应用过滤条件
        
        Args:
            dataframe: 原始数据框
            conditions: 过滤条件列表，None 则使用已解析的条件
            
        Returns:
            (过滤后的数据框, 各条件的损失计数)
        """
        if conditions is None:
            conditions = self.filter_conditions
            
        if not conditions:
            return dataframe.copy(), {}
            
        filtered_df = dataframe.copy()
        loss_counts = {}
        
        for condition in conditions:
            if condition.parameter not in filtered_df.columns:
                continue
                
            if condition.operator == '>':
                mask = filtered_df[condition.parameter] > condition.value
                loss_count = mask.sum()
                filtered_df = filtered_df[~mask]
            else:  # '<'
                mask = filtered_df[condition.parameter] < condition.value
                loss_count = mask.sum()
                filtered_df = filtered_df[~mask]
                
            loss_counts[str(condition)] = int(loss_count)
            
        logger.info(f"过滤完成，原始行数: {len(dataframe)}, 过滤后: {len(filtered_df)}")
        return filtered_df, loss_counts
        
    def apply_filters_to_all_datasets(
        self,
        all_data: Dict[int, pd.DataFrame]
    ) -> Dict[int, pd.DataFrame]:
        """
        对所有数据集应用过滤
        
        Args:
            all_data: 所有数据集字典
            
        Returns:
            过滤后的数据集字典
        """
        filtered_data = {}
        self.yield_loss_data.clear()
        
        for index, dataframe in all_data.items():
            original_count = len(dataframe)
            name = dataframe.index.name
            
            filtered_df, loss_counts = self.apply_filters(dataframe)
            
            filtered_df = filtered_df.reset_index(drop=True)
            filtered_df.index.name = name
            filtered_data[index] = filtered_df
            
            yield_loss_df = self._create_yield_loss_dataframe(
                original_count, loss_counts
            )
            yield_loss_df.index.name = original_count
            self.yield_loss_data[index] = yield_loss_df
            
        logger.info(f"过滤已应用到 {len(all_data)} 个数据集")
        return filtered_data
        
    def _create_yield_loss_dataframe(
        self,
        original_count: int,
        loss_counts: Dict[str, int]
    ) -> pd.DataFrame:
        """
        创建良率损失数据框
        
        Args:
            original_count: 原始数据行数
            loss_counts: 损失计数字典
            
        Returns:
            良率损失数据框
        """
        columns = YIELD_LOSS_COLUMNS
        df = pd.DataFrame(index=YIELD_LOSS_INDEX, columns=columns)
        
        for i, (filter_str, count) in enumerate(loss_counts.items()):
            if i < len(columns):
                df.iloc[0, i] = filter_str
                df.iloc[1, i] = count
                
        return df
        
    def get_yield_loss_output(self, all_data: Dict[int, pd.DataFrame]) -> List[pd.DataFrame]:
        """
        获取良率损失输出数据
        
        Args:
            all_data: 所有数据集
            
        Returns:
            良率损失数据框列表
        """
        output = []
        
        for index in sorted(self.yield_loss_data.keys()):
            if index not in all_data:
                continue
                
            yl_df = self.yield_loss_data[index].copy()
            original_count = yl_df.index.name
            
            yl_df['Total'] = np.nan
            yl_df.iloc[1, 12] = yl_df.iloc[1, :].sum()
            
            yl_df.loc['Loss %'] = np.nan
            for j in range(len(yl_df.columns)):
                if pd.notna(yl_df.iloc[1, j]):
                    yl_df.iloc[2, j] = round(
                        100 * yl_df.iloc[1, j] / original_count, 2
                    )
                    
            yl_df = yl_df.dropna(axis=1, how='all')
            
            dataset_name = all_data[index].index.name
            cell_count = len(all_data[index])
            yl_df.index.name = original_count
            yl_df['Data set'] = f"{dataset_name} ({original_count} cells)"
            yl_df = yl_df.set_index('Data set', append=True).swaplevel(0, 1)
            
            output.append(yl_df)
            
        return output
        
    def convert_to_plain_format(
        self,
        conditions: List[FilterCondition]
    ) -> List[List]:
        """
        转换为纯格式（用于保存）
        
        Args:
            conditions: 过滤条件列表
            
        Returns:
            纯格式列表
        """
        plain_format = []
        
        for condition in conditions:
            row = [
                condition.parameter,
                condition.operator,
                int(condition.value) if condition.value % 1 == 0 else condition.value
            ]
            plain_format.append(row)
            
        return plain_format
