# -*- coding: utf-8 -*-
from __future__ import division
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from PyQt5 import QtGui, QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import rcParams
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    WindowSize, FontSettings, ColorPalette, PlotSettings, PlotLabels, PlotSelection
)
from PlotSettingsDialog import PlotSettingsDialog

rcParams.update({'figure.autolayout': True})

font = {'family': FontSettings.FAMILY, 'size': FontSettings.PLOT_SIZE}
matplotlib.rc('font', **font)


class IVBasePlot(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(IVBasePlot, self).__init__(parent)
        self.parent_window = parent
        self.all_data = parent.ad if parent else {}
        
        self.plot_selection = list(range(len(self.all_data))) if self.all_data else []
        self.single_dataset = False
        self.title_enabled = False
        self.title_selection = False
        self.grid_enabled = True
        self.grid_selection = True
        self.legend_enabled = True
        self.legend_selection = True
        self.dotsize_enabled = False
        self.dotsize_selection = PlotSettings.DEFAULT_DOT_SIZE
        self.linewidth_enabled = False
        self.linewidth_selection = PlotSettings.DEFAULT_LINE_WIDTH
        self.scatter_enabled = False
        self.scatter_selection = 0.0
        
        self.dpi = 100
        self.fig = None
        self.canvas = None
        self.axes = None
        self.axes2 = None
        
    def setup_window(self, title: str) -> None:
        self.setWindowTitle(self.tr(title))
        self.resize(WindowSize.PLOT_WIDTH, WindowSize.PLOT_HEIGHT)
        frame_geometry = self.frameGeometry()
        center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())
        
    def create_menu(self) -> None:
        self.file_menu = self.menuBar().addMenu(self.tr("File"))
        tip = self.tr("Quit")
        quit_action = QtWidgets.QAction(tip, self)
        quit_action.setIcon(QtGui.QIcon(":quit.png"))
        quit_action.triggered.connect(self.close)
        quit_action.setToolTip(tip)
        quit_action.setStatusTip(tip)
        quit_action.setShortcut('Ctrl+Q')
        self.file_menu.addAction(quit_action)
        
    def create_main_frame(self, two_axes: bool = False) -> None:
        self.main_frame = QtWidgets.QWidget()
        
        self.fig = Figure((10.0, 10.0), dpi=self.dpi, facecolor=ColorPalette.BACKGROUND)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        
        self.axes = self.fig.add_subplot(111, facecolor=ColorPalette.BACKGROUND)
        
        if two_axes:
            self.axes2 = self.axes.twinx()
        
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        
        show_button = QtWidgets.QPushButton()
        show_button.clicked.connect(self.plot_settings_view)
        show_button.setIcon(QtGui.QIcon(":gear.png"))
        show_button.setToolTip(self.tr("Plot settings"))
        show_button.setStatusTip(self.tr("Plot settings"))
        
        buttonbox = QtWidgets.QDialogButtonBox()
        buttonbox.addButton(show_button, QtWidgets.QDialogButtonBox.ActionRole)
        self.mpl_toolbar.addWidget(show_button)
        
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.canvas)
        
        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)
        
        self.status_text = QtWidgets.QLabel("")
        self.statusBar().addWidget(self.status_text, 1)
        
    def plot_settings_view(self) -> None:
        settings_dialog = PlotSettingsDialog(self)
        settings_dialog.setModal(True)
        settings_dialog.show()
        
    def on_draw(self) -> None:
        raise NotImplementedError("Subclasses must implement on_draw()")
    
    def setup_axes_labels(self, xlabel: str, ylabel: str, fontsize: int = FontSettings.AXIS_SIZE) -> None:
        self.axes.set_xlabel(xlabel, fontsize=fontsize, weight='black')
        self.axes.set_ylabel(ylabel, fontsize=fontsize, weight='black')
        self.axes.tick_params(pad=8)
        
    def draw_legend(self, loc: str = PlotSettings.LEGEND_LOC_LOWER_LEFT, 
                    scatter_points: int = PlotSettings.SCATTER_POINTS,
                    marker_scale: int = PlotSettings.MARKER_SCALE) -> None:
        if self.legend_selection:
            self.axes.legend(loc=loc, scatterpoints=scatter_points, 
                           markerscale=marker_scale, frameon=False)
            
    def get_color(self, index: int) -> str:
        return ColorPalette.COLORS[index % len(ColorPalette.COLORS)]
    
    def get_dataset_name(self, index: int) -> str:
        if index in self.all_data:
            return self.all_data[index].index.name
        return f"Dataset {index}"
    
    def apply_grid(self) -> None:
        if self.grid_enabled:
            self.axes.grid(self.grid_selection)
            
    def clear_and_prepare(self) -> None:
        self.axes.clear()
        self.apply_grid()
        
    def get_parameter_series(self, dataset_id: int, parameter: str) -> pd.Series:
        data = self.all_data[dataset_id]
        
        if parameter == 'Voc*Isc':
            return data['Uoc'] * data['Isc']
        elif parameter == 'RserLfDfIEC':
            return data[parameter] * 1000
        elif parameter == 'Rsh':
            return data[parameter] / 1000
        else:
            return data[parameter]
    
    def get_axis_label(self, parameter: str) -> str:
        return PlotLabels.LABEL_MAP.get(parameter, parameter)
