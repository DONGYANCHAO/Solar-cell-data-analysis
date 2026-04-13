# -*- coding: utf-8 -*-
"""
文件服务模块 - 文件读写业务逻辑
"""
import os
import pickle
import pandas as pd
from pathlib import Path
from typing import Optional, List, Tuple, Dict

from utils.logger import get_logger
from utils.validators import (
    validate_filename,
    is_supported_file_format,
    get_file_extension,
    sanitize_filename,
)
from utils.exceptions import DataLoadError, FileFormatError
from config.constants import LABEL_FORMATS

logger = get_logger(__name__)


class FileService:
    """文件服务类"""
    
    SUPPORTED_EXTENSIONS = {'.csv', '.xls', '.xlsx'}
    FILTER_EXTENSION = '.scda'
    
    def __init__(self):
        self.previous_directory: str = ""
        
    def get_previous_directory(self) -> str:
        """获取上一次使用的目录"""
        return self.previous_directory
        
    def set_previous_directory(self, path: str) -> None:
        """设置上一次使用的目录"""
        self.previous_directory = path
        
    def load_data_file(
        self,
        filepath: str,
        label_format: int
    ) -> Tuple[Optional[pd.DataFrame], List[str]]:
        """
        加载单个数据文件
        
        Args:
            filepath: 文件路径
            label_format: 标签格式索引
            
        Returns:
            (数据框, 列名列表)，失败返回 (None, [])
        """
        valid, error_msg = validate_filename(filepath)
        if not valid:
            logger.error(f"文件名验证失败: {filepath}, 原因: {error_msg}")
            raise DataLoadError(f"文件名包含非ASCII字符: {filepath}", filepath)
            
        if not is_supported_file_format(filepath):
            raise FileFormatError(f"不支持的文件格式: {filepath}", filepath)
            
        self.previous_directory = str(Path(filepath).parent)
        
        ext = get_file_extension(filepath)
        target_columns = LABEL_FORMATS[label_format]
        
        try:
            if ext == '.csv':
                dataframe = self._load_csv(filepath, target_columns)
            else:
                dataframe = self._load_excel(filepath, target_columns)
                
            if dataframe is None:
                raise DataLoadError("无法识别数据标签", filepath)
                
            logger.info(f"文件加载成功: {filepath}, 行数: {len(dataframe)}")
            return dataframe, list(dataframe.columns)
            
        except Exception as e:
            logger.error(f"加载文件失败: {filepath}, 错误: {e}")
            raise DataLoadError(str(e), filepath)
            
    def _load_csv(
        self,
        filepath: str,
        columns: List[str]
    ) -> Optional[pd.DataFrame]:
        """加载CSV文件"""
        try:
            dataframe = pd.read_csv(filepath)[columns].dropna()
            return dataframe
        except KeyError:
            try:
                dataframe = pd.read_csv(filepath, sep=';')[columns].dropna()
                return dataframe
            except KeyError:
                return None
                
    def _load_excel(
        self,
        filepath: str,
        columns: List[str]
    ) -> Optional[pd.DataFrame]:
        """加载Excel文件"""
        try:
            xl_file = pd.read_excel(filepath)
            dataframe = xl_file[columns].dropna()
            return dataframe
        except KeyError:
            return None
            
    def save_data_file(
        self,
        dataframe: pd.DataFrame,
        directory: str,
        filename: str
    ) -> str:
        """
        保存数据文件
        
        Args:
            dataframe: 数据框
            directory: 目标目录
            filename: 文件名
            
        Returns:
            保存的文件路径
        """
        valid_name = sanitize_filename(filename)
        if not valid_name.endswith('.csv'):
            valid_name += '.csv'
            
        filepath = os.path.join(directory, valid_name)
        dataframe.to_csv(filepath, index=False)
        
        logger.info(f"数据已保存: {filepath}")
        return filepath
        
    def check_file_exists(self, directory: str, filename: str) -> str:
        """
        检查文件是否存在，返回完整路径
        
        Args:
            directory: 目录
            filename: 文件名
            
        Returns:
            完整路径
        """
        return os.path.join(directory, filename)
        
    def load_filter_settings(self, filepath: str) -> List[List]:
        """
        加载过滤器设置
        
        Args:
            filepath: 设置文件路径
            
        Returns:
            过滤器设置列表
        """
        valid, error_msg = validate_filename(filepath)
        if not valid:
            raise FileFormatError(f"文件名包含非ASCII字符: {filepath}", filepath)
            
        self.previous_directory = str(Path(filepath).parent)
        
        try:
            with open(filepath, 'rb') as file:
                settings = pickle.load(file)
            logger.info(f"过滤器设置已加载: {filepath}")
            return settings
        except Exception as e:
            logger.error(f"加载过滤器设置失败: {e}")
            raise FileFormatError(str(e), filepath)
            
    def save_filter_settings(self, filepath: str, settings: List[List]) -> None:
        """
        保存过滤器设置
        
        Args:
            filepath: 目标文件路径
            settings: 过滤器设置列表
        """
        valid, error_msg = validate_filename(filepath)
        if not valid:
            raise FileFormatError(f"文件名包含非ASCII字符: {filepath}", filepath)
            
        self.previous_directory = str(Path(filepath).parent)
        
        try:
            with open(filepath, 'wb') as file:
                pickle.dump(settings, file)
            logger.info(f"过滤器设置已保存: {filepath}")
        except Exception as e:
            logger.error(f"保存过滤器设置失败: {e}")
            raise FileFormatError(str(e), filepath)
            
    def load_custom_labels(self, filepath: str) -> List[str]:
        """
        加载自定义标签
        
        Args:
            filepath: 标签文件路径
            
        Returns:
            标签列表
        """
        valid, error_msg = validate_filename(filepath)
        if not valid:
            raise FileFormatError(f"文件名包含非ASCII字符: {filepath}", filepath)
            
        self.previous_directory = str(Path(filepath).parent)
        
        try:
            with open(filepath, 'rb') as file:
                first_line = file.readline().decode('utf-8')
                labels = "".join(first_line.split()).split(",")
            logger.info(f"自定义标签已加载: {labels}")
            return labels
        except Exception as e:
            logger.error(f"加载自定义标签失败: {e}")
            raise FileFormatError(str(e), filepath)
