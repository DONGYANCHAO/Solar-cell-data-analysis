# -*- coding: utf-8 -*-
from enum import Enum, auto
from typing import Dict, List, Tuple

class DataLabelFormat(Enum):
    FORMAT_A = 0
    FORMAT_B = 1
    FORMAT_C = 2
    FORMAT_D = 3
    FORMAT_CUSTOM = 4

class PlotType(Enum):
    BOXPLOT = 0
    VIOLINPLOT = 1
    CATEGORY_SCATTER = 2
    WALK_THROUGH = 3
    ROLLING_MEAN = 4
    LOW_TO_HIGH = 5
    HISTOGRAM = 6
    DENSITY = 7
    HISTOGRAM_DENSITY = 8
    VOC_ISC = 9
    ETA_FF = 10
    RSH_FF = 11

class FilterOperator(Enum):
    GREATER_THAN = ">"
    LESS_THAN = "<"

class WindowSize:
    WIDTH = 1024
    HEIGHT = 576
    PLOT_WIDTH = 1020
    PLOT_HEIGHT = 752

class FontSettings:
    SIZE = 12
    PLOT_SIZE = 14
    AXIS_SIZE = 24
    FAMILY = 'sans-serif'

class ColorPalette:
    COLORS = ['#4F81BD', '#C0504D', '#9BBB59', '#F79646', '#8064A2', '#4BACC6', '0', '0.5']
    WHITE = 'white'
    BACKGROUND = 'White'
    EDGE_COLOR = 'white'

class DataParameters:
    INTERNAL_NAMES = ['Uoc', 'Isc', 'RserLfDfIEC', 'Rsh', 'FF', 'Eta', 'IRev1']
    
    LABEL_FORMATS: Dict[int, List[str]] = {
        0: ['Uoc', 'Isc', 'RserLfDfIEC', 'Rsh', 'FF', 'Eta', 'IRev1'],
        1: ['Uoc0', 'Isc0', 'Rseries_multi_level', 'Rshunt_SC', 'Fill0', 'Eff0', 'Ireverse_2'],
        2: ['Uoc', 'Isc', 'RserIEC891', 'RshuntDfDr', 'FF', 'Eta', 'IRev1'],
        3: ['Uoc', 'Isc', 'Rs', 'Rsh', 'FF', 'NCell', 'Irev2'],
        4: ['Uoc', 'Isc', 'RserLfDfIEC', 'Rsh', 'FF', 'Eta', 'IRev1'],
    }

class SummaryConfig:
    INDEX_NAMES = ['Best cell', 'Median', 'Average', 'Std.dev.']
    COLUMN_NAMES = ['Voc [V]', 'Isc [A]', 'Rser [mOhm*cm2]', 'Rshunt [kOhm]', 'FF [%]', 'Eta [%]', 'Irev [A]']
    ROUNDING_DECIMALS = [3, 2, 2, 2, 1, 2, 2]
    STD_DEV_PARAMS = [0, 1, 4, 5]

class FilterConfig:
    MAX_FILTERS = 12
    DEFAULT_FILTERS = [
        ["IRev1", ">", 3],
        ["FF", "<", 70],
        ["Eta", "<", 16],
        ["FF", "<", 75],
        ["Rsh", "<", 20],
        ["Eta", "<", 18],
    ]

class PlotLabels:
    IREV_AXIS = r'$\mathrm{\mathsf{I_{REV}\ [A]}}$'
    RSER_AXIS = r'$\mathrm{\mathsf{R_{SERIES}\ [mOhm \cdot cm^{2}]}}$'
    RSHUNT_AXIS = r'$\mathrm{\mathsf{R_{SHUNT}\ [kOhm]}}$'
    ETA_AXIS = r'$\mathrm{\mathsf{Eta\ [\%]}}$'
    VOC_AXIS = r'$\mathrm{\mathsf{V_{OC}\ [V]}}$'
    ISC_AXIS = r'$\mathrm{\mathsf{I_{SC}\ [A]}}$'
    FF_AXIS = r'$\mathrm{\mathsf{FF\ [\%]}}$'
    VOCISC_AXIS = r'$\mathrm{\mathsf{V_{OC}\ *\ I_{SC}\ [V*A]}}$'
    
    LABEL_MAP = {
        'Uoc': VOC_AXIS,
        'Isc': ISC_AXIS,
        'Voc*Isc': VOCISC_AXIS,
        'FF': FF_AXIS,
        'Eta': ETA_AXIS,
        'RserLfDfIEC': RSER_AXIS,
        'Rsh': RSHUNT_AXIS,
        'IRev1': IREV_AXIS,
    }

class PlotSelection:
    PARAMETER_LIST = ['Uoc', 'Isc', 'Voc*Isc', 'FF', 'Eta', 'RserLfDfIEC', 'Rsh', 'IRev1']
    TYPE_LIST = [
        'Boxplot',
        'Violinplot',
        'Category scatter',
        'Walk-through',
        'Rolling mean',
        'Low to high',
        'Histogram',
        'Density',
        'Histogram + density',
        'Voc-Isc',
        'Eta-FF',
        'Rsh-FF',
    ]

class PlotSettings:
    DEFAULT_DOT_SIZE = 20
    DEFAULT_LINE_WIDTH = 3
    DEFAULT_LARGE_DOT_SIZE = 200
    LEGEND_LOC_LOWER_LEFT = 'lower left'
    LEGEND_LOC_UPPER_LEFT = 'upper left'
    SCATTER_POINTS = 1
    MARKER_SCALE = 3
    MARKER_SCALE_LARGE = 1

class ConversionFactors:
    RSER_MULTIPLIER = 1000
    RSH_DIVISOR = 1000
    PERCENTAGE_MULTIPLIER = 100
    DATASET_NAME_MAX_LENGTH = 40

class FileExtensions:
    CSV = '.csv'
    XLS = '.xls'
    XLSX = '.xlsx'
    SCDA = '.scda'
    
    EXCEL_FILTER = "Excel Files (*.csv *.xls *.xlsx)"
    CSV_FILTER = "CSV File (*.csv)"
    SCDA_FILTER = "Filter Settings Files (*.scda)"
    LABEL_FILTER = "Label Settings File (*.csv)"
    XLSX_FILTER = "Excel Files (*.xlsx)"

class Messages:
    ERROR_READ_DATA = "Error while reading data files.\n\nData labels were perhaps not recognized."
    ERROR_EMPTY_DATA = "Empty data sets were found.\n\nThe application only accepts data entries with a value for Voc, Isc, FF, Eta, Rser, Rsh and Irev. All values also need to be non-negative."
    ERROR_NON_ASCII = "Filenames with non-ASCII characters were found.\n\nThe application currently only supports ASCII filenames."
    ERROR_FILE_READ = "Could not read file \"{}\""
    ERROR_FILE_SAVE = "Could not save file \"{}\""
    
    STATUS_READY = "Ready"
    STATUS_LOAD_FILES = "Please load data files"
    STATUS_FILTERING = "Filtering data..."
    STATUS_COMBINING = "Combining data sets..."
    STATUS_MAKING_REPORT = "Making an Excel report..."
    STATUS_OPENING_REPORT = "Opening report..."
    STATUS_FILES_SAVED = "Files saved"
    STATUS_NEW_FILTERS_LOADED = "New filter settings loaded"
    STATUS_CHECKING_FILTERS = "Checking filters..."

class WindowConfig:
    TITLE = "SCiDA Pro"
    ABOUT_TEXT = "Solar cell data analysis\nAuthor: Ronald Naber\nLicense: Public domain"
