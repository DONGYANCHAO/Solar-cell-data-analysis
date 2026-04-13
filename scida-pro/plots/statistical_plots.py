# -*- coding: utf-8 -*-
"""
统计图表模块 - 箱线图、小提琴图、分类散点图
"""
import numpy as np
import pandas as pd

from plots.base_plot import IVBasePlot
from utils.logger import get_logger

logger = get_logger(__name__)


class IVBoxPlot(IVBasePlot):
    """箱线图"""
    
    def __init__(self, parent, param_one_combo: str):
        super().__init__(parent, param_one_combo)
        
    def get_plot_title(self) -> str:
        return 'Boxplot'
        
    def _init_settings(self) -> None:
        """初始化设置"""
        super()._init_settings()
        self.grid_enabled = False
        self.legend_enabled = False
        self.dotsize_enabled = False
        self.linewidth_enabled = False
        self.scatter_enabled = True
        self.scatter_selection = 0.0
        
    def configure_axes(self) -> None:
        """配置坐标轴"""
        self.axes.set_ylabel(
            self.get_axis_label(self.param_one_combo),
            fontsize=24,
            weight='black'
        )
        self.axes.tick_params(pad=8)
        
    def _draw_plot(self) -> None:
        """绘制箱线图"""
        data_to_plot = []
        labels = []
        
        for i in self.plot_selection:
            if i not in self.all_data:
                continue
                
            param_values = self.get_parameter_value(
                self.all_data[i],
                self.param_one_combo
            )
            
            data_to_plot.append(param_values.dropna().values)
            labels.append(self.get_dataset_name(i))
            
        if data_to_plot:
            box_plot = self.axes.boxplot(
                data_to_plot,
                labels=labels,
                patch_artist=True
            )
            
            for patch, color_idx in zip(
                box_plot['boxes'],
                range(len(box_plot['boxes']))
            ):
                patch.set_facecolor(self.get_color(color_idx))
                
    def _apply_common_settings(self) -> None:
        """应用通用设置 - 箱线图特殊处理"""
        pass


class ViolinPlot(IVBasePlot):
    """小提琴图"""
    
    def __init__(self, parent, param_one_combo: str):
        super().__init__(parent, param_one_combo)
        
    def get_plot_title(self) -> str:
        return 'Violinplot'
        
    def _init_settings(self) -> None:
        """初始化设置"""
        super()._init_settings()
        self.grid_enabled = False
        self.legend_enabled = False
        self.dotsize_enabled = False
        self.linewidth_enabled = True
        self.linewidth_selection = 2
        self.scatter_enabled = True
        self.scatter_selection = 0.05
        
    def configure_axes(self) -> None:
        """配置坐标轴"""
        self.axes.set_ylabel(
            self.get_axis_label(self.param_one_combo),
            fontsize=24,
            weight='black'
        )
        self.axes.tick_params(pad=8)
        
    def _draw_plot(self) -> None:
        """绘制小提琴图"""
        data_to_plot = []
        labels = []
        positions = []
        
        for idx, i in enumerate(self.plot_selection):
            if i not in self.all_data:
                continue
                
            param_values = self.get_parameter_value(
                self.all_data[i],
                self.param_one_combo
            )
            
            data_to_plot.append(param_values.dropna().values)
            labels.append(self.get_dataset_name(i))
            positions.append(idx + 1)
            
        if data_to_plot:
            parts = self.axes.violinplot(
                data_to_plot,
                positions=positions,
                showmeans=False,
                showmedians=False,
                showextrema=False
            )
            
            for idx, pc in enumerate(parts['bodies']):
                pc.set_facecolor(self.get_color(idx))
                pc.set_edgecolor('black')
                pc.set_alpha(0.7)
                
            for idx, data in enumerate(data_to_plot):
                jitter = np.random.normal(idx + 1, self.scatter_selection, size=len(data))
                self.axes.scatter(
                    jitter,
                    data,
                    c=self.get_color(idx),
                    edgecolors='white',
                    linewidths=0.3,
                    s=5,
                    alpha=0.5
                )
                
            self.axes.set_xticks(positions)
            self.axes.set_xticklabels(labels, rotation=45, ha='right')
            
    def _apply_common_settings(self) -> None:
        """应用通用设置 - 小提琴图特殊处理"""
        pass


class CategoryScatter(IVBasePlot):
    """分类散点图"""
    
    def __init__(self, parent, param_one_combo: str):
        super().__init__(parent, param_one_combo)
        
    def get_plot_title(self) -> str:
        return 'Category scatter'
        
    def _init_settings(self) -> None:
        """初始化设置"""
        super()._init_settings()
        self.grid_enabled = False
        self.legend_enabled = True
        self.dotsize_enabled = True
        self.scatter_enabled = True
        self.scatter_selection = 0.05
        
    def configure_axes(self) -> None:
        """配置坐标轴"""
        self.axes.set_ylabel(
            self.get_axis_label(self.param_one_combo),
            fontsize=24,
            weight='black'
        )
        self.axes.tick_params(pad=8)
        
    def _draw_plot(self) -> None:
        """绘制分类散点图"""
        for idx, i in enumerate(self.plot_selection):
            if i not in self.all_data:
                continue
                
            param_values = self.get_parameter_value(
                self.all_data[i],
                self.param_one_combo
            )
            
            data = param_values.dropna().values
            jitter = np.random.normal(idx + 1, self.scatter_selection, size=len(data))
            
            self.axes.scatter(
                jitter,
                data,
                c=self.get_color(idx),
                edgecolors='white',
                linewidths=0.3,
                s=self.dotsize_selection,
                label=self.get_dataset_name(i)
            )
            
        self.axes.set_xticks(range(1, len(self.plot_selection) + 1))
        self.axes.set_xticklabels([
            self.get_dataset_name(i) for i in self.plot_selection
        ], rotation=45, ha='right')
        
    def _apply_common_settings(self) -> None:
        """应用通用设置"""
        if self.legend_enabled and self.legend_selection:
            self.axes.legend(
                loc='best',
                scatterpoints=1,
                markerscale=1,
                frameon=False
            )
