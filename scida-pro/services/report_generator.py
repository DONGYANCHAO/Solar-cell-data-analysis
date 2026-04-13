# -*- coding: utf-8 -*-
"""
报告生成器模块 - Excel报告生成
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path

from utils.logger import get_logger
from utils.validators import validate_filename
from utils.exceptions import ReportGenerationError
from config.constants import (
    SUMMARY_COLUMNS,
    SUMMARY_INDEX,
    CONVERSION_FACTORS,
    ROUNDING_PRECISION,
)
from services.data_service import DataService

logger = get_logger(__name__)


class SummaryTableBuilder:
    """汇总表构建器"""
    
    def __init__(self, data_service: DataService):
        self.data_service = data_service
        self.summaries: List[pd.DataFrame] = []
        
    def build(self) -> List[pd.DataFrame]:
        """构建所有汇总表"""
        self.summaries.clear()
        all_data = self.data_service.get_data()
        
        for index in sorted(all_data.keys()):
            dataframe = all_data[index]
            summary = self._build_single_summary(dataframe, index)
            if summary is not None:
                self.summaries.append(summary)
                
        logger.info(f"生成了 {len(self.summaries)} 个汇总表")
        return self.summaries
        
    def _build_single_summary(
        self,
        dataframe: pd.DataFrame,
        index: int
    ) -> Optional[pd.DataFrame]:
        """构建单个汇总表"""
        if dataframe.empty:
            return None
            
        summary = pd.DataFrame(index=SUMMARY_INDEX, columns=SUMMARY_COLUMNS)
        summary.index.name = 'Data property'
        
        dataset_name = dataframe.index.name
        cell_count = len(dataframe)
        summary['Data set'] = f"{dataset_name} ({cell_count} cells)"
        summary = summary.set_index('Data set', append=True).swaplevel(0, 1)
        
        columns = ['Uoc', 'Isc', 'RserLfDfIEC', 'Rsh', 'FF', 'Eta', 'IRev1']
        
        for col_idx, col_name in enumerate(columns):
            if col_name not in dataframe.columns:
                continue
                
            max_idx = dataframe[col_name].idxmax()
            summary.iloc[0, col_idx] = dataframe.loc[max_idx, col_name]
            summary.iloc[1, col_idx] = dataframe[col_name].median()
            summary.iloc[2, col_idx] = dataframe[col_name].mean()
            
            if col_idx in [0, 1, 4, 5]:
                summary.iloc[3, col_idx] = dataframe[col_name].std()
            else:
                summary.iloc[3, col_idx] = np.nan
                
        summary = summary.apply(pd.to_numeric, errors='coerce')
        
        summary.iloc[:, 2] = summary.iloc[:, 2] * CONVERSION_FACTORS['rser_mohm']
        summary.iloc[:, 3] = summary.iloc[:, 3] * CONVERSION_FACTORS['rsh_kohm']
        
        rounding_keys = ['voc', 'isc', 'rser', 'rsh', 'ff', 'eta', 'irev']
        for col_idx, key in enumerate(rounding_keys):
            decimals = ROUNDING_PRECISION[key]
            summary.iloc[:, col_idx] = np.round(
                summary.iloc[:, col_idx].astype(np.double),
                decimals=decimals
            )
            
        return summary


class CorrelationTableBuilder:
    """相关性表构建器"""
    
    def __init__(self, data_service: DataService):
        self.data_service = data_service
        self.correlations: List[pd.DataFrame] = []
        
    def build(self) -> List[pd.DataFrame]:
        """构建所有相关性表"""
        self.correlations.clear()
        all_data = self.data_service.get_data()
        
        for index in sorted(all_data.keys()):
            corr = self.data_service.get_correlation_matrix(index)
            if corr is not None:
                dataframe = all_data[index]
                dataset_name = dataframe.index.name
                cell_count = len(dataframe)
                
                corr.index.name = 'Data property'
                corr['Data set'] = f"{dataset_name} ({cell_count} cells)"
                corr = corr.set_index('Data set', append=True).swaplevel(0, 1)
                
                self.correlations.append(corr)
                
        logger.info(f"生成了 {len(self.correlations)} 个相关性表")
        return self.correlations


class ReportGenerator:
    """报告生成器类"""
    
    def __init__(self, data_service: DataService):
        self.data_service = data_service
        self.summary_builder = SummaryTableBuilder(data_service)
        self.correlation_builder = CorrelationTableBuilder(data_service)
        self.report_path: str = ""
        
    def set_report_path(self, path: str) -> None:
        """设置报告路径"""
        valid, error_msg = validate_filename(path)
        if not valid:
            raise ReportGenerationError(
                f"文件名包含非ASCII字符: {error_msg}",
                path
            )
        self.report_path = path
        
    def generate_report(
        self,
        yield_loss_data: Optional[List[pd.DataFrame]] = None
    ) -> str:
        """
        生成Excel报告
        
        Args:
            yield_loss_data: 良率损失数据列表
            
        Returns:
            生成的文件路径
        """
        if not self.report_path:
            raise ReportGenerationError("未设置报告路径")
            
        if not self.report_path.endswith('.xlsx'):
            self.report_path += '.xlsx'
            
        summaries = self.summary_builder.build()
        correlations = self.correlation_builder.build()
        
        try:
            with pd.ExcelWriter(self.report_path, engine='xlsxwriter') as writer:
                if summaries:
                    pd.concat(summaries).to_excel(writer, sheet_name='Summary')
                    
                if yield_loss_data:
                    pd.concat(yield_loss_data).to_excel(writer, sheet_name='Yield loss')
                    
                if correlations:
                    pd.concat(correlations).to_excel(writer, sheet_name='Correlation')
                    
            logger.info(f"报告已生成: {self.report_path}")
            return self.report_path
            
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            raise ReportGenerationError(str(e), self.report_path)
            
    def get_report_path(self) -> str:
        """获取报告路径"""
        return self.report_path
