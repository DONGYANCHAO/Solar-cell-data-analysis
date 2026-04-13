# -*- coding: utf-8 -*-
import os
import pickle
from typing import Dict, List, Optional
from PyQt5 import QtCore, QtGui, QtWidgets

from HelpDialog import HelpDialog
from plots import (
    IVBoxPlot, ViolinPlot, CategoryScatter, DistWT, DistRM,
    DistLtoH, IVHistPlot, DensEta, IVHistDenPlot,
    CorrVocIsc, CorrEtaFF, CorrRshFF
)
from config import (
    WindowSize, FontSettings, DataParameters, DataLabelFormat,
    FilterConfig, PlotSelection, FileExtensions, Messages, WindowConfig,
    ConversionFactors, SummaryConfig
)
from logger import get_logger, validate_ascii_filename
from services import DataService, FileService, FilterService, ReportGenerator


class IVMainGui(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(IVMainGui, self).__init__(parent)
        self.logger = get_logger('IVMainGui')
        
        self._initialize_services()
        self._setup_window()
        self._initialize_ui_state()
        self.create_menu()
        self.create_main_frame()
        self.set_default_filters()
        
    def _initialize_services(self) -> None:
        self.data_service = DataService()
        self.file_service = FileService(self.data_service)
        self.filter_service = FilterService()
        self.report_generator = ReportGenerator()
        
    def _setup_window(self) -> None:
        self.setWindowTitle(self.tr(WindowConfig.TITLE))
        self.setWindowIcon(QtGui.QIcon(":ScidaPro_icon.png"))
        
        self.resize(WindowSize.WIDTH, WindowSize.HEIGHT)
        frame_geometry = self.frameGeometry()
        center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())
        
        self.setStyleSheet(f'font-size: {FontSettings.SIZE}pt;')
        
    def _initialize_ui_state(self) -> None:
        self.clipboard = QtWidgets.QApplication.clipboard()
        self.series_list_model = QtGui.QStandardItemModel()
        self.series_list_model.itemChanged.connect(self._on_dataset_rename)
        
        self.filter_table_widget = QtWidgets.QTableWidget()
        self.default_filters = FilterConfig.DEFAULT_FILTERS
        
        self.label_formats = DataParameters.LABEL_FORMATS.copy()
        self.label_format = DataLabelFormat.FORMAT_A.value
        
        self.label_text = QtWidgets.QLabel("Data label set A")
        self.status_text = QtWidgets.QLabel("")
        self.first_run = True
        
        self.yield_loss_tables: List = []
        self.summary_tables: List = []
        self.correlation_tables: List = []
        self.current_report_path = ''
        self.yield_loss_output: List = []
        self.translator = None
        
        self.plot_parameter_list = PlotSelection.PARAMETER_LIST
        self.plot_type_list = PlotSelection.TYPE_LIST
        
        self.parameter_combo_box = QtWidgets.QComboBox(self)
        self.plot_type_combo_box = QtWidgets.QComboBox(self)
        self.plot_type_combo_box.currentIndexChanged.connect(self._on_plot_type_changed)
        
        self.plot_window = None
        
    def _on_plot_type_changed(self, index: int) -> None:
        if index < 3:
            self.parameter_combo_box.setEnabled(True)
        elif 2 < index < 7:
            self.parameter_combo_box.setCurrentIndex(4)
            self.parameter_combo_box.setDisabled(True)
        else:
            self.parameter_combo_box.setDisabled(True)
            
    def _on_dataset_rename(self, item: QtGui.QStandardItem) -> None:
        entered_name = str(item.text())
        keep_characters = (' ', '.', '_')
        valid_filename = "".join(c for c in entered_name if c.isalnum() or c in keep_characters).rstrip()

        if len(valid_filename) > 0:
            row_index = self.series_list_model.indexFromItem(item).row()
            if self.data_service.dataset_exists(row_index):
                self.data_service.rename_dataset(row_index, valid_filename)
                item.setText(valid_filename)
        else:
            row_index = self.series_list_model.indexFromItem(item).row()
            dataset_name = self.data_service.get_dataset_name(row_index)
            if dataset_name:
                item.setText(dataset_name)

    def load_file(self, filename=None) -> None:
        file_paths = QtWidgets.QFileDialog.getOpenFileNames(
            self, self.tr("Load files"), 
            self.file_service.get_previous_directory(), 
            FileExtensions.EXCEL_FILTER
        )
        file_paths = file_paths[0]
        
        if not file_paths:
            return
        
        empty_data_warning, non_ascii_warning, read_error_warning = \
            self.file_service.load_data_files(file_paths)
        
        for dataset_id in self.data_service.get_sorted_dataset_ids():
            dataset_name = self.data_service.get_dataset_name(dataset_id)
            if dataset_name:
                item = QtGui.QStandardItem(dataset_name)
                font = item.font()
                font.setBold(1)
                item.setFont(font)
                self.series_list_model.appendRow(item)
        
        if read_error_warning:
            QtWidgets.QMessageBox.about(self, self.tr("Warning"), self.tr(Messages.ERROR_READ_DATA))

        if empty_data_warning:
            QtWidgets.QMessageBox.about(self, self.tr("Warning"), self.tr(Messages.ERROR_EMPTY_DATA))
            
        if non_ascii_warning:
            QtWidgets.QMessageBox.about(self, self.tr("Warning"), self.tr(Messages.ERROR_NON_ASCII))
                              
        if self.data_service.get_dataset_count() > 0:
            self.statusBar().showMessage(self.tr(Messages.STATUS_READY), 3000)
        else:
            self.statusBar().showMessage(self.tr(Messages.STATUS_LOAD_FILES), 3000)

    def save_files(self) -> None:
        dest_dir = QtWidgets.QFileDialog.getExistingDirectory(
            None, self.tr('Open directory'), 
            self.file_service.get_previous_directory(), 
            QtWidgets.QFileDialog.ShowDirsOnly
        )
        
        if not dest_dir:
            return
        
        datasets = self.data_service.get_all_datasets()
        if len(datasets) == 0:
            self.statusBar().showMessage(self.tr(Messages.STATUS_LOAD_FILES), 3000)
            return

        def overwrite_callback(filename, directory):
            reply = QtWidgets.QMessageBox.question(
                self, self.tr("Message"), 
                f"Overwrite '{filename}'?",
                QtWidgets.QMessageBox.YesToAll | QtWidgets.QMessageBox.Yes | 
                QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel, 
                QtWidgets.QMessageBox.No
            )

            if reply == QtWidgets.QMessageBox.No:
                save_path = QtWidgets.QFileDialog.getSaveFileName(
                    self, self.tr("Save file"), 
                    directory, FileExtensions.CSV_FILTER
                )
                return save_path[0] if save_path else None

            if reply == QtWidgets.QMessageBox.YesToAll:
                return 'yes_to_all'
                
            if reply == QtWidgets.QMessageBox.Cancel:
                return 'cancel'
            
            return None

        self.file_service.save_datasets_to_directory(datasets, dest_dir, overwrite_callback)
        self.statusBar().showMessage(self.tr(Messages.STATUS_FILES_SAVED), 3000)
                   
    def combine_datasets(self) -> None:
        datasets = self.data_service.get_all_datasets()
        
        if len(datasets) > 1:
            self.statusBar().showMessage(self.tr(Messages.STATUS_COMBINING), 3000)
        else:
            self.statusBar().showMessage(self.tr(Messages.STATUS_LOAD_FILES), 3000)
            return

        self.yield_loss_tables = []
        self.yield_loss_output = []
        self.summary_tables = []
        self.series_list_model.clear()
        self.series_list_model.setHorizontalHeaderLabels([self.tr('Data series')])

        self.data_service.combine_datasets()

        combined_name = self.data_service.get_dataset_name(0)
        if combined_name:
            item = QtGui.QStandardItem(combined_name)
            font = item.font()
            font.setBold(1)
            item.setFont(font)
            self.series_list_model.appendRow(item)
                
        self.statusBar().showMessage(self.tr(Messages.STATUS_READY), 3000)

    def clear_data(self) -> None:
        self.data_service.clear_all_datasets()
        self.yield_loss_tables = []
        self.yield_loss_output = []
        self.summary_tables = []
        self.correlation_tables = []
        self.series_list_model.clear()
        self.series_list_model.setHorizontalHeaderLabels([self.tr('Data series')])
        self.statusBar().showMessage(self.tr("All data has been cleared"), 3000)

    def filter_data(self) -> None:
        datasets = self.data_service.get_all_datasets()
        
        if datasets:
            self.statusBar().showMessage(self.tr(Messages.STATUS_FILTERING), 3000)
        else:
            self.statusBar().showMessage(self.tr(Messages.STATUS_LOAD_FILES), 3000)
            return

        self._read_filter_table()
        
        datasets = self.filter_service.apply_filters(datasets)
        self.data_service.datasets = datasets
        
        self.yield_loss_tables = self.filter_service.get_yield_loss_tables()

        self.series_list_model.clear()
        self.series_list_model.setHorizontalHeaderLabels([self.tr('Data series')])

        for dataset_id in self.data_service.get_sorted_dataset_ids():
            dataset_name = self.data_service.get_dataset_name(dataset_id)
            if dataset_name:
                item = QtGui.QStandardItem(dataset_name)
                self.series_list_model.appendRow(item)

        self.statusBar().showMessage(self.tr(Messages.STATUS_READY), 3000)

    def make_report(self) -> None:
        datasets = self.data_service.get_all_datasets()
        
        if not datasets:
            self.statusBar().showMessage(self.tr(Messages.STATUS_LOAD_FILES), 3000)
            return

        self.current_report_path = QtWidgets.QFileDialog.getSaveFileName(
            self, self.tr("Save file"), 
            self.file_service.get_previous_directory(), 
            FileExtensions.XLSX_FILTER
        )
        self.current_report_path = self.current_report_path[0]
        
        if not self.current_report_path:
            return

        self.statusBar().showMessage(self.tr(Messages.STATUS_MAKING_REPORT), 3000)

        if not validate_ascii_filename(self.current_report_path):
            QtWidgets.QMessageBox.about(self, self.tr("Warning"), self.tr(Messages.ERROR_NON_ASCII))
            self.current_report_path = ''
            return
                        
        try:
            self.report_generator.generate_report(
                self.current_report_path,
                datasets,
                self.yield_loss_tables,
                self.tr
            )
            self.statusBar().showMessage(self.tr(Messages.STATUS_READY), 3000)
        except Exception as e:
            self.logger.error(f"Report generation failed: {str(e)}")
            QtWidgets.QMessageBox.about(self, self.tr("Warning"), str(e))

    def open_report(self) -> None:
        if len(self.current_report_path):
            self.statusBar().showMessage(self.tr(Messages.STATUS_OPENING_REPORT), 3000)
            if self.current_report_path[0] != '/':
                os.startfile(self.current_report_path)
            else:
                os.system('xdg-open "' + self.current_report_path + '"')
            self.statusBar().showMessage(self.tr(Messages.STATUS_READY), 3000)
        else:
            self.statusBar().showMessage(self.tr("Please make a report first"), 3000)

    def open_plot_selection(self) -> None:
        selected_plot_index = self.plot_type_combo_box.currentIndex()
        
        datasets = self.data_service.get_all_datasets()
        if not datasets:
            self.statusBar().showMessage(self.tr(Messages.STATUS_LOAD_FILES), 3000)
            return

        if self.plot_window:
            if self.plot_window.isWindow():
                self.plot_window.close()

        plot_factories = {
            0: lambda: IVBoxPlot(self, self.parameter_combo_box.currentText()),
            1: lambda: ViolinPlot(self, self.parameter_combo_box.currentText()),
            2: lambda: CategoryScatter(self, self.parameter_combo_box.currentText()),
            3: lambda: DistWT(self, self.parameter_combo_box.currentText()),
            4: lambda: DistRM(self, self.parameter_combo_box.currentText()),
            5: lambda: DistLtoH(self),
            6: lambda: IVHistPlot(self),
            7: lambda: DensEta(self),
            8: lambda: IVHistDenPlot(self),
            9: lambda: CorrVocIsc(self),
            10: lambda: CorrEtaFF(self),
            11: lambda: CorrRshFF(self),
        }

        if selected_plot_index in plot_factories:
            self.plot_window = plot_factories[selected_plot_index]()
            self.plot_window.show()
            self.statusBar().showMessage(self.tr(Messages.STATUS_READY), 3000)

    def set_default_filters(self) -> None:
        self.filter_table_widget.clearContents()

        for row_idx, row in enumerate(self.default_filters):
            for col_idx, value in enumerate(row):
                item = QtWidgets.QTableWidgetItem(str(value))
                self.filter_table_widget.setItem(row_idx, col_idx, item)

    def set_user_filters(self, filters: List[List]) -> None:
        self.filter_table_widget.clearContents()

        for row_idx, row in enumerate(filters):
            for col_idx, value in enumerate(row):
                item = QtWidgets.QTableWidgetItem(str(value))
                self.filter_table_widget.setItem(row_idx, col_idx, item)

    def load_filter_settings(self) -> None:
        file_path = QtWidgets.QFileDialog.getOpenFileName(
            self, self.tr("Open file"), 
            self.file_service.get_previous_directory(), 
            FileExtensions.SCDA_FILTER
        )
        file_path = file_path[0]
        
        if not file_path:
            return

        if not validate_ascii_filename(file_path):
            QtWidgets.QMessageBox.about(self, self.tr("Warning"), self.tr(Messages.ERROR_NON_ASCII))
            return
        
        try:
            filters = self.file_service.load_filter_settings(file_path)
            self.set_user_filters(filters)
            self.statusBar().showMessage(self.tr(Messages.STATUS_NEW_FILTERS_LOADED), 3000)
        except Exception as e:
            self.logger.error(f"Could not read filter settings: {str(e)}")
            QtWidgets.QMessageBox.about(
                self, self.tr("Warning"), 
                self.tr(f"Could not read file \"{os.path.basename(file_path)}\"")
            )

    def save_filter_settings(self) -> None:
        self._read_filter_table()
        filters = self.filter_service.get_filters_plain()

        file_path = QtWidgets.QFileDialog.getSaveFileName(
            self, self.tr("Save file"), 
            self.file_service.get_previous_directory(), 
            "Description Files (*.scda)"
        )
        file_path = file_path[0]
        
        if not file_path:
            return

        if not validate_ascii_filename(file_path):
            QtWidgets.QMessageBox.about(self, self.tr("Warning"), self.tr(Messages.ERROR_NON_ASCII))
            return
        
        try:
            self.file_service.save_filter_settings(file_path, filters)
            self.statusBar().showMessage(self.tr(Messages.STATUS_FILES_SAVED), 3000)
        except Exception as e:
            self.logger.error(f"Could not save filter settings: {str(e)}")
            QtWidgets.QMessageBox.about(
                self, self.tr("Warning"), 
                self.tr(f"Could not save file \"{os.path.basename(file_path)}\"")
            )

    def _read_filter_table(self) -> None:
        self.statusBar().showMessage(self.tr(Messages.STATUS_CHECKING_FILTERS), 3000)
        
        table_data = []
        for row_idx in range(FilterConfig.MAX_FILTERS):
            row = []
            for col_idx in range(3):
                item = self.filter_table_widget.item(row_idx, col_idx)
                row.append(item.text() if item else "")
            table_data.append(row)
        
        self.filter_service.set_filters_from_table(table_data)
        
        filters = self.filter_service.get_filters_as_list()
        
        self.filter_table_widget.clearContents()
        for row_idx, filter_item in enumerate(filters):
            for col_idx, value in enumerate(filter_item):
                item = QtWidgets.QTableWidgetItem(str(value))
                self.filter_table_widget.setItem(row_idx, col_idx, item)

        self.statusBar().showMessage(self.tr(Messages.STATUS_READY), 3000)

    def keyPressEvent(self, event) -> None:
        if event.modifiers() & QtCore.Qt.ControlModifier:
            selected = self.filter_table_widget.selectedRanges()
                 
            if event.key() == QtCore.Qt.Key_V:
                first_row = selected[0].topRow()
                first_col = selected[0].leftColumn()
                 
                for row_idx, row in enumerate(self.clipboard.text().split('\n')):
                    for col_idx, text in enumerate(row.split('\t')):
                        if len(text):
                            self.filter_table_widget.setItem(
                                first_row + row_idx, first_col + col_idx, 
                                QtWidgets.QTableWidgetItem(text)
                            )
 
            elif event.key() == QtCore.Qt.Key_C:
                copied_text = ""
                for row_idx in range(selected[0].topRow(), selected[0].bottomRow() + 1):
                    for col_idx in range(selected[0].leftColumn(), selected[0].rightColumn() + 1):
                        try:
                            copied_text += str(self.filter_table_widget.item(row_idx, col_idx).text()) + "\t"
                        except AttributeError:
                            copied_text += "\t"
                    copied_text = copied_text[:-1] + "\n"
                self.clipboard.setText(copied_text)

    def set_data_format_a(self) -> None:
        self.label_format = DataLabelFormat.FORMAT_A.value
        self.data_service.set_label_format(DataLabelFormat.FORMAT_A.value)
        self._update_label_text("Data label set A")

    def set_data_format_b(self) -> None:
        self.label_format = DataLabelFormat.FORMAT_B.value
        self.data_service.set_label_format(DataLabelFormat.FORMAT_B.value)
        self._update_label_text("Data label set B")

    def set_data_format_c(self) -> None:
        self.label_format = DataLabelFormat.FORMAT_C.value
        self.data_service.set_label_format(DataLabelFormat.FORMAT_C.value)
        self._update_label_text("Data label set C")

    def set_data_format_d(self) -> None:
        self.label_format = DataLabelFormat.FORMAT_D.value
        self.data_service.set_label_format(DataLabelFormat.FORMAT_D.value)
        self._update_label_text("Data label set D")

    def set_data_format_custom(self) -> None:
        file_path = QtWidgets.QFileDialog.getOpenFileName(
            self, self.tr("Open file"), 
            self.file_service.get_previous_directory(), 
            FileExtensions.LABEL_FILTER
        )
        file_path = file_path[0]
        
        if not file_path:
            return

        if not validate_ascii_filename(file_path):
            QtWidgets.QMessageBox.about(self, self.tr("Warning"), self.tr(Messages.ERROR_NON_ASCII))
            return
        
        try:
            labels = self.file_service.load_custom_labels(file_path)
            self.label_formats[4] = labels
            self.label_format = DataLabelFormat.FORMAT_CUSTOM.value
            self.data_service.set_label_format(DataLabelFormat.FORMAT_CUSTOM.value)

            QtWidgets.QMessageBox.about(
                self, self.tr("Warning"), 
                self.tr('Data series') + ": " + str(labels)
            )

            self.statusBar().showMessage(self.tr(Messages.STATUS_READY), 3000)
            self._update_label_text("Custom label set")
        except Exception as e:
            self.logger.error(f"Could not read custom labels: {str(e)}")
            QtWidgets.QMessageBox.about(
                self, self.tr("Warning"), 
                self.tr(f"Could not read file \"{os.path.basename(file_path)}\"")
            )

    def _update_label_text(self, text: str) -> None:
        self.statusBar().removeWidget(self.label_text)
        self.label_text = QtWidgets.QLabel(text)
        self.statusBar().addPermanentWidget(self.label_text)

    def switch_to_korean(self) -> None:
        if self.translator:
            QtWidgets.QApplication.removeTranslator(self.translator)
        
        self.translator = QtCore.QTranslator()
        self.translator.load(":IVMain_kr.qm")
        QtWidgets.QApplication.installTranslator(self.translator)

        self._refresh_ui()

    def switch_to_chinese(self) -> None:
        if self.translator:
            QtWidgets.QApplication.removeTranslator(self.translator)
        
        self.translator = QtCore.QTranslator()
        self.translator.load(":IVMain_cn.qm")
        QtWidgets.QApplication.installTranslator(self.translator)

        self._refresh_ui()

    def switch_to_english(self) -> None:
        if self.translator:
            QtWidgets.QApplication.removeTranslator(self.translator)

        self._refresh_ui()

    def _refresh_ui(self) -> None:
        self.menuBar().clear()
        self.create_menu()
        self.parameter_combo_box.clear()
        self.plot_type_combo_box.clear()
        self.main_frame.deleteLater()
        self.create_main_frame()

    def open_help_dialog(self) -> None:
        help_dialog = HelpDialog(self)
        help_dialog.setModal(True)
        help_dialog.show()

    def on_about(self) -> None:
        QtWidgets.QMessageBox.about(self, self.tr("About the application"), self.tr(WindowConfig.ABOUT_TEXT))

    def create_main_frame(self) -> None:
        self.setWindowTitle(self.tr("Solar cell data analysis"))
        self.main_frame = QtWidgets.QWidget()

        left_panel = self._create_left_panel()
        middle_panel = self._create_middle_panel()
        toolbar = self._create_toolbar()

        top_layout = QtWidgets.QHBoxLayout()
        top_layout.addLayout(left_panel)
        top_layout.addLayout(middle_panel)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(toolbar)
        main_layout.addLayout(top_layout)

        self.main_frame.setLayout(main_layout)
        self.setCentralWidget(self.main_frame)

        self.statusBar().addWidget(self.status_text, 1)

        if self.first_run:
            self.statusBar().removeWidget(self.label_text)
            self.first_run = False

        self.statusBar().addPermanentWidget(self.label_text)

    def _create_left_panel(self) -> QtWidgets.QVBoxLayout:
        self.series_list_view = QtWidgets.QTreeView()
        self.series_list_view.setModel(self.series_list_model)
        self.series_list_model.setHorizontalHeaderLabels([self.tr('Data series')])
        self.series_list_view.setRootIsDecorated(False)
        self.series_list_view.setDragDropMode(QtWidgets.QAbstractItemView.NoDragDrop)
        self.series_list_view.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

        open_files_button = QtWidgets.QPushButton()
        open_files_button.clicked.connect(self.load_file)
        open_files_button.setIcon(QtGui.QIcon(":open.png"))
        open_files_button.setToolTip(self.tr("Load files"))
        open_files_button.setStatusTip(self.tr("Load files"))

        save_files_button = QtWidgets.QPushButton()
        save_files_button.clicked.connect(self.save_files)
        save_files_button.setIcon(QtGui.QIcon(":save.png"))
        save_files_button.setToolTip(self.tr("Save files"))
        save_files_button.setStatusTip(self.tr("Save files"))

        combine_data_button = QtWidgets.QPushButton()
        combine_data_button.clicked.connect(self.combine_datasets)
        combine_data_button.setIcon(QtGui.QIcon(":combine.png"))
        combine_data_button.setToolTip(self.tr("Combine data sets"))
        combine_data_button.setStatusTip(self.tr("Combine data sets"))

        clear_data_button = QtWidgets.QPushButton()
        clear_data_button.clicked.connect(self.clear_data)
        clear_data_button.setIcon(QtGui.QIcon(":erase.png"))
        clear_data_button.setToolTip(self.tr("Remove all data sets"))
        clear_data_button.setStatusTip(self.tr("Remove all data sets"))

        button_box = QtWidgets.QDialogButtonBox()
        button_box.addButton(open_files_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(save_files_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(combine_data_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(clear_data_button, QtWidgets.QDialogButtonBox.ActionRole)

        left_panel = QtWidgets.QVBoxLayout()
        left_panel.addWidget(self.series_list_view)
        left_panel.addWidget(button_box)

        return left_panel

    def _create_middle_panel(self) -> QtWidgets.QVBoxLayout:
        self.filter_table_widget.setRowCount(FilterConfig.MAX_FILTERS)
        self.filter_table_widget.setColumnCount(3)
        self.filter_table_widget.setHorizontalHeaderLabels(
            (self.tr('Parameter'), self.tr('< or >'), self.tr('Number'))
        )
        self.filter_table_widget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.filter_table_widget.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        open_filters_button = QtWidgets.QPushButton()
        open_filters_button.clicked.connect(self.load_filter_settings)
        open_filters_button.setIcon(QtGui.QIcon(":open.png"))
        open_filters_button.setToolTip(self.tr("Load filter settings"))
        open_filters_button.setStatusTip(self.tr("Load filter settings"))

        save_filters_button = QtWidgets.QPushButton()
        save_filters_button.clicked.connect(self.save_filter_settings)
        save_filters_button.setIcon(QtGui.QIcon(":save.png"))
        save_filters_button.setToolTip(self.tr("Save filter settings"))
        save_filters_button.setStatusTip(self.tr("Save filter settings"))

        check_filters_button = QtWidgets.QPushButton()
        check_filters_button.clicked.connect(self._read_filter_table)
        check_filters_button.setIcon(QtGui.QIcon(":check.png"))
        check_filters_button.setToolTip(self.tr("Check filters"))
        check_filters_button.setStatusTip(self.tr("Check filters"))

        execute_filters_button = QtWidgets.QPushButton()
        execute_filters_button.clicked.connect(self.filter_data)
        execute_filters_button.setIcon(QtGui.QIcon(":filter.png"))
        execute_filters_button.setToolTip(self.tr("Execute filters"))
        execute_filters_button.setStatusTip(self.tr("Execute filters"))

        default_filters_button = QtWidgets.QPushButton()
        default_filters_button.clicked.connect(self.set_default_filters)
        default_filters_button.setIcon(QtGui.QIcon(":revert.png"))
        default_filters_button.setToolTip(self.tr("Reload default filters"))
        default_filters_button.setStatusTip(self.tr("Reload default filters"))

        button_box = QtWidgets.QDialogButtonBox()
        button_box.addButton(open_filters_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(save_filters_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(check_filters_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(execute_filters_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(default_filters_button, QtWidgets.QDialogButtonBox.ActionRole)

        middle_panel = QtWidgets.QVBoxLayout()
        middle_panel.addWidget(self.filter_table_widget)
        middle_panel.addWidget(button_box)

        return middle_panel

    def _create_toolbar(self) -> QtWidgets.QHBoxLayout:
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

        plot_selection_button = QtWidgets.QPushButton()
        plot_selection_button.clicked.connect(self.open_plot_selection)
        plot_selection_button.setIcon(QtGui.QIcon(":chart.png"))
        plot_selection_button.setToolTip(self.tr("Plot selection"))
        plot_selection_button.setStatusTip(self.tr("Plot selection"))

        top_button_box = QtWidgets.QDialogButtonBox()
        top_button_box.addButton(report_button, QtWidgets.QDialogButtonBox.ActionRole)
        top_button_box.addButton(open_report_button, QtWidgets.QDialogButtonBox.ActionRole)
        top_button_box.addButton(plot_selection_button, QtWidgets.QDialogButtonBox.ActionRole)

        for param in self.plot_parameter_list:
            self.parameter_combo_box.addItem(param)
        self.parameter_combo_box.setCurrentIndex(4)

        for plot_type in self.plot_type_list:
            self.plot_type_combo_box.addItem(plot_type)

        toolbar_layout = QtWidgets.QHBoxLayout()
        toolbar_layout.addWidget(top_button_box)
        toolbar_layout.addWidget(self.parameter_combo_box)
        toolbar_layout.addWidget(self.plot_type_combo_box)

        return toolbar_layout

    def create_menu(self) -> None:
        self._create_file_menu()
        self._create_edit_menu()
        self._create_language_menu()
        self._create_help_menu()

    def _create_file_menu(self) -> None:
        self.file_menu = self.menuBar().addMenu(self.tr("File"))

        tip = self.tr("Open file")
        load_action = QtWidgets.QAction(self.tr("Open..."), self)
        load_action.setIcon(QtGui.QIcon(":open.png"))
        load_action.triggered.connect(self.load_file)
        load_action.setToolTip(tip)
        load_action.setStatusTip(tip)

        tip = self.tr("Save files")
        save_action = QtWidgets.QAction(self.tr("Save..."), self)
        save_action.setIcon(QtGui.QIcon(":save.png"))
        save_action.triggered.connect(self.save_files)
        save_action.setToolTip(tip)
        save_action.setStatusTip(tip)

        tip = self.tr("Quit")
        quit_action = QtWidgets.QAction(tip, self)
        quit_action.setIcon(QtGui.QIcon(":quit.png"))
        quit_action.triggered.connect(self.close)
        quit_action.setToolTip(tip)
        quit_action.setStatusTip(tip)
        quit_action.setShortcut('Ctrl+Q')

        self.file_menu.addAction(load_action)
        self.file_menu.addAction(save_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(quit_action)

    def _create_edit_menu(self) -> None:
        self.edit_menu = self.menuBar().addMenu(self.tr("Data labels"))

        tip = self.tr("Data label set A")
        format_action_a = QtWidgets.QAction(self.tr("Data label set A"), self)
        format_action_a.setIcon(QtGui.QIcon(":label.png"))
        format_action_a.triggered.connect(self.set_data_format_a)
        format_action_a.setToolTip(tip)
        format_action_a.setStatusTip(tip)

        tip = self.tr("Data label set B")
        format_action_b = QtWidgets.QAction(self.tr("Data label set B"), self)
        format_action_b.setIcon(QtGui.QIcon(":label.png"))
        format_action_b.triggered.connect(self.set_data_format_b)
        format_action_b.setToolTip(tip)
        format_action_b.setStatusTip(tip)

        tip = self.tr("Data label set C")
        format_action_c = QtWidgets.QAction(self.tr("Data label set C"), self)
        format_action_c.setIcon(QtGui.QIcon(":label.png"))
        format_action_c.triggered.connect(self.set_data_format_c)
        format_action_c.setToolTip(tip)
        format_action_c.setStatusTip(tip)

        tip = self.tr("Data label set D")
        format_action_d = QtWidgets.QAction(self.tr("Data label set D"), self)
        format_action_d.setIcon(QtGui.QIcon(":label.png"))
        format_action_d.triggered.connect(self.set_data_format_d)
        format_action_d.setToolTip(tip)
        format_action_d.setStatusTip(tip)

        tip = self.tr("Custom labels")
        format_action_custom = QtWidgets.QAction(self.tr("Custom labels"), self)
        format_action_custom.setIcon(QtGui.QIcon(":label.png"))
        format_action_custom.triggered.connect(self.set_data_format_custom)
        format_action_custom.setToolTip(tip)
        format_action_custom.setStatusTip(tip)

        self.edit_menu.addAction(format_action_a)
        self.edit_menu.addAction(format_action_b)
        self.edit_menu.addAction(format_action_c)
        self.edit_menu.addAction(format_action_d)
        self.edit_menu.addAction(format_action_custom)

    def _create_language_menu(self) -> None:
        self.language_menu = self.menuBar().addMenu(self.tr("Language"))

        tip = self.tr("Switch to Chinese language")
        chinese_action = QtWidgets.QAction(self.tr("Chinese"), self)
        chinese_action.setIcon(QtGui.QIcon(":lang.png"))
        chinese_action.triggered.connect(self.switch_to_chinese)
        chinese_action.setToolTip(tip)
        chinese_action.setStatusTip(tip)

        tip = self.tr("Switch to Korean language")
        korean_action = QtWidgets.QAction(self.tr("Korean"), self)
        korean_action.setIcon(QtGui.QIcon(":lang.png"))
        korean_action.triggered.connect(self.switch_to_korean)
        korean_action.setToolTip(tip)
        korean_action.setStatusTip(tip)

        tip = self.tr("Switch to English language")
        english_action = QtWidgets.QAction(self.tr("English"), self)
        english_action.setIcon(QtGui.QIcon(":lang.png"))
        english_action.triggered.connect(self.switch_to_english)
        english_action.setToolTip(tip)
        english_action.setStatusTip(tip)

        self.language_menu.addAction(chinese_action)
        self.language_menu.addAction(korean_action)
        self.language_menu.addAction(english_action)

    def _create_help_menu(self) -> None:
        self.help_menu = self.menuBar().addMenu(self.tr("Help"))

        tip = self.tr("Help information")
        help_action = QtWidgets.QAction(self.tr("Help..."), self)
        help_action.setIcon(QtGui.QIcon(":help.png"))
        help_action.triggered.connect(self.open_help_dialog)
        help_action.setToolTip(tip)
        help_action.setStatusTip(tip)
        help_action.setShortcut('H')

        tip = self.tr("About the application")
        about_action = QtWidgets.QAction(self.tr("About..."), self)
        about_action.setIcon(QtGui.QIcon(":info.png"))
        about_action.triggered.connect(self.on_about)
        about_action.setToolTip(tip)
        about_action.setStatusTip(tip)
        about_action.setShortcut('F1')

        self.help_menu.addAction(help_action)
        self.help_menu.addAction(about_action)
