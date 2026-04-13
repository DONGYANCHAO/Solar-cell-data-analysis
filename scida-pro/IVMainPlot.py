# -*- coding: utf-8 -*-
from __future__ import division
from abc import ABCMeta, abstractmethod
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import sip
from PyQt5 import QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import rcParams

from PlotSettingsDialog import PlotSettingsDialog
from config import (
    PlotColors, PlotAxisLabels, MatplotlibStyle, WindowConfig,
    PlotParameters, Converters
)
from logger_config import setup_logger

rcParams.update({'figure.autolayout': True})
font = {'family': MatplotlibStyle.FONT_FAMILY, 'size': MatplotlibStyle.FONT_SIZE}
matplotlib.rc('font', **font)
logger = setup_logger(__name__)


class QtABCMeta(sip.wrappertype, ABCMeta):
    pass


class IVBasePlot(QtWidgets.QMainWindow, metaclass=QtABCMeta):
    def __init__(self, parent, title: str) -> None:
        QtWidgets.QMainWindow.__init__(self, parent)
        self.parent = parent
        self.data = parent.ad
        self.plot_selection = list(range(len(self.data)))
        self.has_two_axes = False

        self._setup_window(title)
        self._setup_default_settings()
        self._setup_parameter(None)
        self._init_ui()
        self.on_draw()

    def _setup_window(self, title: str) -> None:
        self.setWindowTitle(self.tr(title))
        self.resize(WindowConfig.PLOT_WIDTH, WindowConfig.PLOT_HEIGHT)
        frame_geometry = self.frameGeometry()
        center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def _setup_default_settings(self) -> None:
        self.single_dataset = False
        self.title_enabled = False
        self.title_selection = False
        self.grid_enabled = True
        self.grid_selection = True
        self.legend_enabled = True
        self.legend_selection = True
        self.dotsize_enabled = True
        self.dotsize_selection = 20
        self.linewidth_enabled = False
        self.linewidth_selection = 3
        self.scatter_enabled = False
        self.scatter_selection = 0.5
        self.legend_location = 'lower left'

    def _setup_parameter(self, param: str) -> None:
        if param and param in PlotParameters.SELECTION_LIST:
            self.parameter = param

    def _init_ui(self) -> None:
        self.create_menu()
        self.create_main_frame()

    def create_main_frame(self) -> None:
        self.main_frame = QtWidgets.QWidget()
        self.fig = Figure(
            MatplotlibStyle.FIGURE_SIZE,
            dpi=MatplotlibStyle.DPI,
            facecolor=MatplotlibStyle.FACECOLOR
        )
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        self.axes = self.fig.add_subplot(111, facecolor=MatplotlibStyle.FACECOLOR)

        if self.has_two_axes:
            self.axes2 = self.axes.twinx()

        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        self._add_settings_button()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.canvas)
        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)

        self.status_text = QtWidgets.QLabel("")
        self.statusBar().addWidget(self.status_text, 1)

    def _add_settings_button(self) -> None:
        show_button = QtWidgets.QPushButton()
        show_button.clicked.connect(self.plot_settings_view)
        show_button.setIcon(QtGui.QIcon(":gear.png"))
        show_button.setToolTip(self.tr("Plot settings"))
        show_button.setStatusTip(self.tr("Plot settings"))
        self.mpl_toolbar.addWidget(show_button)

    def create_menu(self) -> None:
        self.file_menu = self.menuBar().addMenu(self.tr("File"))
        quit_action = QtWidgets.QAction(self.tr("Quit"), self)
        quit_action.setIcon(QtGui.QIcon(":quit.png"))
        quit_action.triggered.connect(self.close)
        quit_action.setShortcut('Ctrl+Q')
        self.file_menu.addAction(quit_action)

    def plot_settings_view(self) -> None:
        settings_dialog = PlotSettingsDialog(self)
        settings_dialog.setModal(True)
        settings_dialog.show()

    def _get_color(self, index: int) -> str:
        return PlotColors.PALETTE[index % len(PlotColors.PALETTE)]

    def _setup_axis_labels(self, x_label: str, y_label: str) -> None:
        self.axes.set_xlabel(x_label, fontsize=24, weight='black')
        self.axes.set_ylabel(y_label, fontsize=24, weight='black')
        self.axes.tick_params(pad=8)

    def _add_legend_if_enabled(self) -> None:
        if self.legend_selection:
            self.axes.legend(
                loc=self.legend_location,
                scatterpoints=1,
                markerscale=3,
                frameon=False
            )

    @abstractmethod
    def on_draw(self) -> None:
        pass


