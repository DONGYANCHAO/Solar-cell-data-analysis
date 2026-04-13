# -*- coding: utf-8 -*-
"""
图表基类模块 - 模板方法模式
"""
from typing import List, Dict, Optional, Any
import numpy as np
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import rcParams

from PyQt5 import QtGui, QtWidgets

from config.constants import (
    ColorPalette,
    PLOT_WINDOW_SIZE,
    FONT_SIZE,
    DOT_SIZE,
    LINE_WIDTH,
)
from utils.logger import get_logger

rcParams.update({'figure.autolayout': True})

font = {'family': 'sans-serif', 'size': FONT_SIZE}
matplotlib.rc('font', **font)

logger = get_logger(__name__)


class IVBasePlot(QtWidgets.QMainWindow):
    """
    图表基类 - 使用模板方法模式
    
    子类只需实现:
    - get_plot_title(): 返回图表标题
    - configure_axes(): 配置坐标轴
    - draw_plot(): 绘制图表内容
    """
    
    def __init__(self, parent=None, param_one_combo: Optional[str] = None):
        super().__init__(parent)
        
        self.parent_window = parent
        self.param_one_combo = param_one_combo
        self.all_data: Dict[int, pd.DataFrame] = parent.ad if parent else {}
        
        self.plot_selection: List[int] = []
        self._init_plot_selection()
        
        self.color_list = ColorPalette.PRIMARY_COLORS.value + [
            ColorPalette.DEFAULT_COLOR.value,
            ColorPalette.SECONDARY_COLOR.value
        ]
        
        self._init_settings()
        self._setup_window()
        self._create_menu()
        self._create_main_frame()
        self.on_draw()
        
    def _init_plot_selection(self) -> None:
        """初始化绘图选择"""
        self.plot_selection = list(range(len(self.all_data)))
        
    def _init_settings(self) -> None:
        """初始化绘图设置 - 子类可覆盖"""
        self.single_dataset = False
        self.title_enabled = False
        self.title_selection = False
        self.grid_enabled = True
        self.grid_selection = True
        self.legend_enabled = True
        self.legend_selection = True
        self.dotsize_enabled = True
        self.dotsize_selection = DOT_SIZE
        self.linewidth_enabled = False
        self.linewidth_selection = LINE_WIDTH
        self.scatter_enabled = False
        self.scatter_selection = 0.0
        
    def _setup_window(self) -> None:
        """设置窗口属性"""
        self.setWindowTitle(self.tr(self.get_plot_title()))
        self.resize(*PLOT_WINDOW_SIZE)
        
        frame_geometry = self.frameGeometry()
        center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())
        
    def get_plot_title(self) -> str:
        """返回图表标题 - 子类必须实现"""
        raise NotImplementedError("子类必须实现 get_plot_title 方法")
        
    def _create_main_frame(self, two_axes: bool = False) -> None:
        """创建主框架"""
        self.main_frame = QtWidgets.QWidget()
        
        self.dpi = 100
        self.fig = Figure((10.0, 10.0), dpi=self.dpi, facecolor='White')
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        
        self.axes = self.fig.add_subplot(111, facecolor='White')
        
        if two_axes:
            self.axes2 = self.axes.twinx()
            
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        
        settings_button = QtWidgets.QPushButton()
        settings_button.clicked.connect(self.plot_settings_view)
        settings_button.setIcon(QtGui.QIcon(":gear.png"))
        settings_button.setToolTip(self.tr("Plot settings"))
        settings_button.setStatusTip(self.tr("Plot settings"))
        
        button_box = QtWidgets.QDialogButtonBox()
        button_box.addButton(settings_button, QtWidgets.QDialogButtonBox.ActionRole)
        
        self.mpl_toolbar.addWidget(settings_button)
        
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.canvas)
        
        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)
        
        self.status_text = QtWidgets.QLabel("")
        self.statusBar().addWidget(self.status_text, 1)
        
    def _create_menu(self) -> None:
        """创建菜单"""
        self.file_menu = self.menuBar().addMenu(self.tr("File"))
        
        quit_action = QtWidgets.QAction(self.tr("Quit"), self)
        quit_action.setIcon(QtGui.QIcon(":quit.png"))
        quit_action.triggered.connect(self.close)
        quit_action.setToolTip(self.tr("Quit"))
        quit_action.setStatusTip(self.tr("Quit"))
        quit_action.setShortcut('Ctrl+Q')
        
        self.file_menu.addAction(quit_action)
        
    def on_draw(self) -> None:
        """绘制图表 - 模板方法"""
        self.axes.clear()
        self._configure_axes()
        self._draw_plot()
        self._apply_common_settings()
        self.canvas.draw()
        
    def _configure_axes(self) -> None:
        """配置坐标轴 - 子类可覆盖或实现 get_xlabel/get_ylabel"""
        self.configure_axes()
        
    def configure_axes(self) -> None:
        """配置坐标轴 - 子类必须实现"""
        raise NotImplementedError("子类必须实现 configure_axes 方法")
        
    def _draw_plot(self) -> None:
        """绘制图表内容 - 子类必须实现"""
        raise NotImplementedError("子类必须实现 _draw_plot 方法")
        
    def _apply_common_settings(self) -> None:
        """应用通用设置"""
        if self.grid_enabled:
            self.axes.grid(self.grid_selection)
            
        if self.legend_enabled and self.legend_selection:
            self._draw_legend()
            
    def _draw_legend(self) -> None:
        """绘制图例 - 子类可覆盖"""
        self.axes.legend(
            loc='lower left',
            scatterpoints=1,
            markerscale=3,
            frameon=False
        )
        
    def get_color(self, index: int) -> str:
        """获取颜色"""
        return self.color_list[index % len(self.color_list)]
        
    def get_dataset_name(self, index: int) -> str:
        """获取数据集名称"""
        if index in self.all_data:
            return self.all_data[index].index.name
        return f"Dataset {index}"
        
    def get_parameter_value(self, dataframe: pd.DataFrame, param: str) -> pd.Series:
        """
        获取参数值，处理特殊参数
        
        Args:
            dataframe: 数据框
            param: 参数名
            
        Returns:
            参数值序列
        """
        if param == 'Voc*Isc':
            return dataframe['Uoc'] * dataframe['Isc']
        elif param == 'RserLfDfIEC':
            return 1000 * dataframe[param]
        elif param == 'Rsh':
            return 0.001 * dataframe[param]
        else:
            return dataframe[param]
            
    def get_axis_label(self, param: str) -> str:
        """
        获取坐标轴标签
        
        Args:
            param: 参数名
            
        Returns:
            坐标轴标签
        """
        label_map = {
            'Uoc': r'$\mathrm{\mathsf{V_{OC}\ [V]}}$',
            'Isc': r'$\mathrm{\mathsf{I_{SC}\ [A]}}$',
            'Voc*Isc': r'$\mathrm{\mathsf{V_{OC}\ *\ I_{SC}\ [V*A]}}$',
            'FF': r'$\mathrm{\mathsf{FF\ [\%]}}$',
            'Eta': r'$\mathrm{\mathsf{Eta\ [\%]}}$',
            'RserLfDfIEC': r'$\mathrm{\mathsf{R_{SERIES}\ [mOhm \cdot cm^{2}]}}$',
            'Rsh': r'$\mathrm{\mathsf{R_{SHUNT}\ [kOhm]}}$',
            'IRev1': r'$\mathrm{\mathsf{I_{REV}\ [A]}}$',
        }
        return label_map.get(param, param)
        
    def plot_settings_view(self) -> None:
        """打开绘图设置对话框"""
        from PlotSettingsDialog import PlotSettingsDialog
        settings_dialog = PlotSettingsDialog(self)
        settings_dialog.setModal(True)
        settings_dialog.show()
