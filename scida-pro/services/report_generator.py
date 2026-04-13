# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SummaryConfig, Messages
from logger import get_logger, ReportGenerationError


class ReportBuilder:
    def __init__(self):
        self.summary_tables: List[pd.DataFrame] = []
        self.yield_loss_tables: List[pd.DataFrame] = []
        self.correlation_tables: List[pd.DataFrame] = []
        self.datasets: Dict[int, pd.DataFrame] = {}
        
    def set_datasets(self, datasets: Dict[int, pd.DataFrame]) -> 'ReportBuilder':
        self.datasets = datasets
        return self
    
    def build_summary_tables(self) -> 'ReportBuilder':
        self.summary_tables = []
        
        for dataset_id in sorted(self.datasets.keys()):
            dataframe = self.datasets[dataset_id]
            summary = self._create_summary_table(dataframe)
            self.summary_tables.append(summary)
        
        return self
    
    def build_yield_loss_tables(self, yield_loss_tables: List[pd.DataFrame]) -> 'ReportBuilder':
        self.yield_loss_tables = []
        
        for idx, yield_loss_df in enumerate(yield_loss_tables):
            processed = self._process_yield_loss_table(yield_loss_df, idx)
            self.yield_loss_tables.append(processed)
        
        return self
    
    def build_correlation_tables(self) -> 'ReportBuilder':
        self.correlation_tables = []
        
        for dataset_id in sorted(self.datasets.keys()):
            dataframe = self.datasets[dataset_id]
            correlation = self._create_correlation_table(dataframe)
            if correlation is not None:
                self.correlation_tables.append(correlation)
        
        return self
    
    def export_to_excel(self, file_path: str, translator=None) -> bool:
        try:
            writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
            
            if self.summary_tables:
                output_summary = pd.concat(self.summary_tables)
                sheet_name = 'Summary'
                if translator:
                    sheet_name = str(translator('Summary'))
                output_summary.to_excel(writer, sheet_name)
            
            if self.yield_loss_tables:
                output_yield = pd.concat(self.yield_loss_tables)
                sheet_name = 'Yield loss'
                if translator:
                    sheet_name = str(translator('Yield loss'))
                output_yield.to_excel(writer, sheet_name)
            
            if self.correlation_tables:
                output_corr = pd.concat(self.correlation_tables)
                sheet_name = 'Correlation'
                if translator:
                    sheet_name = str(translator('Correlation'))
                output_corr.to_excel(writer, sheet_name)
            
            writer.close()
            return True
            
        except Exception as e:
            raise ReportGenerationError(f"Failed to export report: {str(e)}")
    
    def _create_summary_table(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        summary = pd.DataFrame(
            index=SummaryConfig.INDEX_NAMES, 
            columns=SummaryConfig.COLUMN_NAMES
        )
        summary.index.name = 'Data property'
        summary['Data set'] = f"{dataframe.index.name} ({len(dataframe)} cells)"
        summary = summary.set_index('Data set', append=True).swaplevel(0, 1)
        
        max_values = dataframe.max()
        for col_idx, value in enumerate(max_values):
            if col_idx == 5:
                best_idx = dataframe['Eta'].idxmax()
                summary.iloc[0, col_idx] = dataframe.iloc[best_idx, col_idx]
            else:
                summary.iloc[0, col_idx] = value
        
        summary.iloc[1, :] = dataframe.median()
        summary.iloc[2, :] = dataframe.mean()
        
        for col_idx in range(len(dataframe.columns)):
            if col_idx in SummaryConfig.STD_DEV_PARAMS:
                summary.iloc[3, col_idx] = dataframe.std().iloc[col_idx]
            else:
                summary.iloc[3, col_idx] = np.nan
        
        summary = summary.apply(pd.to_numeric, errors='coerce')
        
        summary.iloc[:, 2] = summary.iloc[:, 2] * 1000
        summary.iloc[:, 3] = summary.iloc[:, 3] / 1000
        
        for col_idx, decimals in enumerate(SummaryConfig.ROUNDING_DECIMALS):
            summary.iloc[:, col_idx] = np.round(
                summary.iloc[:, col_idx].astype(np.double), 
                decimals=decimals
            )
        
        return summary
    
    def _create_correlation_table(self, dataframe: pd.DataFrame) -> Optional[pd.DataFrame]:
        if len(dataframe) <= 1:
            return None
        
        correlation = np.round(dataframe.corr(), decimals=2)
        correlation.iloc[:, 2:4] = np.nan
        correlation.iloc[2:4, :] = np.nan
        correlation.iloc[6, :] = np.nan
        correlation.iloc[:, 6] = np.nan
        correlation = correlation.dropna(0, 'all').T.dropna(0, 'all')
        
        correlation.index.name = 'Data property'
        correlation['Data set'] = f"{dataframe.index.name} ({len(dataframe)} cells)"
        correlation = correlation.set_index('Data set', append=True).swaplevel(0, 1)
        
        return correlation
    
    def _process_yield_loss_table(
        self, 
        yield_loss_df: pd.DataFrame, 
        idx: int
    ) -> pd.DataFrame:
        yield_loss_df = yield_loss_df.copy()
        
        yield_loss_df['Total'] = np.nan
        yield_loss_df.iloc[1, SummaryConfig.ROUNDING_DECIMALS.__len__()] = yield_loss_df.iloc[1, :].sum()
        
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
        
        sorted_keys = sorted(self.datasets.keys())
        if idx < len(sorted_keys):
            dataset = self.datasets[sorted_keys[idx]]
            yield_loss_df['Data set'] = f"{dataset.index.name} ({original_count} cells)"
            yield_loss_df = yield_loss_df.set_index('Data set', append=True).swaplevel(0, 1)
        
        return yield_loss_df
    
    def get_summary_tables(self) -> List[pd.DataFrame]:
        return self.summary_tables
    
    def get_yield_loss_tables(self) -> List[pd.DataFrame]:
        return self.yield_loss_tables
    
    def get_correlation_tables(self) -> List[pd.DataFrame]:
        return self.correlation_tables


class ReportGenerator:
    def __init__(self):
        self.logger = get_logger('ReportGenerator')
        
    def generate_report(
        self, 
        file_path: str, 
        datasets: Dict[int, pd.DataFrame],
        yield_loss_tables: List[pd.DataFrame] = None,
        translator=None
    ) -> bool:
        if not datasets:
            return False
        
        try:
            builder = ReportBuilder()
            builder.set_datasets(datasets)
            builder.build_summary_tables()
            
            if yield_loss_tables:
                builder.build_yield_loss_tables(yield_loss_tables)
            
            builder.build_correlation_tables()
            
            return builder.export_to_excel(file_path, translator)
            
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}")
            raise ReportGenerationError(f"Failed to generate report: {str(e)}")
    
    def create_builder(self) -> ReportBuilder:
        return ReportBuilder()
