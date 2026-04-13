# -*- coding: utf-8 -*-
"""
异常定义模块 - 自定义异常类
"""


class SCiDAError(Exception):
    """基础异常类"""
    pass


class DataLoadError(SCiDAError):
    """数据加载错误"""
    def __init__(self, message: str = "数据加载失败", filename: str = None):
        self.filename = filename
        super().__init__(message)


class FileFormatError(SCiDAError):
    """文件格式错误"""
    def __init__(self, message: str = "文件格式不支持", filename: str = None):
        self.filename = filename
        super().__init__(message)


class FilterError(SCiDAError):
    """过滤操作错误"""
    def __init__(self, message: str = "过滤操作失败", filter_info: str = None):
        self.filter_info = filter_info
        super().__init__(message)


class ReportGenerationError(SCiDAError):
    """报告生成错误"""
    def __init__(self, message: str = "报告生成失败", report_name: str = None):
        self.report_name = report_name
        super().__init__(message)


class PlotError(SCiDAError):
    """图表绘制错误"""
    def __init__(self, message: str = "图表绘制失败", plot_type: str = None):
        self.plot_type = plot_type
        super().__init__(message)


class DataValidationError(SCiDAError):
    """数据验证错误"""
    def __init__(self, message: str = "数据验证失败", column: str = None):
        self.column = column
        super().__init__(message)
