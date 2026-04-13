# -*- coding: utf-8 -*-
"""
SCiDA Pro 主 GUI 模块 - 重构后版本
仅保留界面逻辑，业务逻辑已抽取到服务层
"""
import os
import subprocess
import sys
from typing import List, Optional

import numpy as np
import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets

from HelpDialog import HelpDialog
from config.constants import (
    DEFAULT_FILTERS,
    PLOT_PARAMETERS,
    PLOT_SELECTION_COMBO_LIST,
    LABEL_FORMATS,
    FILTER_TABLE_ROWS,
    FILTER_TABLE_COLS,
    WINDOW_SIZE,
    DATASET_NAME_MAX_LENGTH,
)
from utils.logger import get_logger, setup_logging
from utils.validators import is_number, remove_whitespace, sanitize_filename
from utils.exceptions import SCiDAError, DataLoadError, FileFormatError
from services.data_service import DataService
from services.file_service import FileService
from services.filter_service import FilterService
from services.report_generator import ReportGenerator
from plots import (
    CorrVocIsc,
    CorrEtaFF,
    CorrRshFF,
    DistLtoH,
    DensEta,
    DistWT,
    DistRM,
    IVBoxPlot,
    ViolinPlot,
    CategoryScatter,
    IVHistPlot,
    IVHistDenPlot,
)

setup_logging()
logger = get_logger(__name__)