class CorrelationPlotBase(IVBasePlot):
    def __init__(self, parent, x_param: str, y_param: str) -> None:
        self.x_param = x_param
        self.y_param = y_param
        self.log_y = False
        super().__init__(parent, "Correlation")

    def on_draw(self) -> None:
        self.axes.clear()
        self.axes.grid(self.grid_selection)
        self._setup_axis_labels(
            self._get_axis_label(self.x_param),
            self._get_axis_label(self.y_param)
        )
        if self.log_y:
            self.axes.semilogy()

        for i in self.plot_selection:
            self.axes.scatter(
                self.data[i][self.x_param],
                self.data[i][self.y_param],
                c=self._get_color(i),
                edgecolors='white',
                linewidths=0.3,
                s=self.dotsize_selection,
                label=self.data[i].index.name
            )

        self._add_legend_if_enabled()
        self.canvas.draw()

    @staticmethod
    def _get_axis_label(param: str) -> str:
        labels = {
            'Uoc': PlotAxisLabels.VOC,
            'Isc': PlotAxisLabels.ISC,
            'FF': PlotAxisLabels.FF,
            'Eta': PlotAxisLabels.ETA,
            'Rsh': PlotAxisLabels.RSHUNT,
        }
        return labels.get(param, '')


class CorrVocIsc(CorrelationPlotBase):
    def __init__(self, parent) -> None:
        super().__init__(parent, 'Uoc', 'Isc')


class CorrEtaFF(CorrelationPlotBase):
    def __init__(self, parent) -> None:
        super().__init__(parent, 'FF', 'Eta')


class CorrRshFF(CorrelationPlotBase):
    def __init__(self, parent) -> None:
        super().__init__(parent, 'FF', 'Rsh')
        self.log_y = True
        self.legend_location = 'lower left'


class DistLtoH(IVBasePlot):
    def __init__(self, parent) -> None:
        super().__init__(parent, "Distribution")
        self.dotsize_selection = 200

    def on_draw(self) -> None:
        self.axes.clear()
        self.axes.grid(self.grid_selection)
        self._setup_axis_labels(
            PlotAxisLabels.ETA,
            r'$\mathrm{\mathsf{Normalized\ cell\ number\ [a.u.]}}$'
        )

        x_min, x_max, y_min = 1e4, 0, -1
        for i in self.plot_selection:
            sorted_eta = pd.DataFrame(np.sort(self.data[i]['Eta']))
            x_min = min(x_min, sorted_eta.iloc[:, 0].min())
            x_max = max(x_max, sorted_eta.iloc[:, 0].max())
            y_min = min(y_min, np.log10(1 / len(sorted_eta)))
            sorted_eta.index = (sorted_eta.index + 1) / len(sorted_eta)
            self.axes.scatter(
                sorted_eta,
                sorted_eta.index,
                c=self._get_color(i),
                edgecolor=self._get_color(i),
                marker=r'$\circ$',
                s=self.dotsize_selection,
                label=self.data[i].index.name
            )

        self.axes.set_xlim((np.floor(x_min), np.ceil(x_max)))
        self.axes.semilogy(10 ** np.floor(y_min))
        self.axes.set_ylim((10 ** np.floor(y_min), 2))
        self.legend_location = 'upper left'
        self._add_legend_if_enabled()
        self.canvas.draw()


class DensEta(IVBasePlot):
    def __init__(self, parent) -> None:
        super().__init__(parent, "Density")
        self.dotsize_enabled = False
        self.linewidth_enabled = True

    def on_draw(self) -> None:
        self.axes.clear()
        x_min, x_max = 1e4, 0

        for i in self.plot_selection:
            eta_data = self.data[i]['Eta']
            x_min = min(x_min, eta_data.min())
            x_max = max(x_max, eta_data.max())
            eta_data.plot(
                kind='kde',
                c=self._get_color(i),
                lw=self.linewidth_selection,
                label=self.data[i].index.name,
                ax=self.axes
            )

        self._setup_axis_labels(PlotAxisLabels.ETA, r'$\mathrm{\mathsf{Density\ [a.u.]}}$')
        self.axes.grid(self.grid_selection)
        self.axes.set_xlim((np.floor(x_min), np.ceil(x_max)))
        self.legend_location = 'upper left'
        self._add_legend_if_enabled()
        self.canvas.draw()


class ParametricPlotBase(IVBasePlot):
    def __init__(self, parent, title: str, param: str) -> None:
        super().__init__(parent, title)
        self._setup_parameter(param)
        self.legend_frame = True
        self.scatter = False

    def _get_parameter_data(self, dataset_index: int):
        if self.parameter == 'Voc*Isc':
            return pd.DataFrame(self.data[dataset_index]['Uoc'] * self.data[dataset_index]['Isc'])
        if self.parameter == 'RserLfDfIEC':
            return pd.DataFrame(self.data[dataset_index][self.parameter] * Converters.RSER_MULTIPLIER)
        if self.parameter == 'Rsh':
            return pd.DataFrame(self.data[dataset_index][self.parameter] / Converters.RSH_DIVISOR)
        return pd.DataFrame(self.data[dataset_index][self.parameter])

    def _get_y_label(self) -> str:
        for i, param_name in enumerate(PlotParameters.SELECTION_LIST):
            if self.parameter == param_name:
                return PlotAxisLabels.LABEL_LIST[i]
        return ''


