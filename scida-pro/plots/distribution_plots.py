# -*- coding: utf-8 -*-
"""
分布图表模块
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional

from plots.base_plot import IVBasePlot
from config.constants import DOT_SIZE_LARGE, LINE_WIDTH
from utils.logger import get_logger

logger = get_logger(__name__)


class DistLtoH(IVBasePlot):
    """低到高分布图"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
    def get_plot_title(self) -> str:
        return 'Distribution'
        
    def _init_settings(self) -> None:
        """初始化设置"""
        super()._init_settings()
        self.dotsize_selection = DOT_SIZE_LARGE
        
    def configure_axes(self) -> None:
        """配置坐标轴"""
        self.axes.set_xlabel(
            r'$\mathrm{\mathsf{Eta\ [\%]}}$',
            fontsize=24,
            weight='black'
        )
        self.axes.set_ylabel(
            r'$\mathrm{\mathsf{Normalized\ cell\ number\ [a.u.]}}$',
            fontsize=24,
            weight='black'
        )
        self.axes.tick_params(pad=8)
        
    def _draw_plot(self) -> None:
        """绘制分布图"""
        x_min, x_max = 1e4, 0
        y_min = -1
        
        for i in self.plot_selection:
            if i not in self.all_data:
                continue
                
            sorted_eta = pd.DataFrame(np.sort(self.all_data[i]['Eta']))
            
            if sorted_eta.iloc[:, 0].min() <= x_min:
                x_min = sorted_eta.iloc[:, 0].min()
            if sorted_eta.iloc[:, 0].max() >= x_max:
                x_max = sorted_eta.iloc[:, 0].max()
            if np.log10(1 / len(sorted_eta)) < y_min:
                y_min = np.log10(1 / len(sorted_eta))
                
            sorted_eta.index = (sorted_eta.index + 1) / len(sorted_eta)
            
            self.axes.scatter(
                sorted_eta,
                sorted_eta.index,
                c=self.get_color(i),
                edgecolor=self.get_color(i),
                marker=r'$\circ$',
                s=self.dotsize_selection,
                label=self.get_dataset_name(i)
            )
            
        self.axes.set_xlim((np.floor(x_min), np.ceil(x_max)))
        self.axes.semilogy(10 ** np.floor(y_min))
        self.axes.set_ylim((10 ** np.floor(y_min), 2))
        
    def _draw_legend(self) -> None:
        """绘制图例"""
        self.axes.legend(
            loc='upper left',
            scatterpoints=1,
            markerscale=1,
            frameon=False
        )


class DensEta(IVBasePlot):
    """效率密度图"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
    def get_plot_title(self) -> str:
        return 'Density'
        
    def _init_settings(self) -> None:
        """初始化设置"""
        super()._init_settings()
        self.dotsize_enabled = False
        self.linewidth_enabled = True
        self.linewidth_selection = LINE_WIDTH
        
    def configure_axes(self) -> None:
        """配置坐标轴"""
        self.axes.set_xlabel(
            r'$\mathrm{\mathsf{Eta\ [\%]}}$',
            fontsize=24,
            weight='black'
        )
        self.axes.set_ylabel(
            r'$\mathrm{\mathsf{Density\ [a.u.]}}$',
            fontsize=24,
            weight='black'
        )
        self.axes.tick_params(pad=8)
        
    def _draw_plot(self) -> None:
        """绘制密度图"""
        x_min, x_max = 1e4, 0
        
        for i in self.plot_selection:
            if i not in self.all_data:
                continue
                
            eta_data = self.all_data[i]['Eta']
            
            if eta_data.min() <= x_min:
                x_min = eta_data.min()
            if eta_data.max() >= x_max:
                x_max = eta_data.max()
                
            eta_data.plot(
                kind='kde',
                c=self.get_color(i),
                lw=self.linewidth_selection,
                label=self.get_dataset_name(i),
                ax=self.axes
            )
            
        self.axes.set_xlim((np.floor(x_min), np.ceil(x_max)))
        
    def _draw_legend(self) -> None:
        """绘制图例"""
        self.axes.legend(
            loc='upper left',
            scatterpoints=1,
            markerscale=1,
            frameon=False
        )


class DistWT(IVBasePlot):
    """Walk-through 分布图"""
    
    def __init__(self, parent, param_one_combo: str):
        super().__init__(parent, param_one_combo)
        
    def get_plot_title(self) -> str:
        return 'Walkthrough'
        
    def configure_axes(self) -> None:
        """配置坐标轴"""
        self.axes.set_xlabel(
            r'$\mathrm{\mathsf{Normalized\ cell\ number\ [a.u.]}}$',
            fontsize=24,
            weight='black'
        )
        
        if self.param_one_combo:
            self.axes.set_ylabel(
                self.get_axis_label(self.param_one_combo),
                fontsize=24,
                weight='black'
            )
            
        self.axes.tick_params(pad=8)
        
    def _draw_plot(self) -> None:
        """绘制 walk-through 图"""
        for i in self.plot_selection:
            if i not in self.all_data:
                continue
                
            param_values = self.get_parameter_value(
                self.all_data[i],
                self.param_one_combo
            )
            
            se = pd.DataFrame(param_values)
            se.index = (se.index + 1) / len(se)
            
            self.axes.scatter(
                se.index,
                se,
                c=self.get_color(i),
                edgecolors='white',
                linewidths=0.3,
                s=self.dotsize_selection,
                label=self.get_dataset_name(i)
            )
            
        self.axes.set_xlim((0, 1))
        
    def _draw_legend(self) -> None:
        """绘制图例"""
        self.axes.legend(
            loc='lower left',
            scatterpoints=1,
            markerscale=3,
            frameon=True
        )


class DistRM(IVBasePlot):
    """滚动均值分布图"""
    
    def __init__(self, parent, param_one_combo: str):
        super().__init__(parent, param_one_combo)
        
    def get_plot_title(self) -> str:
        return 'Rolling mean'
        
    def _init_settings(self) -> None:
        """初始化设置"""
        super()._init_settings()
        self.dotsize_enabled = False
        self.linewidth_enabled = True
        self.linewidth_selection = LINE_WIDTH
        
    def configure_axes(self) -> None:
        """配置坐标轴"""
        self.axes.set_xlabel(
            r'$\mathrm{\mathsf{Normalized\ cell\ number\ [a.u.]}}$',
            fontsize=24,
            weight='black'
        )
        
        if self.param_one_combo:
            self.axes.set_ylabel(
                self.get_axis_label(self.param_one_combo),
                fontsize=24,
                weight='black'
            )
            
        self.axes.tick_params(pad=8)
        
    def _draw_plot(self) -> None:
        """绘制滚动均值图"""
        for i in self.plot_selection:
            if i not in self.all_data:
                continue
                
            param_values = self.get_parameter_value(
                self.all_data[i],
                self.param_one_combo
            )
            
            se = pd.DataFrame(param_values)
            se.index = (se.index + 1) / len(se)
            
            window_size = int(np.floor(len(se) * 0.1)) if len(se) > 100 else 1
            rolling_mean = se.rolling(center=True, window=window_size).mean()
            
            self.axes.plot(
                rolling_mean.index,
                rolling_mean,
                c=self.get_color(i),
                lw=self.linewidth_selection,
                label=self.get_dataset_name(i)
            )
            
    def _draw_legend(self) -> None:
        """绘制图例"""
        self.axes.legend(
            loc='lower left',
            scatterpoints=1,
            markerscale=3,
            frameon=True
        )
