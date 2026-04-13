# -*- coding: utf-8 -*-
from enum import Enum, IntEnum


class LabelFormat(IntEnum):
    A = 0
    B = 1
    C = 2
    D = 3
    CUSTOM = 4


class DataColumns:
    STANDARD = ['Uoc', 'Isc', 'RserLfDfIEC', 'Rsh', 'FF', 'Eta', 'IRev1']
    FORMAT_B = ['Uoc0', 'Isc0', 'Rseries_multi_level', 'Rshunt_SC', 'Fill0', 'Eff0', 'Ireverse_2']
    FORMAT_C = ['Uoc', 'Isc', 'RserIEC891', 'RshuntDfDr', 'FF', 'Eta', 'IRev1']
    FORMAT_D = ['Uoc', 'Isc', 'Rs', 'Rsh', 'FF', 'NCell', 'Irev2']

    LABEL_FORMATS = {
        LabelFormat.A: STANDARD,
        LabelFormat.B: FORMAT_B,
        LabelFormat.C: FORMAT_C,
        LabelFormat.D: FORMAT_D,
        LabelFormat.CUSTOM: STANDARD,
    }


class PlotParameters:
    SELECTION_LIST = ['Uoc', 'Isc', 'Voc*Isc', 'FF', 'Eta', 'RserLfDfIEC', 'Rsh', 'IRev1']
    COMBO_LIST = [
        'Boxplot', 'Violinplot', 'Category scatter', 'Walk-through',
        'Rolling mean', 'Low to high', 'Histogram', 'Density',
        'Histogram + density', 'Voc-Isc', 'Eta-FF', 'Rsh-FF'
    ]


class PlotColors:
    PALETTE = [
        '#4F81BD', '#C0504D', '#9BBB59', '#F79646',
        '#8064A2', '#4BACC6', '0', '0.5'
    ]


class PlotAxisLabels:
    IREV = r'$\mathrm{\mathsf{I_{REV}\ [A]}}$'
    RSER = r'$\mathrm{\mathsf{R_{SERIES}\ [mOhm \cdot cm^{2}]}}$'
    RSHUNT = r'$\mathrm{\mathsf{R_{SHUNT}\ [kOhm]}}$'
    ETA = r'$\mathrm{\mathsf{Eta\ [\%]}}$'
    VOC = r'$\mathrm{\mathsf{V_{OC}\ [V]}}$'
    ISC = r'$\mathrm{\mathsf{I_{SC}\ [A]}}$'
    FF = r'$\mathrm{\mathsf{FF\ [\%]}}$'
    VOC_ISC = r'$\mathrm{\mathsf{V_{OC}\ *\ I_{SC}\ [V*A]}}$'

    LABEL_LIST = [VOC, ISC, VOC_ISC, FF, ETA, RSER, RSHUNT, IREV]


class MatplotlibStyle:
    FONT_FAMILY = 'sans-serif'
    FONT_SIZE = 14
    DPI = 100
    FIGURE_SIZE = (10.0, 10.0)
    FACECOLOR = 'White'


class WindowConfig:
    MAIN_WIDTH = 1024
    MAIN_HEIGHT = 576
    PLOT_WIDTH = 1020
    PLOT_HEIGHT = 752
    FONT_SIZE = 12


class FilterConfig:
    DEFAULT_FILTERS = [
        ["IRev1", ">", 3], ["FF", "<", 70], ["Eta", "<", 16],
        ["FF", "<", 75], ["Rsh", "<", 20], ["Eta", "<", 18]
    ]
    MAX_FILTERS = 12
    FILTER_OPERATORS = ['<', '>']


class SummaryConfig:
    INDEX = ['Best cell', 'Median', 'Average', 'Std.dev.']
    COLUMNS = ['Voc [V]', 'Isc [A]', 'Rser [mOhm*cm2]', 'Rshunt [kOhm]', 'FF [%]', 'Eta [%]', 'Irev [A]']
    ROUNDING = [3, 2, 2, 2, 1, 2, 2]


class FileExtensions:
    DATA = ['*.csv', '*.xls', '*.xlsx']
    CSV = '*.csv'
    EXCEL = '*.xlsx'
    FILTERS = '*.scda'
    LABELS = '*.csv'


class Converters:
    RSER_MULTIPLIER = 1000
    RSH_DIVISOR = 1000


class LoggingConfig:
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LEVEL = 'INFO'


class ExceptionMessages:
    NON_ASCII_FILENAME = "Filenames with non-ASCII characters were found.\n\nThe application currently only supports ASCII filenames."
    READ_ERROR = "Error while reading data files.\n\nData labels were perhaps not recognized."
    EMPTY_DATA = "Empty data sets were found.\n\nThe application only accepts data entries with a value for Voc, Isc, FF, Eta, Rser, Rsh and Irev. All values also need to be non-negative."
    FILE_NOT_FOUND = "Could not read file \"{}\""
    FILE_SAVE_ERROR = "Could not save file \"{}\""
    NO_DATA = "Please load data files"


class PlotType(Enum):
    BOXPLOT = 0
    VIOLINPLOT = 1
    CATEGORY_SCATTER = 2
    WALKTHROUGH = 3
    ROLLING_MEAN = 4
    LOW_TO_HIGH = 5
    HISTOGRAM = 6
    DENSITY = 7
    HISTOGRAM_DENSITY = 8
    CORR_VOC_ISC = 9
    CORR_ETA_FF = 10
    CORR_RSH_FF = 11


NULL_DATA_ROW = [-1, -1, -1, -1, -1, -1, -1]
KEEP_CHARACTERS = (' ', '.', '_')