class DistWT(ParametricPlotBase):
    def __init__(self, parent, param: str) -> None:
        super().__init__(parent, "Walkthrough", param)

    def on_draw(self) -> None:
        self.axes.clear()
        self.axes.grid(self.grid_selection)
        self.axes.set_xlabel(
            r'$\mathrm{\mathsf{Normalized\ cell\ number\ [a.u.]}}$',
            fontsize=24,
            weight='black'
        )
        self.axes.set_ylabel(self._get_y_label(), fontsize=24, weight='black')
        self.axes.tick_params(pad=8)

        for i in self.plot_selection:
            data = self._get_parameter_data(i)
            data.index = (data.index + 1) / len(data)
            self.axes.scatter(
                data.index,
                data,
                c=self._get_color(i),
                edgecolors='white',
                linewidths=0.3,
                s=self.dotsize_selection,
                label=self.data[i].index.name
            )

        self.axes.set_xlim((0, 1))
        self._add_legend_if_enabled()
        self.canvas.draw()


class DistRM(ParametricPlotBase):
    def __init__(self, parent, param: str) -> None:
        super().__init__(parent, "Rolling mean", param)
        self.dotsize_enabled = False
        self.linewidth_enabled = True

    def on_draw(self) -> None:
        self.axes.clear()
        self.axes.grid(self.grid_selection)
        self.axes.set_xlabel(
            r'$\mathrm{\mathsf{Normalized\ cell\ number\ [a.u.]}}$',
            fontsize=24,
            weight='black'
        )
        self.axes.set_ylabel(self._get_y_label(), fontsize=24, weight='black')
        self.axes.tick_params(pad=8)

        for i in self.plot_selection:
            data = self._get_parameter_data(i)
            data.index = (data.index + 1) / len(data)
            window_size = int(np.floor(len(data) * .1) if len(data) > 100 else 1)
            rolling_mean = data.rolling(center=True, window=window_size).mean()
            self.axes.plot(
                rolling_mean.index,
                rolling_mean,
                c=self._get_color(i),
                lw=self.linewidth_selection,
                label=self.data[i].index.name
            )

        self._add_legend_if_enabled()
        self.canvas.draw()


class StatisticalPlotBase(ParametricPlotBase):
    def __init__(self, parent, title: str, param: str) -> None:
        super().__init__(parent, title, param)
        self.grid_enabled = False
        self.legend_enabled = False

    def _collect_plot_data(self):
        data_list = []
        labels = []
        for i in self.plot_selection:
            data = self._get_parameter_data(i)
            data_list.append(data.values.flatten())
            labels.append(self.data[i].index.name)
        return data_list, labels


class IVBoxPlot(StatisticalPlotBase):
    def __init__(self, parent, param: str) -> None:
        super().__init__(parent, "Boxplot", param)

    def on_draw(self) -> None:
        self.axes.clear()
        self.axes.set_ylabel(self._get_y_label(), fontsize=24, weight='black')
        self.axes.tick_params(pad=8)

        if len(self.plot_selection) == 0:
            self.canvas.draw()
            return

        data, labels = self._collect_plot_data()
        boxplot = self.axes.boxplot(data, 0, '')
        self.axes.set_xticks([y + 1 for y in range(len(labels))])
        self.axes.set_xticklabels(labels, rotation=0)
        plt.setp(boxplot['boxes'], color='black', lw=2)
        plt.setp(boxplot['whiskers'], color='black', lw=2, ls='-')
        plt.setp(boxplot['caps'], color='black', lw=2)

        self.canvas.draw()


class ViolinPlot(StatisticalPlotBase):
    def __init__(self, parent, param: str) -> None:
        super().__init__(parent, "Violinplot", param)

    def on_draw(self) -> None:
        self.axes.clear()
        self.axes.set_ylabel(self._get_y_label(), fontsize=24, weight='black')
        self.axes.tick_params(pad=8)

        if len(self.plot_selection) == 0:
            self.canvas.draw()
            return

        data, labels = self._collect_plot_data()
        self.axes.violinplot(data, showmeans=False, showmedians=True)
        self.axes.set_xticks([y + 1 for y in range(len(labels))])
        self.axes.set_xticklabels(labels, rotation=0)

        self.canvas.draw()


