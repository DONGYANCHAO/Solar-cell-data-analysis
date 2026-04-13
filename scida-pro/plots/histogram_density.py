# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plots.base_plot import IVBasePlot
from config import PlotLabels, PlotSettings, ColorPalette, FontSettings

class IVHistDenPlot(IVBasePlot):
    def __init__(self, parent):
        super(IVHistDenPlot, self).__init__(parent)
        self.setup_window("Histogram + density")
        
        self.title_enabled = True
        self.title_selection = False
        self.grid_enabled = True
        self.grid_selection = True
        
        self.create_menu()
        self.create_main_frame()
        self.on_draw()
        
    def on_draw(self):
        self.axes.clear()
        
        all_eta = []
        for i in self.plot_selection:
            all_eta.extend(self.all_data[i]['Eta'].values)
        
        all_eta = np.array(all_eta)
        
        self.axes.hist(all_eta, bins=50, density=True, color=ColorPalette.COLORS[0], 
                      edgecolor='black', alpha=0.5, label='Histogram')
        
        all_eta_series = pd.Series(all_eta)
        all_eta_series.plot(kind='kde', c=ColorPalette.COLORS[1], lw=2, ax=self.axes, label='Density')
        
        self.setup_axes_labels(
            PlotLabels.ETA_AXIS,
            r'$\mathrm{\mathsf{Density\ [a.u.]}}$'
        )
        
        if self.title_selection:
            self.axes.set_title('Eta Distribution with Density')
        
        self.apply_grid()
        self.draw_legend(loc='upper left', marker_scale=1)
        self.canvas.draw()
