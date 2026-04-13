# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plots.base_plot import IVBasePlot
from config import PlotLabels, PlotSettings, ColorPalette, PlotSelection, FontSettings

class CategoryScatter(IVBasePlot):
    def __init__(self, parent, param_one_combo):
        super(CategoryScatter, self).__init__(parent)
        self.setup_window("Category scatter")
        
        self.dotsize_enabled = True
        self.dotsize_selection = PlotSettings.DEFAULT_DOT_SIZE
        self.scatter_enabled = True
        self.scatter_selection = 0.0
        
        if str(param_one_combo) in PlotSelection.PARAMETER_LIST:
            self.param_one_combo = str(param_one_combo)
        else:
            self.param_one_combo = 'Eta'
        
        self.create_menu()
        self.create_main_frame()
        self.on_draw()
        
    def on_draw(self):
        self.clear_and_prepare()
        
        all_data_list = []
        all_labels = []
        all_colors = []
        
        for idx, i in enumerate(self.plot_selection):
            series = self.get_parameter_series(i, self.param_one_combo)
            scatter_offset = np.random.uniform(-self.scatter_selection, self.scatter_selection, len(series))
            
            for j, value in enumerate(series):
                all_data_list.append(value)
                all_labels.append(idx + scatter_offset[j])
                all_colors.append(self.get_color(i))
        
        self.axes.scatter(all_labels, all_data_list, c=all_colors, s=self.dotsize_selection, alpha=0.6)
        
        self.axes.set_ylabel(self.get_axis_label(self.param_one_combo), 
                            fontsize=FontSettings.AXIS_SIZE, weight='black')
        self.axes.tick_params(pad=8)
        
        unique_indices = list(range(len(self.plot_selection)))
        dataset_names = [self.get_dataset_name(i) for i in self.plot_selection]
        self.axes.set_xticks(unique_indices)
        self.axes.set_xticklabels(dataset_names, rotation=45, ha='right')
        
        self.canvas.draw()
