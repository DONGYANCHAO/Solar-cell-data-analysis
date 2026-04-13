# -*- coding: utf-8 -*-
"""
验证工具模块 - 通用验证函数
"""
import os
from typing import Tuple


def validate_filename(filename: str) -> Tuple[bool, str]:
    """
    验证文件名是否有效
    
    Args:
        filename: 待验证的文件名
        
    Returns:
        (是否有效, 错误信息)
    """
    try:
        filename.encode('ascii')
        return True, ""
    except UnicodeEncodeError:
        return False, "文件名包含非ASCII字符"


def is_number(value: str) -> bool:
    """
    检查字符串是否为数字
    
    Args:
        value: 待检查的字符串
        
    Returns:
        是否为数字
    """
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def remove_whitespace(text: str) -> str:
    """
    移除字符串中的空白字符
    
    Args:
        text: 原始字符串
        
    Returns:
        清理后的字符串
    """
    if text is None:
        return ""
    return text.replace(" ", "").replace("\t", "")


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    清理文件名，保留有效字符
    
    Args:
        filename: 原始文件名
        max_length: 最大长度
        
    Returns:
        清理后的文件名
    """
    keep_characters = (' ', '.', '_', '-')
    valid_filename = "".join(
        c for c in filename if c.isalnum() or c in keep_characters
    ).rstrip()
    return valid_filename[:max_length]


def get_file_extension(filename: str) -> str:
    """
    获取文件扩展名（小写）
    
    Args:
        filename: 文件名
        
    Returns:
        文件扩展名
    """
    return os.path.splitext(filename)[1].lower()


def is_supported_file_format(filename: str) -> bool:
    """
    检查是否为支持的文件格式
    
    Args:
        filename: 文件名
        
    Returns:
        是否支持
    """
    supported_extensions = {'.csv', '.xls', '.xlsx'}
    ext = get_file_extension(filename)
    return ext in supported_extensions