class CategoryScatter(StatisticalPlotBase):
    def __init__(self, parent, param: str) -> None:
        super().__init__(parent, "Category scatter", param)
        self.scatter_enabled = True
        self.dotsize_selection = 20

    def on_draw(self) -> None:
        self.axes.clear()
        self.axes.set_ylabel(self._get_y_label(), fontsize=24, weight='black')
        self.axes.tick_params(pad=8)

        if len(self.plot_selection) == 0:
            self.canvas.draw()
            return

        xticks = []
        xticklabels = []
        scatter_amount = self.scatter_selection

        for i in self.plot_selection:
            data = self._get_parameter_data(i).values.flatten()
            n_points = len(data)
            x_values = scatter_amount * np.random.uniform(size=n_points) - scatter_amount * 0.5 + i
            self.axes.scatter(
                x_values,
                data,
                c=self._get_color(i),
                edgecolors='white',
                s=self.dotsize_selection
            )
            xticks.append(i)
            xticklabels.append(self.data[i].index.name)

        self.axes.set_xticks(xticks)
        self.axes.set_xticklabels(xticklabels)
        self.canvas.draw()


class SingleDatasetPlot(IVBasePlot):
    def __init__(self, parent, title: str, has_two_axes: bool = False) -> None:
        self.has_two_axes = has_two_axes
        super().__init__(parent, title)
        self.plot_selection = [0]
        self.single_dataset = True
        self.title_enabled = True
        self.title_selection = True
        self.grid_enabled = False
        self.legend_enabled = False
        self.dotsize_enabled = False

    def _get_eta_range(self):
        x_min, x_max = 1e4, 0
        for dataset in self.data.values():
            eta_data = dataset['Eta']
            x_min = min(x_min, eta_data.min())
            x_max = max(x_max, eta_data.max())
        return x_min, x_max


class IVHistPlot(SingleDatasetPlot):
    def __init__(self, parent) -> None:
        super().__init__(parent, "Histogram")

    def on_draw(self) -> None:
        self.axes.clear()
        x_min, x_max = self._get_eta_range()

        eta_data = self.data[self.plot_selection[0]]['Eta'].round(1)
        frequency = eta_data.value_counts()
        frequency = 100 * frequency / len(eta_data)
        frequency = frequency.sort_index()

        self.axes.bar(
            frequency.index,
            frequency.values,
            0.1,
            color=self._get_color(self.plot_selection[0]),
            align='center',
            edgecolor='0'
        )

        if self.title_selection:
            self.axes.set_title(self.data[self.plot_selection[0]].index.name)

        self.axes.set_xlim((np.floor(x_min), np.ceil(x_max)))
        self._setup_axis_labels(PlotAxisLabels.ETA, r'$\mathrm{\mathsf{Frequency\ [\%]}}$')
        self.axes.grid(False)
        self.canvas.draw()


class IVHistDenPlot(SingleDatasetPlot):
    def __init__(self, parent) -> None:
        super().__init__(parent, "Histogram and density", has_two_axes=True)
        self.linewidth_enabled = True

    def on_draw(self) -> None:
        self.axes.clear()
        self.axes2.clear()
        x_min, x_max = self._get_eta_range()

        dataset = self.data[self.plot_selection[0]]
        eta_data = dataset['Eta']
        binned_data = dataset['Eta'].round(1)
        frequency = binned_data.value_counts()
        frequency = 100 * frequency / len(binned_data)
        frequency = frequency.sort_index()

        self.axes.bar(
            frequency.index,
            frequency.values,
            0.1,
            color=self._get_color(self.plot_selection[0]),
            align='center',
            edgecolor='0'
        )

        eta_data.plot(kind='kde', c='white', lw=self.linewidth_selection + 3, ax=self.axes2)
        eta_data.plot(kind='kde', c='black', lw=self.linewidth_selection + 1, ax=self.axes2)
        eta_data.plot(kind='kde', c='r', lw=self.linewidth_selection, ax=self.axes2)

        if self.title_selection:
            self.axes.set_title(self.data[self.plot_selection[0]].index.name)

        self.axes.set_xlim((np.floor(x_min), np.ceil(x_max)))
        self.axes2.set_xlim((np.floor(x_min), np.ceil(x_max)))

        self._setup_axis_labels(PlotAxisLabels.ETA, r'$\mathrm{\mathsf{Frequency\ [\%]}}$')
        self.axes2.set_ylabel(
            r'$\mathrm{\mathsf{Density\ [a.u.]}}$',
            fontsize=24,
            weight='black'
        )
        self.axes2.tick_params(pad=8)

        self.axes.grid(False)
        self.axes2.grid(False)
        self.canvas.draw()
