# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plots.base_plot import IVBasePlot
from config import PlotLabels, PlotSettings, ColorPalette, PlotSelection

class DistWT(IVBasePlot):
    def __init__(self, parent, param_one_combo):
        super(DistWT, self).__init__(parent)
        self.setup_window("Walkthrough")
        
        self.dotsize_enabled = True
        self.dotsize_selection = PlotSettings.DEFAULT_DOT_SIZE
        
        if str(param_one_combo) in PlotSelection.PARAMETER_LIST:
            self.param_one_combo = str(param_one_combo)
        else:
            self.param_one_combo = 'Eta'
        
        self.create_menu()
        self.create_main_frame()
        self.on_draw()
        
    def on_draw(self):
        self.clear_and_prepare()
        
        self.setup_axes_labels(
            r'$\mathrm{\mathsf{Normalized\ cell\ number\ [a.u.]}}$',
            self.get_axis_label(self.param_one_combo)
        )
        
        for i in self.plot_selection:
            series = self.get_parameter_series(i, self.param_one_combo)
            series_df = pd.DataFrame(series)
            series_df.index = (series_df.index + 1) / len(series_df)
            
            self.axes.scatter(
                series_df.index,
                series_df,
                c=self.get_color(i),
                edgecolors=ColorPalette.EDGE_COLOR,
                linewidths=0.3,
                s=self.dotsize_selection,
                label=self.get_dataset_name(i)
            )
        
        self.axes.set_xlim((0, 1))
        self.draw_legend(loc='lower left', marker_scale=3)
        self.canvas.draw()
