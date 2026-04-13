# -*- coding: utf-8 -*-
"""
常量定义模块 - 枚举和常量定义
"""
from enum import Enum
from typing import Dict, List, Tuple


class DataColumn(Enum):
    """数据列名枚举"""
    UOC = 'Uoc'
    ISC = 'Isc'
    RSER_LF_DF_IEC = 'RserLfDfIEC'
    RSH = 'Rsh'
    FF = 'FF'
    ETA = 'Eta'
    IREV1 = 'IRev1'

    UOC0 = 'Uoc0'
    ISC0 = 'Isc0'
    RSERIES_MULTI_LEVEL = 'Rseries_multi_level'
    RSHUNT_SC = 'Rshunt_SC'
    FILL0 = 'Fill0'
    EFF0 = 'Eff0'
    IREVERSE_2 = 'Ireverse_2'

    UOC_IEC = 'Uoc'
    RSER_IEC891 = 'RserIEC891'
    RSHUNT_DF_DR = 'RshuntDfDr'

    RS = 'Rs'
    NCELL = 'NCell'
    IREV2 = 'Irev2'


class PlotType(Enum):
    """图表类型枚举"""
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


class LabelFormat(Enum):
    """数据标签格式枚举"""
    FORMAT_A = 0
    FORMAT_B = 1
    FORMAT_C = 2
    FORMAT_D = 3
    CUSTOM = 4


class FilterOperator(Enum):
    """过滤操作符枚举"""
    GREATER_THAN = '>'
    LESS_THAN = '<'


class ColorPalette(Enum):
    """颜色调色板"""
    PRIMARY_COLORS = [
        '#4F81BD',
        '#C0504D',
        '#9BBB59',
        '#F79646',
        '#8064A2',
        '#4BACC6',
    ]
    DEFAULT_COLOR = 'black'
    SECONDARY_COLOR = '0.5'


class SummaryIndex(Enum):
    """汇总表索引"""
    BEST_CELL = 'Best cell'
    MEDIAN = 'Median'
    AVERAGE = 'Average'
    STD_DEV = 'Std.dev.'


LABEL_FORMATS: Dict[int, List[str]] = {
    0: ['Uoc', 'Isc', 'RserLfDfIEC', 'Rsh', 'FF', 'Eta', 'IRev1'],
    1: ['Uoc0', 'Isc0', 'Rseries_multi_level', 'Rshunt_SC', 'Fill0', 'Eff0', 'Ireverse_2'],
    2: ['Uoc', 'Isc', 'RserIEC891', 'RshuntDfDr', 'FF', 'Eta', 'IRev1'],
    3: ['Uoc', 'Isc', 'Rs', 'Rsh', 'FF', 'NCell', 'Irev2'],
    4: ['Uoc', 'Isc', 'RserLfDfIEC', 'Rsh', 'FF', 'Eta', 'IRev1'],
}

DEFAULT_FILTERS: List[List] = [
    ['IRev1', '>', 3],
    ['FF', '<', 70],
    ['Eta', '<', 16],
    ['FF', '<', 75],
    ['Rsh', '<', 20],
    ['Eta', '<', 18]
]

SUMMARY_COLUMNS: List[str] = [
    'Voc [V]',
    'Isc [A]',
    'Rser [mOhm*cm2]',
    'Rshunt [kOhm]',
    'FF [%]',
    'Eta [%]',
    'Irev [A]'
]

SUMMARY_INDEX: List[str] = [
    'Best cell',
    'Median',
    'Average',
    'Std.dev.'
]

YIELD_LOSS_COLUMNS: List[str] = [f'Filter {i+1}' for i in range(12)]

YIELD_LOSS_INDEX: List[str] = ['Filter', 'Loss count']

PLOT_PARAMETERS: List[str] = [
    'Uoc',
    'Isc',
    'Voc*Isc',
    'FF',
    'Eta',
    'RserLfDfIEC',
    'Rsh',
    'IRev1'
]

PLOT_SELECTION_COMBO_LIST: List[str] = [
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
    'Rsh-FF'
]

AXIS_LABELS: Dict[str, str] = {
    'irev': r'$\mathrm{\mathsf{I_{REV}\ [A]}}$',
    'rser': r'$\mathrm{\mathsf{R_{SERIES}\ [mOhm \cdot cm^{2}]}}$',
    'rshunt': r'$\mathrm{\mathsf{R_{SHUNT}\ [kOhm]}}$',
    'eta': r'$\mathrm{\mathsf{Eta\ [\%]}}$',
    'voc': r'$\mathrm{\mathsf{V_{OC}\ [V]}}$',
    'isc': r'$\mathrm{\mathsf{I_{SC}\ [A]}}$',
    'ff': r'$\mathrm{\mathsf{FF\ [\%]}}$',
    'vocisc': r'$\mathrm{\mathsf{V_{OC}\ *\ I_{SC}\ [V*A]}}$',
    'normalized_cell': r'$\mathrm{\mathsf{Normalized\ cell\ number\ [a.u.]}}$',
    'density': r'$\mathrm{\mathsf{Density\ [a.u.]}}$',
}

PLOT_LABEL_LIST: List[str] = [
    AXIS_LABELS['voc'],
    AXIS_LABELS['isc'],
    AXIS_LABELS['vocisc'],
    AXIS_LABELS['ff'],
    AXIS_LABELS['eta'],
    AXIS_LABELS['rser'],
    AXIS_LABELS['rshunt'],
    AXIS_LABELS['irev'],
]

WINDOW_SIZE: Tuple[int, int] = (1024, 576)
PLOT_WINDOW_SIZE: Tuple[int, int] = (1020, 752)

FONT_SIZE: int = 14
DOT_SIZE: int = 20
DOT_SIZE_LARGE: int = 200
LINE_WIDTH: int = 3
LINE_WIDTH_DEFAULT: int = 1

DATASET_NAME_MAX_LENGTH: int = 39

FILTER_TABLE_ROWS: int = 12
FILTER_TABLE_COLS: int = 3

ROLLING_WINDOW_RATIO: float = 0.1
ROLLING_WINDOW_MIN: int = 1

CONVERSION_FACTORS: Dict[str, float] = {
    'eta_percent': 100.0,
    'ff_percent': 100.0,
    'rser_mohm': 1000.0,
    'rsh_kohm': 0.001,
}

ROUNDING_PRECISION: Dict[str, int] = {
    'voc': 3,
    'isc': 2,
    'rser': 2,
    'rsh': 2,
    'ff': 1,
    'eta': 2,
    'irev': 2,
}

VALID_FILTER_OPERATORS: List[str] = ['<', '>']

DATA_INDEX_COLUMNS: List[str] = ['Uoc', 'Isc', 'RserLfDfIEC', 'Rsh', 'FF', 'Eta', 'IRev1']

NULL_DATA_VALUES: List[float] = [-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0]
