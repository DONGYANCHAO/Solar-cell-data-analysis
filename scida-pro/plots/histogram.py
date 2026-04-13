# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plots.base_plot import IVBasePlot
from config import PlotLabels, PlotSettings, ColorPalette, FontSettings

class IVHistPlot(IVBasePlot):
    def __init__(self, parent):
        super(IVHistPlot, self).__init__(parent)
        self.setup_window("Histogram")
        
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
        
        self.axes.hist(all_eta, bins=50, color=ColorPalette.COLORS[0], edgecolor='black', alpha=0.7)
        
        self.setup_axes_labels(
            PlotLabels.ETA_AXIS,
            r'$\mathrm{\mathsf{Count}}$'
        )
        
        if self.title_selection:
            self.axes.set_title('Eta Distribution')
        
        self.apply_grid()
        self.canvas.draw()
