# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plots.base_plot import IVBasePlot
from config import PlotLabels, PlotSettings, ColorPalette, PlotSelection, FontSettings

class ViolinPlot(IVBasePlot):
    def __init__(self, parent, param_one_combo):
        super(ViolinPlot, self).__init__(parent)
        self.setup_window("Violinplot")
        
        self.grid_enabled = False
        self.legend_enabled = False
        
        if str(param_one_combo) in PlotSelection.PARAMETER_LIST:
            self.param_one_combo = str(param_one_combo)
        else:
            self.param_one_combo = 'Eta'
        
        self.create_menu()
        self.create_main_frame()
        self.on_draw()
        
    def on_draw(self):
        self.axes.clear()
        
        data_list = []
        labels_list = []
        
        for i in self.plot_selection:
            series = self.get_parameter_series(i, self.param_one_combo)
            data_list.append(series.values)
            labels_list.append(self.get_dataset_name(i))
        
        parts = self.axes.violinplot(data_list, showmeans=False, showmedians=False, showextrema=False)
        
        for idx, pc in enumerate(parts['bodies']):
            pc.set_facecolor(self.get_color(idx))
            pc.set_edgecolor('black')
            pc.set_alpha(0.7)
        
        self.axes.set_xticks(np.arange(1, len(labels_list) + 1))
        self.axes.set_xticklabels(labels_list, rotation=45, ha='right')
        self.axes.set_ylabel(self.get_axis_label(self.param_one_combo), 
                            fontsize=FontSettings.AXIS_SIZE, weight='black')
        self.axes.tick_params(pad=8)
        
        self.canvas.draw()
