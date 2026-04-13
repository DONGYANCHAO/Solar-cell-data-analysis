# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plots.base_plot import IVBasePlot
from config import PlotLabels, PlotSettings, ColorPalette

class DistLtoH(IVBasePlot):
    def __init__(self, parent):
        super(DistLtoH, self).__init__(parent)
        self.setup_window("Distribution")
        
        self.dotsize_enabled = True
        self.dotsize_selection = PlotSettings.DEFAULT_LARGE_DOT_SIZE
        
        self.create_menu()
        self.create_main_frame()
        self.on_draw()
        
    def on_draw(self):
        self.clear_and_prepare()
        
        xmin = 1e4
        xmax = 0
        ymin = -1
        
        self.setup_axes_labels(
            PlotLabels.ETA_AXIS,
            r'$\mathrm{\mathsf{Normalized\ cell\ number\ [a.u.]}}$'
        )
        
        for i in self.plot_selection:
            sorted_eta = pd.DataFrame(np.sort(self.all_data[i]['Eta']))
            
            if sorted_eta.iloc[:, 0].min() <= xmin:
                xmin = sorted_eta.iloc[:, 0].min()
            if sorted_eta.iloc[:, 0].max() >= xmax:
                xmax = sorted_eta.iloc[:, 0].max()
            if np.log10(1 / len(sorted_eta)) < ymin:
                ymin = np.log10(1 / len(sorted_eta))
            
            sorted_eta.index = (sorted_eta.index + 1) / len(sorted_eta)
            
            self.axes.scatter(
                sorted_eta,
                sorted_eta.index,
                c=self.get_color(i),
                edgecolor=self.get_color(i),
                marker=r'$\circ$',
                s=self.dotsize_selection,
                label=self.get_dataset_name(i)
            )
        
        self.axes.set_xlim((np.floor(xmin), np.ceil(xmax)))
        self.axes.semilogy(10 ** np.floor(ymin))
        self.axes.set_ylim((10 ** np.floor(ymin), 2))
        
        self.draw_legend(loc='upper left', marker_scale=1)
        self.canvas.draw()