class IVMainGui(QtWidgets.QMainWindow):
    """SCiDA Pro 主窗口类"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._init_services()
        self._init_ui_state()
        self._setup_window()
        self._create_menu()
        self._create_main_frame()
        self._set_default_filters()
        
    def _init_services(self) -> None:
        """初始化服务层"""
        self.data_service = DataService()
        self.file_service = FileService()
        self.filter_service = FilterService()
        self.report_generator = ReportGenerator(self.data_service)
        
    def _init_ui_state(self) -> None:
        """初始化 UI 状态"""
        self.clipboard = QtWidgets.QApplication.clipboard()
        self.series_list_model = QtGui.QStandardItemModel()
        self.series_list_model.itemChanged.connect(self._on_dataset_renamed)
        
        self.filter_table_widget = QtWidgets.QTableWidget()
        self.user_filters_plain_format: List[List] = []
        
        self.label_format = 0
        self.label_text = QtWidgets.QLabel("Data label set A")
        self.first_run = True
        self.status_text = QtWidgets.QLabel("")
        
        self.plot_window: Optional[QtWidgets.QMainWindow] = None
        self.translator: Optional[QtCore.QTranslator] = None
        
        self.param_one_combo = QtWidgets.QComboBox(self)
        self.plot_selection_combo = QtWidgets.QComboBox(self)
        self.plot_selection_combo.currentIndexChanged.connect(
            self._on_plot_selection_changed
        )
        
    def _setup_window(self) -> None:
        """设置窗口属性"""
        self.setWindowTitle(self.tr("SCiDA Pro"))
        self.setWindowIcon(QtGui.QIcon(":ScidaPro_icon.png"))
        
        self.resize(*WINDOW_SIZE)
        frame_geometry = self.frameGeometry()
        center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())
        
        self.setStyleSheet('font-size: 12pt;')
        
    @property
    def ad(self) -> dict:
        """兼容旧代码的数据访问属性"""
        return self.data_service.get_data()
        
    @QtCore.pyqtSlot(int)
    def _on_plot_selection_changed(self, index: int) -> None:
        """绘图选择改变事件"""
        if index < 3:
            self.param_one_combo.setEnabled(True)
        elif 2 < index < 7:
            self.param_one_combo.setCurrentIndex(4)
            self.param_one_combo.setDisabled(True)
        else:
            self.param_one_combo.setDisabled(True)
            
    @QtCore.pyqtSlot(QtGui.QStandardItem)
    def _on_dataset_renamed(self, item: QtGui.QStandardItem) -> None:
        """数据集重命名事件"""
        entered_name = str(item.text())
        valid_name = sanitize_filename(entered_name, DATASET_NAME_MAX_LENGTH)
        
        if valid_name:
            row = self.series_list_model.indexFromItem(item).row()
            self.data_service.rename_dataset(row, valid_name)
            item.setText(valid_name)
        else:
            row = self.series_list_model.indexFromItem(item).row()
            dataset = self.data_service.get_dataset(row)
            if dataset is not None:
                item.setText(dataset.index.name)
                
    def load_file(self) -> None:
        """加载数据文件"""
        file_paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            self.tr("Load files"),
            self.file_service.get_previous_directory(),
            "Excel Files (*.csv *.xls *.xlsx)"
        )
        
        if not file_paths:
            return
            
        empty_data_warning = False
        non_ascii_warning = False
        read_error_warning = False
        
        for file_path in file_paths:
            try:
                valid, _ = self._validate_filename(file_path)
                if not valid:
                    non_ascii_warning = True
                    continue
                    
                dataframe = self.file_service.load_data_file(
                    file_path,
                    self.label_format
                )
                
                if dataframe is None:
                    read_error_warning = True
                    continue
                    
                processed_df = self.data_service.process_loaded_data(
                    dataframe,
                    self.label_format
                )
                
                if processed_df is None:
                    empty_data_warning = True
                    continue
                    
                dataset_name = os.path.splitext(
                    os.path.basename(file_path)
                )[0]
                index = self.data_service.add_dataframe(processed_df, dataset_name)
                self._add_dataset_to_list(index, dataset_name)
                
            except (DataLoadError, FileFormatError) as e:
                logger.error(f"加载文件失败: {e}")
                read_error_warning = True
                
        self._show_load_warnings(
            read_error_warning,
            empty_data_warning,
            non_ascii_warning
        )
        
        self._update_status_after_load()
        
    def _validate_filename(self, filename: str) -> tuple:
        """验证文件名"""
        try:
            filename.encode('ascii')
            return True, ""
        except UnicodeEncodeError:
            return False, "非ASCII字符"
            
    def _add_dataset_to_list(self, index: int, name: str) -> None:
        """添加数据集到列表"""
        item = QtGui.QStandardItem(name[:DATASET_NAME_MAX_LENGTH])
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        self.series_list_model.appendRow(item)
        
    def _show_load_warnings(
        self,
        read_error: bool,
        empty_data: bool,
        non_ascii: bool
    ) -> None:
        """显示加载警告"""
        if read_error:
            QtWidgets.QMessageBox.about(
                self,
                self.tr("Warning"),
                self.tr("Error while reading data files.\n\nData labels were perhaps not recognized.")
            )
            
        if empty_data:
            QtWidgets.QMessageBox.about(
                self,
                self.tr("Warning"),
                self.tr("Empty data sets were found.\n\nThe application only accepts data entries with a value for Voc, Isc, FF, Eta, Rser, Rsh and Irev. All values also need to be non-negative.")
            )
            
        if non_ascii:
            QtWidgets.QMessageBox.about(
                self,
                self.tr("Warning"),
                self.tr("Filenames with non-ASCII characters were found.\n\nThe application currently only supports ASCII filenames.")
            )
            
    def _update_status_after_load(self) -> None:
        """加载后更新状态"""
        if self.data_service.get_data():
            self.statusBar().showMessage(self.tr("Ready"), 3000)
        else:
            self.statusBar().showMessage(self.tr("Please load data files"), 3000)
            
    def save_files(self) -> None:
        """保存数据文件"""
        if self.data_service.get_dataset_count() == 0:
            self.statusBar().showMessage(self.tr("Please load data files"), 3000)
            return
            
        dest_dir = QtWidgets.QFileDialog.getExistingDirectory(
            None,
            self.tr('Open directory'),
            self.file_service.get_previous_directory(),
            QtWidgets.QFileDialog.ShowDirsOnly
        )
        
        if not dest_dir:
            return
            
        self.file_service.set_previous_directory(dest_dir)
        yes_to_all = False
        
        for index, dataframe in self.data_service.get_data().items():
            filename = f"{dataframe.index.name}.csv"
            save_path = os.path.join(dest_dir, filename)
            
            if os.path.isfile(save_path) and not yes_to_all:
                reply = QtWidgets.QMessageBox.question(
                    self,
                    self.tr("Message"),
                    f"Overwrite '{filename}'?",
                    QtWidgets.QMessageBox.YesToAll |
                    QtWidgets.QMessageBox.Yes |
                    QtWidgets.QMessageBox.No |
                    QtWidgets.QMessageBox.Cancel,
                    QtWidgets.QMessageBox.No
                )
                
                if reply == QtWidgets.QMessageBox.No:
                    save_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                        self,
                        self.tr("Save file"),
                        dest_dir,
                        "CSV File (*.csv)"
                    )
                    if not save_path:
                        continue
                        
                elif reply == QtWidgets.QMessageBox.YesToAll:
                    yes_to_all = True
                    
                elif reply == QtWidgets.QMessageBox.Cancel:
                    return
                    
            try:
                self.file_service.save_data_file(dataframe, dest_dir, filename)
            except Exception as e:
                logger.error(f"保存文件失败: {e}")
                
        self.statusBar().showMessage(self.tr("Files saved"), 3000)
        
    def combine_datasets(self) -> None:
        """合并数据集"""
        if self.data_service.get_dataset_count() <= 1:
            self.statusBar().showMessage(self.tr("Please load data files"), 3000)
            return
            
        self.statusBar().showMessage(self.tr("Combining data sets..."), 3000)
        
        self.filter_service = FilterService()
        self.series_list_model.clear()
        self.series_list_model.setHorizontalHeaderLabels([self.tr('Data series')])
        
        combined = self.data_service.combine_datasets()
        
        if combined is not None:
            item = QtGui.QStandardItem(combined.index.name)
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            self.series_list_model.appendRow(item)
            
        self.statusBar().showMessage(self.tr("Ready"), 3000)
        
    def filter_data(self) -> None:
        """过滤数据"""
        if not self.data_service.get_data():
            self.statusBar().showMessage(self.tr("Please load data files"), 3000)
            return
            
        self.statusBar().showMessage(self.tr("Filtering data..."), 3000)
        
        self._read_filter_table()
        
        all_data = self.data_service.get_data()
        filtered_data = self.filter_service.apply_filters_to_all_datasets(all_data)
        
        for index, dataframe in filtered_data.items():
            self.data_service.all_data[index] = dataframe
            
        for index in filtered_data:
            self.data_service.fill_empty_dataset(index)
            
        self._refresh_dataset_list()
        
        self.statusBar().showMessage(self.tr("Ready"), 3000)
        
    def _read_filter_table(self) -> None:
        """读取过滤表"""
        self.statusBar().showMessage(self.tr("Checking filters..."), 3000)
        
        table_data = []
        for row in range(FILTER_TABLE_ROWS):
            item = self.filter_table_widget.item(row, 0)
            if item and item.text():
                param = remove_whitespace(item.text())
                op_item = self.filter_table_widget.item(row, 1)
                val_item = self.filter_table_widget.item(row, 2)
                
                if op_item and val_item:
                    table_data.append([
                        param,
                        remove_whitespace(op_item.text()),
                        remove_whitespace(val_item.text())
                    ])
                    
        self.filter_service.parse_filter_table(table_data)
        
        for row in range(FILTER_TABLE_ROWS):
            for col in range(FILTER_TABLE_COLS):
                if row < len(self.filter_service.filter_conditions):
                    condition = self.filter_service.filter_conditions[row]
                    values = [condition.parameter, condition.operator, condition.value]
                    item = QtWidgets.QTableWidgetItem(str(values[col]))
                else:
                    item = QtWidgets.QTableWidgetItem("")
                self.filter_table_widget.setItem(row, col, item)
                
        self.statusBar().showMessage(self.tr("Ready"), 3000)
        
    def _refresh_dataset_list(self) -> None:
        """刷新数据集列表"""
        self.series_list_model.clear()
        self.series_list_model.setHorizontalHeaderLabels([self.tr('Data series')])
        
        for index, dataframe in self.data_service.get_data().items():
            item = QtGui.QStandardItem(dataframe.index.name)
            self.series_list_model.appendRow(item)
            
    def make_report(self) -> None:
        """生成报告"""
        if not self.data_service.get_data():
            self.statusBar().showMessage(self.tr("Please load data files"), 3000)
            return
            
        report_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            self.tr("Save file"),
            self.file_service.get_previous_directory(),
            "Excel Files (*.xlsx)"
        )
        
        if not report_path:
            return
            
        try:
            self.report_generator.set_report_path(report_path)
            self.statusBar().showMessage(self.tr("Making an Excel report..."), 3000)
            
            yield_loss_data = self.filter_service.get_yield_loss_output(
                self.data_service.get_data()
            )
            
            self.report_generator.generate_report(yield_loss_data)
            self.statusBar().showMessage(self.tr("Ready"), 3000)
            
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            QtWidgets.QMessageBox.about(
                self,
                self.tr("Warning"),
                self.tr("Could not generate report.")
            )
            
    def open_report(self) -> None:
        """打开报告"""
        report_path = self.report_generator.get_report_path()
        
        if not report_path:
            self.statusBar().showMessage(self.tr("No report available"), 3000)
            return
            
        self.statusBar().showMessage(self.tr("Opening report..."), 3000)
        
        try:
            if sys.platform == 'win32':
                os.startfile(report_path)
            elif sys.platform == 'darwin':
                subprocess.call(['open', report_path])
            else:
                subprocess.call(['xdg-open', report_path])
        except Exception as e:
            logger.error(f"打开报告失败: {e}")
            
    def clear_data(self) -> None:
        """清空数据"""
        self.data_service.clear_data()
        self.filter_service = FilterService()
        self.series_list_model.clear()
        self.series_list_model.setHorizontalHeaderLabels([self.tr('Data series')])
        self.statusBar().showMessage(self.tr("Data cleared"), 3000)
        
    def open_plot_selection(self) -> None:
        """打开绘图选择"""
        if not self.data_service.get_data():
            self.statusBar().showMessage(self.tr("Please load data files"), 3000)
            return
            
        selected_plot = self.plot_selection_combo.currentIndex()
        selected_param = self.param_one_combo.currentText()
        
        if self.plot_window and self.plot_window.isWindow():
            self.plot_window.close()
            
        plot_classes = {
            0: lambda: IVBoxPlot(self, selected_param),
            1: lambda: ViolinPlot(self, selected_param),
            2: lambda: CategoryScatter(self, selected_param),
            3: lambda: DistWT(self, selected_param),
            4: lambda: DistRM(self, selected_param),
            5: lambda: DistLtoH(self),
            6: lambda: IVHistPlot(self),
            7: lambda: DensEta(self),
            8: lambda: IVHistDenPlot(self),
            9: lambda: CorrVocIsc(self),
            10: lambda: CorrEtaFF(self),
            11: lambda: CorrRshFF(self),
        }
        
        if selected_plot in plot_classes:
            self.plot_window = plot_classes[selected_plot]()
            self.plot_window.show()
            
        self.statusBar().showMessage(self.tr("Ready"), 3000)
        
    def _set_default_filters(self) -> None:
        """设置默认过滤器"""
        self.filter_table_widget.clearContents()
        
        for row_idx, row_data in enumerate(DEFAULT_FILTERS):
            for col_idx, value in enumerate(row_data):
                item = QtWidgets.QTableWidgetItem(str(value))
                self.filter_table_widget.setItem(row_idx, col_idx, item)
                
    def set_user_filters(self) -> None:
        """设置用户过滤器"""
        self.filter_table_widget.clearContents()
        
        for row_idx, row_data in enumerate(self.user_filters_plain_format):
            for col_idx, value in enumerate(row_data):
                item = QtWidgets.QTableWidgetItem(str(value))
                self.filter_table_widget.setItem(row_idx, col_idx, item)
                
    def load_filter_settings(self) -> None:
        """加载过滤器设置"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.tr("Open file"),
            self.file_service.get_previous_directory(),
            "Filter Settings Files (*.scda)"
        )
        
        if not file_path:
            return
            
        try:
            self.user_filters_plain_format = self.file_service.load_filter_settings(
                file_path
            )
            self.set_user_filters()
            self.statusBar().showMessage(
                self.tr("New filter settings loaded"),
                3000
            )
        except FileFormatError as e:
            QtWidgets.QMessageBox.about(
                self,
                self.tr("Warning"),
                self.tr(f"Could not read file: {e}")
            )
            
    def save_filter_settings(self) -> None:
        """保存过滤器设置"""
        self._read_filter_table()
        
        plain_format = self.filter_service.convert_to_plain_format(
            self.filter_service.filter_conditions
        )
        self.user_filters_plain_format = plain_format
        
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            self.tr("Save file"),
            self.file_service.get_previous_directory(),
            "Description Files (*.scda)"
        )
        
        if not file_path:
            return
            
        try:
            self.file_service.save_filter_settings(file_path, plain_format)
            self.statusBar().showMessage(self.tr("File saved"), 3000)
        except FileFormatError as e:
            QtWidgets.QMessageBox.about(
                self,
                self.tr("Warning"),
                self.tr(f"Could not save file: {e}")
            )
            
    def set_data_format(self, format_index: int) -> None:
        """设置数据格式"""
        self.label_format = format_index
        self.data_service.set_label_format(format_index)
        
        self.statusBar().removeWidget(self.label_text)
        
        format_labels = {
            0: "Data label set A",
            1: "Data label set B",
            2: "Data label set C",
            3: "Data label set D",
            4: "Custom label set"
        }
        
        self.label_text = QtWidgets.QLabel(format_labels.get(format_index, "Unknown"))
        self.statusBar().addPermanentWidget(self.label_text)
        
    def load_custom_labels(self) -> None:
        """加载自定义标签"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.tr("Open file"),
            self.file_service.get_previous_directory(),
            "Label Settings File (*.csv)"
        )
        
        if not file_path:
            return
            
        try:
            labels = self.file_service.load_custom_labels(file_path)
            self.data_service.set_custom_label_format(labels)
            self.set_data_format(4)
            
            QtWidgets.QMessageBox.about(
                self,
                self.tr("Warning"),
                self.tr(f'Data series: {labels}')
            )
            
        except FileFormatError as e:
            QtWidgets.QMessageBox.about(
                self,
                self.tr("Warning"),
                self.tr(f"Could not read file: {e}")
            )
            
    def lang_korean(self) -> None:
        """切换韩语"""
        if self.translator:
            QtWidgets.QApplication.removeTranslator(self.translator)
            
        self.translator = QtCore.QTranslator()
        self.translator.load(":IVMain_kr.qm")
        QtWidgets.QApplication.installTranslator(self.translator)
        self._retranslate_ui()
        
    def lang_chinese(self) -> None:
        """切换中文"""
        if self.translator:
            QtWidgets.QApplication.removeTranslator(self.translator)
            
        self.translator = QtCore.QTranslator()
        self.translator.load(":IVMain_cn.qm")
        QtWidgets.QApplication.installTranslator(self.translator)
        self._retranslate_ui()
        
    def lang_english(self) -> None:
        """切换英语"""
        if self.translator:
            QtWidgets.QApplication.removeTranslator(self.translator)
            
        self._retranslate_ui()
        
    def _retranslate_ui(self) -> None:
        """重新翻译 UI"""
        self.menuBar().clear()
        self._create_menu()
        self.param_one_combo.clear()
        self.plot_selection_combo.clear()
        self.main_frame.deleteLater()
        self._create_main_frame()
        
    def open_help_dialog(self) -> None:
        """打开帮助对话框"""
        help_dialog = HelpDialog(self)
        help_dialog.setModal(True)
        help_dialog.show()
        
    def on_about(self) -> None:
        """关于对话框"""
        QtWidgets.QMessageBox.about(
            self,
            self.tr("About the application"),
            self.tr("Solar cell data analysis\nAuthor: Ronald Naber\nLicense: Public domain")
        )
        
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """键盘事件处理"""
        if event.modifiers() & QtCore.Qt.ControlModifier:
            selected = self.filter_table_widget.selectedRanges()
            
            if not selected:
                return
                
            if event.key() == QtCore.Qt.Key_V:
                self._paste_to_table(selected[0])
            elif event.key() == QtCore.Qt.Key_C:
                self._copy_from_table(selected[0])
                
    def _paste_to_table(self, selection) -> None:
        """粘贴到表格"""
        first_row = selection.topRow()
        first_col = selection.leftColumn()
        
        for row_idx, row_text in enumerate(self.clipboard.text().split('\n')):
            for col_idx, text in enumerate(row_text.split('\t')):
                if text:
                    self.filter_table_widget.setItem(
                        first_row + row_idx,
                        first_col + col_idx,
                        QtWidgets.QTableWidgetItem(text)
                    )
                    
    def _copy_from_table(self, selection) -> None:
        """从表格复制"""
        text = ""
        for row in range(selection.topRow(), selection.bottomRow() + 1):
            for col in range(selection.leftColumn(), selection.rightColumn() + 1):
                try:
                    text += str(self.filter_table_widget.item(row, col).text()) + "\t"
                except AttributeError:
                    text += "\t"
            text = text[:-1] + "\n"
            
        self.clipboard.setText(text)
        
    def _create_main_frame(self) -> None:
        """创建主框架"""
        self.setWindowTitle(self.tr("Solar cell data analysis"))
        self.main_frame = QtWidgets.QWidget()
        
        left_layout = self._create_left_panel()
        middle_layout = self._create_middle_panel()
        top_layout = self._create_top_panel()
        
        main_hbox = QtWidgets.QHBoxLayout()
        main_hbox.addLayout(left_layout)
        main_hbox.addLayout(middle_layout)
        
        main_vbox = QtWidgets.QVBoxLayout()
        main_vbox.addLayout(top_layout)
        main_vbox.addLayout(main_hbox)
        
        self.main_frame.setLayout(main_vbox)
        self.setCentralWidget(self.main_frame)
        
        self.statusBar().addWidget(self.status_text, 1)
        
        if self.first_run:
            self.statusBar().removeWidget(self.label_text)
            self.first_run = False
            
        self.statusBar().addPermanentWidget(self.label_text)
        
    def _create_left_panel(self) -> QtWidgets.QVBoxLayout:
        """创建左侧面板"""
        self.series_list_view = QtWidgets.QTreeView()
        self.series_list_view.setModel(self.series_list_model)
        self.series_list_model.setHorizontalHeaderLabels([self.tr('Data series')])
        self.series_list_view.setRootIsDecorated(False)
        self.series_list_view.setDragDropMode(QtWidgets.QAbstractItemView.NoDragDrop)
        self.series_list_view.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        
        open_button = QtWidgets.QPushButton()
        open_button.clicked.connect(self.load_file)
        open_button.setIcon(QtGui.QIcon(":open.png"))
        open_button.setToolTip(self.tr("Load files"))
        open_button.setStatusTip(self.tr("Load files"))
        
        save_button = QtWidgets.QPushButton()
        save_button.clicked.connect(self.save_files)
        save_button.setIcon(QtGui.QIcon(":save.png"))
        save_button.setToolTip(self.tr("Save files"))
        save_button.setStatusTip(self.tr("Save files"))
        
        combine_button = QtWidgets.QPushButton()
        combine_button.clicked.connect(self.combine_datasets)
        combine_button.setIcon(QtGui.QIcon(":combine.png"))
        combine_button.setToolTip(self.tr("Combine data sets"))
        combine_button.setStatusTip(self.tr("Combine data sets"))
        
        clear_button = QtWidgets.QPushButton()
        clear_button.clicked.connect(self.clear_data)
        clear_button.setIcon(QtGui.QIcon(":erase.png"))
        clear_button.setToolTip(self.tr("Remove all data sets"))
        clear_button.setStatusTip(self.tr("Remove all data sets"))
        
        button_box = QtWidgets.QDialogButtonBox()
        button_box.addButton(open_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(save_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(combine_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(clear_button, QtWidgets.QDialogButtonBox.ActionRole)
        
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.series_list_view)
        layout.addWidget(button_box)
        
        return layout
        
    def _create_middle_panel(self) -> QtWidgets.QVBoxLayout:
        """创建中间面板"""
        self.filter_table_widget.setRowCount(FILTER_TABLE_ROWS)
        self.filter_table_widget.setColumnCount(FILTER_TABLE_COLS)
        self.filter_table_widget.setHorizontalHeaderLabels(
            (self.tr('Parameter'), self.tr('< or >'), self.tr('Number'))
        )
        self.filter_table_widget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )
        self.filter_table_widget.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )
        
        open_filter_button = QtWidgets.QPushButton()
        open_filter_button.clicked.connect(self.load_filter_settings)
        open_filter_button.setIcon(QtGui.QIcon(":open.png"))
        open_filter_button.setToolTip(self.tr("Load filter settings"))
        open_filter_button.setStatusTip(self.tr("Load filter settings"))
        
        save_filter_button = QtWidgets.QPushButton()
        save_filter_button.clicked.connect(self.save_filter_settings)
        save_filter_button.setIcon(QtGui.QIcon(":save.png"))
        save_filter_button.setToolTip(self.tr("Save filter settings"))
        save_filter_button.setStatusTip(self.tr("Save filter settings"))
        
        check_button = QtWidgets.QPushButton()
        check_button.clicked.connect(self._read_filter_table)
        check_button.setIcon(QtGui.QIcon(":check.png"))
        check_button.setToolTip(self.tr("Check filters"))
        check_button.setStatusTip(self.tr("Check filters"))
        
        execute_button = QtWidgets.QPushButton()
        execute_button.clicked.connect(self.filter_data)
        execute_button.setIcon(QtGui.QIcon(":filter.png"))
        execute_button.setToolTip(self.tr("Execute filters"))
        execute_button.setStatusTip(self.tr("Execute filters"))
        
        default_button = QtWidgets.QPushButton()
        default_button.clicked.connect(self._set_default_filters)
        default_button.setIcon(QtGui.QIcon(":revert.png"))
        default_button.setToolTip(self.tr("Reload default filters"))
        default_button.setStatusTip(self.tr("Reload default filters"))
        
        button_box = QtWidgets.QDialogButtonBox()
        button_box.addButton(open_filter_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(save_filter_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(check_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(execute_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(default_button, QtWidgets.QDialogButtonBox.ActionRole)
        
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.filter_table_widget)
        layout.addWidget(button_box)
        
        return layout
        
    def _create_top_panel(self) -> QtWidgets.QHBoxLayout:
        """创建顶部面板"""
        report_button = QtWidgets.QPushButton()
        report_button.clicked.connect(self.make_report)
        report_button.setIcon(QtGui.QIcon(":report.png"))
        report_button.setToolTip(self.tr("Make report"))
        report_button.setStatusTip(self.tr("Make report"))
        
        open_report_button = QtWidgets.QPushButton()
        open_report_button.clicked.connect(self.open_report)
        open_report_button.setIcon(QtGui.QIcon(":link.png"))
        open_report_button.setToolTip(self.tr("Open report"))
        open_report_button.setStatusTip(self.tr("Open report"))
        
        plot_button = QtWidgets.QPushButton()
        plot_button.clicked.connect(self.open_plot_selection)
        plot_button.setIcon(QtGui.QIcon(":chart.png"))
        plot_button.setToolTip(self.tr("Plot selection"))
        plot_button.setStatusTip(self.tr("Plot selection"))
        
        button_box = QtWidgets.QDialogButtonBox()
        button_box.addButton(report_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(open_report_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(plot_button, QtWidgets.QDialogButtonBox.ActionRole)
        
        for param in PLOT_PARAMETERS:
            self.param_one_combo.addItem(param)
        self.param_one_combo.setCurrentIndex(4)
        
        for plot_type in PLOT_SELECTION_COMBO_LIST:
            self.plot_selection_combo.addItem(plot_type)
            
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(button_box)
        layout.addWidget(self.param_one_combo)
        layout.addWidget(self.plot_selection_combo)
        
        return layout
        
    def _create_menu(self) -> None:
        """创建菜单"""
        self._create_file_menu()
        self._create_edit_menu()
        self._create_language_menu()
        self._create_help_menu()
        
    def _create_file_menu(self) -> None:
        """创建文件菜单"""
        file_menu = self.menuBar().addMenu(self.tr("File"))
        
        load_action = QtWidgets.QAction(self.tr("Open..."), self)
        load_action.setIcon(QtGui.QIcon(":open.png"))
        load_action.triggered.connect(self.load_file)
        load_action.setToolTip(self.tr("Open file"))
        load_action.setStatusTip(self.tr("Open file"))
        load_action.setShortcut('Ctrl+O')
        
        save_action = QtWidgets.QAction(self.tr("Save..."), self)
        save_action.setIcon(QtGui.QIcon(":save.png"))
        save_action.triggered.connect(self.save_files)
        save_action.setToolTip(self.tr("Save files"))
        save_action.setStatusTip(self.tr("Save files"))
        
        combine_action = QtWidgets.QAction(self.tr("Combine"), self)
        combine_action.setIcon(QtGui.QIcon(":combine.png"))
        combine_action.triggered.connect(self.combine_datasets)
        combine_action.setToolTip(self.tr("Combine data sets"))
        combine_action.setStatusTip(self.tr("Combine data sets"))
        
        clear_action = QtWidgets.QAction(self.tr("Clear"), self)
        clear_action.setIcon(QtGui.QIcon(":erase.png"))
        clear_action.triggered.connect(self.clear_data)
        clear_action.setToolTip(self.tr("Remove all data sets"))
        clear_action.setStatusTip(self.tr("Remove all data sets"))
        
        quit_action = QtWidgets.QAction(self.tr("Quit"), self)
        quit_action.setIcon(QtGui.QIcon(":quit.png"))
        quit_action.triggered.connect(self.close)
        quit_action.setToolTip(self.tr("Quit"))
        quit_action.setStatusTip(self.tr("Quit"))
        quit_action.setShortcut('Ctrl+Q')
        
        file_menu.addAction(load_action)
        file_menu.addAction(save_action)
        file_menu.addAction(combine_action)
        file_menu.addAction(clear_action)
        file_menu.addSeparator()
        file_menu.addAction(quit_action)
        
    def _create_edit_menu(self) -> None:
        """创建编辑菜单"""
        edit_menu = self.menuBar().addMenu(self.tr("Edit"))
        
        format_actions = [
            ("Data label set A", 0, ":label.png"),
            ("Data label set B", 1, ":label.png"),
            ("Data label set C", 2, ":label.png"),
            ("Data label set D", 3, ":label.png"),
            ("Custom labels", None, ":label.png"),
        ]
        
        for label, format_idx, icon in format_actions:
            action = QtWidgets.QAction(self.tr(label), self)
            action.setIcon(QtGui.QIcon(icon))
            
            if format_idx is not None:
                action.triggered.connect(
                    lambda checked, idx=format_idx: self.set_data_format(idx)
                )
            else:
                action.triggered.connect(self.load_custom_labels)
                
            action.setToolTip(self.tr(label))
            action.setStatusTip(self.tr(label))
            edit_menu.addAction(action)
            
    def _create_language_menu(self) -> None:
        """创建语言菜单"""
        lang_menu = self.menuBar().addMenu(self.tr("Language"))
        
        cn_action = QtWidgets.QAction(self.tr("Chinese"), self)
        cn_action.setIcon(QtGui.QIcon(":lang.png"))
        cn_action.triggered.connect(self.lang_chinese)
        cn_action.setToolTip(self.tr("Switch to Chinese language"))
        cn_action.setStatusTip(self.tr("Switch to Chinese language"))
        
        kr_action = QtWidgets.QAction(self.tr("Korean"), self)
        kr_action.setIcon(QtGui.QIcon(":lang.png"))
        kr_action.triggered.connect(self.lang_korean)
        kr_action.setToolTip(self.tr("Switch to Korean language"))
        kr_action.setStatusTip(self.tr("Switch to Korean language"))
        
        en_action = QtWidgets.QAction(self.tr("English"), self)
        en_action.setIcon(QtGui.QIcon(":lang.png"))
        en_action.triggered.connect(self.lang_english)
        en_action.setToolTip(self.tr("Switch to English language"))
        en_action.setStatusTip(self.tr("Switch to English language"))
        
        lang_menu.addAction(cn_action)
        lang_menu.addAction(kr_action)
        lang_menu.addAction(en_action)
        
    def _create_help_menu(self) -> None:
        """创建帮助菜单"""
        help_menu = self.menuBar().addMenu(self.tr("Help"))
        
        help_action = QtWidgets.QAction(self.tr("Help..."), self)
        help_action.setIcon(QtGui.QIcon(":help.png"))
        help_action.triggered.connect(self.open_help_dialog)
        help_action.setToolTip(self.tr("Help information"))
        help_action.setStatusTip(self.tr("Help information"))
        help_action.setShortcut('H')
        
        about_action = QtWidgets.QAction(self.tr("About..."), self)
        about_action.setIcon(QtGui.QIcon(":info.png"))
        about_action.triggered.connect(self.on_about)
        about_action.setToolTip(self.tr("About the application"))
        about_action.setStatusTip(self.tr("About the application"))
        about_action.setShortcut('F1')
        
        help_menu.addAction(help_action)
        help_menu.addAction(about_action)
