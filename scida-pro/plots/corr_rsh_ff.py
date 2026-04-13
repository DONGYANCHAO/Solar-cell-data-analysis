# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plots.base_plot import IVBasePlot
from config import PlotLabels, PlotSettings, ColorPalette

class CorrRshFF(IVBasePlot):
    def __init__(self, parent):
        super(CorrRshFF, self).__init__(parent)
        self.setup_window("Correlation")
        
        self.dotsize_enabled = True
        self.dotsize_selection = PlotSettings.DEFAULT_DOT_SIZE
        
        self.create_menu()
        self.create_main_frame()
        self.on_draw()
        
    def on_draw(self):
        self.clear_and_prepare()
        
        self.setup_axes_labels(
            PlotLabels.FF_AXIS, 
            PlotLabels.RSHUNT_AXIS
        )
        
        self.axes.semilogy()
        
        for i in self.plot_selection:
            self.axes.scatter(
                self.all_data[i]['FF'],
                self.all_data[i]['Rsh'],
                c=self.get_color(i),
                edgecolors=ColorPalette.EDGE_COLOR,
                linewidths=0.3,
                s=self.dotsize_selection,
                label=self.get_dataset_name(i)
            )
        
        self.draw_legend(loc='lower left', marker_scale=3)
        self.canvas.draw()
