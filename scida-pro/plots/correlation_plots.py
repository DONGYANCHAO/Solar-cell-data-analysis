# -*- coding: utf-8 -*-
"""
相关性图表模块
"""
import pandas as pd
from typing import Tuple

from plots.base_plot import IVBasePlot
from utils.logger import get_logger

logger = get_logger(__name__)


class CorrelationPlotBase(IVBasePlot):
    """相关性图表基类"""
    
    def __init__(self, parent, x_param: str, y_param: str, 
                 x_label: str, y_label: str, title: str):
        self.x_param = x_param
        self.y_param = y_param
        self.x_label = x_label
        self.y_label = y_label
        self.plot_title = title
        super().__init__(parent)
        
    def get_plot_title(self) -> str:
        return self.plot_title
        
    def configure_axes(self) -> None:
        """配置坐标轴"""
        self.axes.set_xlabel(self.x_label, fontsize=24, weight='black')
        self.axes.set_ylabel(self.y_label, fontsize=24, weight='black')
        self.axes.tick_params(pad=8)
        
    def _draw_plot(self) -> None:
        """绘制散点图"""
        for i in self.plot_selection:
            if i not in self.all_data:
                continue
            dataframe = self.all_data[i]
            if self.x_param not in dataframe.columns or self.y_param not in dataframe.columns:
                continue
                
            self.axes.scatter(
                dataframe[self.x_param],
                dataframe[self.y_param],
                c=self.get_color(i),
                edgecolors='white',
                linewidths=0.3,
                s=self.dotsize_selection,
                label=self.get_dataset_name(i)
            )


class CorrVocIsc(CorrelationPlotBase):
    """Voc-Isc 相关性图"""
    
    def __init__(self, parent):
        super().__init__(
            parent=parent,
            x_param='Uoc',
            y_param='Isc',
            x_label=r'$\mathrm{\mathsf{V_{OC}\ [V]}}$',
            y_label=r'$\mathrm{\mathsf{I_{SC}\ [A]}}$',
            title='Correlation'
        )


class CorrEtaFF(CorrelationPlotBase):
    """Eta-FF 相关性图"""
    
    def __init__(self, parent):
        super().__init__(
            parent=parent,
            x_param='FF',
            y_param='Eta',
            x_label=r'$\mathrm{\mathsf{FF\ [\%]}}$',
            y_label=r'$\mathrm{\mathsf{Eta\ [\%]}}$',
            title='Correlation'
        )


class CorrRshFF(CorrelationPlotBase):
    """Rsh-FF 相关性图"""
    
    def __init__(self, parent):
        super().__init__(
            parent=parent,
            x_param='FF',
            y_param='Rsh',
            x_label=r'$\mathrm{\mathsf{FF\ [\%]}}$',
            y_label=r'$\mathrm{\mathsf{Rsh\ [kOhm]}}$',
            title='Correlation'
        )
        
    def configure_axes(self) -> None:
        """配置坐标轴 - 使用对数刻度"""
        super().configure_axes()
        self.axes.semilogy()
