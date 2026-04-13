# -*- coding: utf-8 -*-
"""
直方图模块
"""
import numpy as np
import pandas as pd

from plots.base_plot import IVBasePlot
from config.constants import LINE_WIDTH
from utils.logger import get_logger

logger = get_logger(__name__)


class IVHistPlot(IVBasePlot):
    """直方图"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
    def get_plot_title(self) -> str:
        return 'Histogram'
        
    def _init_settings(self) -> None:
        """初始化设置"""
        super()._init_settings()
        self.grid_enabled = False
        self.legend_enabled = True
        self.dotsize_enabled = False
        self.linewidth_enabled = True
        self.linewidth_selection = LINE_WIDTH
        self.single_dataset = True
        
    def configure_axes(self) -> None:
        """配置坐标轴"""
        self.axes.set_xlabel(
            r'$\mathrm{\mathsf{Eta\ [\%]}}$',
            fontsize=24,
            weight='black'
        )
        self.axes.set_ylabel(
            r'$\mathrm{\mathsf{Count}}$',
            fontsize=24,
            weight='black'
        )
        self.axes.tick_params(pad=8)
        
    def _draw_plot(self) -> None:
        """绘制直方图"""
        for i in self.plot_selection:
            if i not in self.all_data:
                continue
                
            eta_data = self.all_data[i]['Eta'].dropna()
            
            self.axes.hist(
                eta_data,
                bins=20,
                alpha=0.7,
                color=self.get_color(i),
                edgecolor='white',
                linewidth=self.linewidth_selection,
                label=self.get_dataset_name(i)
            )
            
    def _draw_legend(self) -> None:
        """绘制图例"""
        self.axes.legend(
            loc='upper right',
            frameon=False
        )


class IVHistDenPlot(IVBasePlot):
    """直方图+密度图"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
    def get_plot_title(self) -> str:
        return 'Histogram + Density'
        
    def _init_settings(self) -> None:
        """初始化设置"""
        super()._init_settings()
        self.grid_enabled = False
        self.legend_enabled = True
        self.dotsize_enabled = False
        self.linewidth_enabled = True
        self.linewidth_selection = LINE_WIDTH
        self.single_dataset = True
        
    def configure_axes(self) -> None:
        """配置坐标轴"""
        self.axes.set_xlabel(
            r'$\mathrm{\mathsf{Eta\ [\%]}}$',
            fontsize=24,
            weight='black'
        )
        self.axes.set_ylabel(
            r'$\mathrm{\mathsf{Count}}$',
            fontsize=24,
            weight='black'
        )
        self.axes.tick_params(pad=8)
        
    def _create_main_frame(self, two_axes: bool = False) -> None:
        """创建主框架 - 使用双Y轴"""
        super()._create_main_frame(two_axes=True)
        
    def _draw_plot(self) -> None:
        """绘制直方图+密度图"""
        for i in self.plot_selection:
            if i not in self.all_data:
                continue
                
            eta_data = self.all_data[i]['Eta'].dropna()
            
            n, bins, patches = self.axes.hist(
                eta_data,
                bins=20,
                alpha=0.5,
                color=self.get_color(i),
                edgecolor='white',
                label=self.get_dataset_name(i)
            )
            
            eta_data.plot(
                kind='kde',
                c=self.get_color(i),
                lw=self.linewidth_selection,
                ax=self.axes2,
                secondary_y=True
            )
            
        self.axes2.set_ylabel(
            r'$\mathrm{\mathsf{Density}}$',
            fontsize=24,
            weight='black'
        )
        
    def _draw_legend(self) -> None:
        """绘制图例"""
        lines1, labels1 = self.axes.get_legend_handles_labels()
        lines2, labels2 = self.axes2.get_legend_handles_labels()
        self.axes.legend(
            lines1 + lines2,
            labels1 + labels2,
            loc='upper right',
            frameon=False
        )
