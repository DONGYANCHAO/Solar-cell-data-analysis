# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plots.base_plot import IVBasePlot
from config import PlotLabels, PlotSettings, ColorPalette

class DensEta(IVBasePlot):
    def __init__(self, parent):
        super(DensEta, self).__init__(parent)
        self.setup_window("Density")
        
        self.linewidth_enabled = True
        self.linewidth_selection = PlotSettings.DEFAULT_LINE_WIDTH
        
        self.create_menu()
        self.create_main_frame()
        self.on_draw()
        
    def on_draw(self):
        self.axes.clear()
        
        xmin = 1e4
        xmax = 0
        
        for i in self.plot_selection:
            eta_series = self.all_data[i]['Eta']
            
            if eta_series.min() <= xmin:
                xmin = eta_series.min()
            if eta_series.max() >= xmax:
                xmax = eta_series.max()
            
            eta_series.plot(
                kind='kde',
                c=self.get_color(i),
                lw=self.linewidth_selection,
                label=self.get_dataset_name(i),
                ax=self.axes
            )
        
        self.setup_axes_labels(
            PlotLabels.ETA_AXIS,
            r'$\mathrm{\mathsf{Density\ [a.u.]}}$'
        )
        
        self.apply_grid()
        self.axes.set_xlim((np.floor(xmin), np.ceil(xmax)))
        
        self.draw_legend(loc='upper left', marker_scale=1)
        self.canvas.draw()
