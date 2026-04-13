# -*- coding: utf-8 -*-
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

from HelpDialog import HelpDialog
from IVMainPlot import (
    CorrVocIsc, CorrEtaFF, CorrRshFF, DistLtoH, DensEta,
    DistWT, DistRM, IVBoxPlot, IVHistPlot, IVHistDenPlot,
    ViolinPlot, CategoryScatter
)
from FileService import FileService
from DataService import DataService
from FilterService import FilterService
from ReportGenerator import ReportGenerator
from config import (
    LabelFormat, DataColumns, PlotParameters, WindowConfig,
    FilterConfig, PlotType
)
from logger_config import setup_logger

logger = setup_logger(__name__)


class IVMainGui(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_window()
        self._initialize_services()
        self._initialize_gui_state()
        self._build_ui()

    def _setup_window(self):
        self.setWindowTitle(self.tr("SCiDA Pro"))
        self.setWindowIcon(QtGui.QIcon(":ScidaPro_icon.png"))
        self.resize(WindowConfig.MAIN_WIDTH, WindowConfig.MAIN_HEIGHT)
        self._center_window()
        self.setStyleSheet(f'font-size: {WindowConfig.FONT_SIZE}pt;')

    def _center_window(self):
        frame_geometry = self.frameGeometry()
        center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def _initialize_services(self):
        self.file_service = FileService()
        self.data_service = DataService()
        self.filter_service = FilterService()
        self.report_generator = ReportGenerator(self.data_service, self.filter_service)

    def _initialize_gui_state(self):
        self.clipboard = QtWidgets.QApplication.clipboard()
        self.series_list_model = QtGui.QStandardItemModel()
        self.series_list_model.itemChanged.connect(self._on_rename_dataset)
        self.filter_table_widget = QtWidgets.QTableWidget()
        self.label_format = LabelFormat.A
        self.label_text = QtWidgets.QLabel("Data label set A")
        self.first_run = True
        self.status_text = QtWidgets.QLabel("")
        self.report_name = ''
        self.translator = None
        self.plot_window = None
        self.ad = self.data_service.datasets

    def _build_ui(self):
        self._create_menu()
        self._create_main_frame()
        self._set_default_filters()

    @QtCore.pyqtSlot(int)
    def _on_plot_selection_changed(self, index: int):
        if index < 3:
            self.param_one_combo.setEnabled(True)
        elif 2 < index < 7:
            self.param_one_combo.setCurrentIndex(4)
            self.param_one_combo.setDisabled(True)
        else:
            self.param_one_combo.setDisabled(True)

    @QtCore.pyqtSlot(QtGui.QStandardItem)
    def _on_rename_dataset(self, item):
        entered_name = str(item.text())
        valid_filename = self.file_service.sanitize_filename(entered_name)

        if len(valid_filename) > 0:
            dataset_index = self.series_list_model.indexFromItem(item).row()
            self.data_service.rename_dataset(dataset_index, valid_filename)
            item.setText(valid_filename)
        else:
            dataset_index = self.series_list_model.indexFromItem(item).row()
            item.setText(self.data_service.get_dataset_name(dataset_index))

    def load_file(self):
        file_dialog = QtWidgets.QFileDialog()
        filenames, _ = file_dialog.getOpenFileNames(
            self, self.tr("Load files"),
            self.file_service.previous_directory,
            "Excel Files (*.csv *.xls *.xlsx)"
        )

        if not filenames:
            return

        has_non_ascii = False
        has_read_error = False
        has_empty_data = False
        initial_count = self.data_service.get_dataset_count()

        for filepath in filenames:
            if not self.file_service.is_ascii_filename(filepath):
                has_non_ascii = True
                continue

            self.file_service.update_previous_directory(filepath)
            success = self._load_single_file(filepath)

            if success is False:
                has_read_error = True
            elif success is None:
                has_empty_data = True

        self._show_load_warnings(has_non_ascii, has_read_error, has_empty_data)
        self._update_status_ready()

    def _load_single_file(self, filepath: str) -> bool:
        current_index = self.data_service.get_dataset_count()
        columns = DataColumns.LABEL_FORMATS[self.label_format]

        dataframe = self.file_service.load_data_file(filepath, columns)
        if dataframe is None:
            return False

        dataframe = self.data_service.to_numeric(dataframe)
        dataframe = self.data_service.filter_positive_values(dataframe)

        if dataframe.empty:
            return None

        self.data_service.add_dataset(dataframe, '')
        self.data_service.apply_label_format_conversion(current_index, self.label_format)

        basename = self.file_service.get_basename_without_extension(filepath)
        dataset_name = self.file_service.sanitize_filename(basename)
        self.data_service.rename_dataset(current_index, dataset_name)
        self._add_to_series_list(dataset_name)

        logger.info("Loaded file: %s (%d rows)", filepath, len(dataframe))
        return True

    def _add_to_series_list(self, name: str):
        item = QtGui.QStandardItem(name)
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        self.series_list_model.appendRow(item)

    def _show_load_warnings(self, non_ascii: bool, read_error: bool, empty_data: bool):
        if non_ascii:
            self._show_warning(self.tr("Filenames with non-ASCII characters were found.\n\nThe application currently only supports ASCII filenames."))
        if read_error:
            self._show_warning(self.tr("Error while reading data files.\n\nData labels were perhaps not recognized."))
        if empty_data:
            self._show_warning(self.tr("Empty data sets were found.\n\nThe application only accepts data entries with a value for Voc, Isc, FF, Eta, Rser, Rsh and Irev. All values also need to be non-negative."))

    def _show_warning(self, message: str):
        QtWidgets.QMessageBox.about(self, self.tr("Warning"), message)

    def _update_status_ready(self):
        if self.data_service.has_data():
            self.statusBar().showMessage(self.tr("Ready"), 3000)
        else:
            self.statusBar().showMessage(self.tr("Please load data files"), 3000)

    def save_files(self):
        dest_dir = QtWidgets.QFileDialog.getExistingDirectory(
            None, self.tr('Open directory'),
            self.file_service.previous_directory,
            QtWidgets.QFileDialog.ShowDirsOnly
        )

        if not dest_dir:
            return

        if not self.data_service.has_data():
            self.statusBar().showMessage(self.tr("Please load data files"), 3000)
            return

        self.file_service.previous_directory = dest_dir
        yes_to_all = False

        for idx in sorted(self.data_service.datasets.keys()):
            filename = f'{self.data_service.get_dataset_name(idx)}.csv'
            save_path = self.file_service.get_save_path(dest_dir, filename)
            save_path = self._check_overwrite(save_path, filename, yes_to_all)

            if save_path is None:
                continue
            if save_path is False:
                return

            self.file_service.save_csv(self.data_service.get_dataset(idx), save_path)

        self.statusBar().showMessage(self.tr("Files saved"), 3000)

    def _check_overwrite(self, save_path: str, filename: str, yes_to_all: bool):
        if not yes_to_all and self.file_service.check_overwrite(save_path):
            reply = QtWidgets.QMessageBox.question(
                self, self.tr("Message"),
                f"Overwrite '{filename}'?",
                QtWidgets.QMessageBox.YesToAll | QtWidgets.QMessageBox.Yes |
                QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel,
                QtWidgets.QMessageBox.No
            )

            if reply == QtWidgets.QMessageBox.No:
                new_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                    self, self.tr("Save file"),
                    save_path, "CSV File (*.csv)"
                )
                return new_path if new_path else None

            if reply == QtWidgets.QMessageBox.YesToAll:
                return save_path

            if reply == QtWidgets.QMessageBox.Cancel:
                return False

        return save_path

    def combine_datasets(self):
        if self.data_service.get_dataset_count() <= 1:
            self._update_status_ready()
            return

        self.statusBar().showMessage(self.tr("Combining data sets..."), 3000)
        self.report_generator.clear_yield_loss()

        self.series_list_model.clear()
        self.series_list_model.setHorizontalHeaderLabels([self.tr('Data series')])

        self.data_service.combine_datasets()
        self._add_to_series_list(self.data_service.get_dataset_name(0))

        self.statusBar().showMessage(self.tr("Ready"), 3000)

    def filter_data(self):
        if not self.data_service.has_data():
            self._update_status_ready()
            return

        self.statusBar().showMessage(self.tr("Filtering data..."), 3000)
        self._read_filter_table()

        for idx in sorted(self.data_service.datasets.keys()):
            if idx >= len(self.report_generator.yield_loss_data):
                dataset = self.data_service.get_dataset(idx)
                dataset_filtered, yield_loss = self.filter_service.apply_filters(dataset)
                self.data_service.datasets[idx] = dataset_filtered
                self.report_generator.add_yield_loss(yield_loss)
                self.data_service.reset_dataset_index(idx)
                self.data_service.fill_empty_dataset(idx)

        self._refresh_series_list()
        self.statusBar().showMessage(self.tr("Ready"), 3000)

    def _refresh_series_list(self):
        self.series_list_model.clear()
        self.series_list_model.setHorizontalHeaderLabels([self.tr('Data series')])
        for idx in sorted(self.data_service.datasets.keys()):
            self._add_to_series_list(self.data_service.get_dataset_name(idx))

    def make_report(self):
        if not self.data_service.has_data():
            self._update_status_ready()
            return

        report_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, self.tr("Save file"),
            self.file_service.previous_directory,
            "Excel Files (*.xlsx)"
        )

        if not report_path:
            return

        if not self.file_service.is_ascii_filename(report_path):
            self._show_warning(self.tr("Filenames with non-ASCII characters were found.\n\nThe application currently only supports ASCII filenames."))
            self.report_name = ''
            return

        self.statusBar().showMessage(self.tr("Making an Excel report..."), 3000)

        result = self.report_generator.create_report(report_path, self)
        if result:
            self.report_name = result
            self.statusBar().showMessage(self.tr("Ready"), 3000)

    def open_report(self):
        if not self.report_name:
            self.statusBar().showMessage(self.tr("Please make report"), 3000)
            return

        self.statusBar().showMessage(self.tr("Opening report..."), 3000)
        url = self.file_service.get_file_url(self.report_name)
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url, QtCore.QUrl.StrictMode))
        self.statusBar().showMessage(self.tr("Ready"), 3000)

    def clear_data(self):
        self.data_service.clear_all()
        self.report_generator.clear_yield_loss()
        self.series_list_model.clear()
        self.series_list_model.setHorizontalHeaderLabels([self.tr('Data series')])
        self.report_name = ''
        self.statusBar().showMessage(self.tr("All data has been cleared"), 3000)

    def open_plot_selection(self):
        if not self.data_service.has_data():
            self._update_status_ready()
            return

        self.statusBar().showMessage(self.tr("Creating plot window..."), 3000)

        selected_plot = PlotType(self.plot_selection_combo.currentIndex())

        if self.plot_window and self.plot_window.isWindow():
            self.plot_window.close()

        param_text = self.param_one_combo.currentText()
        plot_classes = {
            PlotType.BOXPLOT: lambda: IVBoxPlot(self, param_text),
            PlotType.VIOLINPLOT: lambda: ViolinPlot(self, param_text),
            PlotType.CATEGORY_SCATTER: lambda: CategoryScatter(self, param_text),
            PlotType.WALKTHROUGH: lambda: DistWT(self, param_text),
            PlotType.ROLLING_MEAN: lambda: DistRM(self, param_text),
            PlotType.LOW_TO_HIGH: lambda: DistLtoH(self),
            PlotType.HISTOGRAM: lambda: IVHistPlot(self),
            PlotType.DENSITY: lambda: DensEta(self),
            PlotType.HISTOGRAM_DENSITY: lambda: IVHistDenPlot(self),
            PlotType.CORR_VOC_ISC: lambda: CorrVocIsc(self),
            PlotType.CORR_ETA_FF: lambda: CorrEtaFF(self),
            PlotType.CORR_RSH_FF: lambda: CorrRshFF(self),
        }

        if selected_plot in plot_classes:
            self.plot_window = plot_classes[selected_plot]()
            self.plot_window.show()

        self.statusBar().showMessage(self.tr("Ready"), 3000)

    def _set_default_filters(self):
        self._populate_filter_table(self.filter_service.get_default_filters())

    def _set_user_filters(self):
        self._populate_filter_table(self.filter_service.user_filters_plain)

    def _populate_filter_table(self, filters):
        self.filter_table_widget.clearContents()
        for row_idx, row_data in enumerate(filters):
            for col_idx, value in enumerate(row_data):
                item = QtWidgets.QTableWidgetItem(str(value))
                self.filter_table_widget.setItem(row_idx, col_idx, item)

    def load_filter_settings(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, self.tr("Open file"),
            self.file_service.previous_directory,
            "Filter Settings Files (*.scda)"
        )

        if not filename:
            return

        if not self.file_service.is_ascii_filename(filename):
            self._show_warning(self.tr("Filenames with non-ASCII characters were found.\n\nThe application currently only supports ASCII filenames."))
            return

        self.file_service.update_previous_directory(filename)
        filters = self.file_service.load_filters(filename)

        if filters:
            self.filter_service.load_plain_filters(filters)
            self._set_user_filters()
            self.statusBar().showMessage(self.tr("New filter settings loaded"), 3000)

    def save_filter_settings(self):
        self._read_filter_table()
        self.filter_service.convert_to_plain_format()

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, self.tr("Save file"),
            self.file_service.previous_directory,
            "Description Files (*.scda)"
        )

        if not filename:
            return

        if not self.file_service.is_ascii_filename(filename):
            self._show_warning(self.tr("Filenames with non-ASCII characters were found.\n\nThe application currently only supports ASCII filenames."))
            return

        self.file_service.update_previous_directory(filename)
        self.file_service.save_filters(self.filter_service.user_filters_plain, filename)
        self.statusBar().showMessage(self.tr("File saved"), 3000)

    def _read_filter_table(self):
        self.statusBar().showMessage(self.tr("Checking filters..."), 3000)
        table_data = []

        for row in range(FilterConfig.MAX_FILTERS):
            if self.filter_table_widget.item(row, 0):
                param = self.filter_service.remove_whitespace(
                    self.filter_table_widget.item(row, 0).text()
                )
                operator = self.filter_service.remove_whitespace(
                    self.filter_table_widget.item(row, 1).text()
                )
                value = self.filter_service.remove_whitespace(
                    self.filter_table_widget.item(row, 2).text()
                )
                table_data.append((param, operator, value))

        self.filter_service.parse_filters_from_table_data(table_data)
        self._update_filter_table_display()
        self.statusBar().showMessage(self.tr("Ready"), 3000)

    def _update_filter_table_display(self):
        filters_for_table = self.filter_service.get_filters_for_table()
        for row in range(FilterConfig.MAX_FILTERS):
            for col in range(3):
                if row < len(filters_for_table):
                    text = filters_for_table[row][col]
                else:
                    text = ""
                item = QtWidgets.QTableWidgetItem(text)
                self.filter_table_widget.setItem(row, col, item)

    def keyPressEvent(self, event):
        if event.modifiers() & QtCore.Qt.ControlModifier:
            selected = self.filter_table_widget.selectedRanges()

            if event.key() == QtCore.Qt.Key_V:
                self._paste_filter_cells(selected[0])
            elif event.key() == QtCore.Qt.Key_C:
                self._copy_filter_cells(selected[0])

    def _paste_filter_cells(self, selection):
        first_row = selection.topRow()
        first_col = selection.leftColumn()

        for row_delta, row_text in enumerate(self.clipboard.text().split('\n')):
            for col_delta, cell_text in enumerate(row_text.split('\t')):
                if cell_text:
                    item = QtWidgets.QTableWidgetItem(cell_text)
                    self.filter_table_widget.setItem(
                        first_row + row_delta,
                        first_col + col_delta,
                        item
                    )

    def _copy_filter_cells(self, selection):
        text = ""
        for row in range(selection.topRow(), selection.bottomRow() + 1):
            for col in range(selection.leftColumn(), selection.rightColumn() + 1):
                try:
                    text += str(self.filter_table_widget.item(row, col).text()) + "\t"
                except AttributeError:
                    text += "\t"
            text = text[:-1] + "\n"
        self.clipboard.setText(text)

    def _set_label_format(self, format_id: LabelFormat, label_text: str):
        self.label_format = format_id
        self.statusBar().removeWidget(self.label_text)
        self.label_text = QtWidgets.QLabel(label_text)
        self.statusBar().addPermanentWidget(self.label_text)

    def set_data_format0(self):
        self._set_label_format(LabelFormat.A, "Data label set A")

    def set_data_format1(self):
        self._set_label_format(LabelFormat.B, "Data label set B")

    def set_data_format2(self):
        self._set_label_format(LabelFormat.C, "Data label set C")

    def set_data_format3(self):
        self._set_label_format(LabelFormat.D, "Data label set D")

    def set_data_format4(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, self.tr("Open file"),
            self.file_service.previous_directory,
            "Label Settings File (*.csv)"
        )

        if not filename:
            return

        if not self.file_service.is_ascii_filename(filename):
            self._show_warning(self.tr("Filenames with non-ASCII characters were found.\n\nThe application currently only supports ASCII filenames."))
            return

        self.file_service.update_previous_directory(filename)
        labels = self.file_service.load_custom_labels(filename)

        if labels:
            DataColumns.LABEL_FORMATS[LabelFormat.CUSTOM] = labels
            self._set_label_format(LabelFormat.CUSTOM, "Custom label set")
            self._show_warning(self.tr('Data series') + ": " + str(labels))

        self.statusBar().showMessage(self.tr("Ready"), 3000)

    def _switch_language(self, translation_file: str = None):
        if self.translator:
            QtWidgets.QApplication.removeTranslator(self.translator)

        if translation_file:
            self.translator = QtCore.QTranslator()
            self.translator.load(translation_file)
            QtWidgets.QApplication.installTranslator(self.translator)

        self.menuBar().clear()
        self._create_menu()
        self.param_one_combo.clear()
        self.plot_selection_combo.clear()
        self.main_frame.deleteLater()
        self._create_main_frame()

    def langKor(self):
        self._switch_language(":IVMain_kr.qm")

    def langChin(self):
        self._switch_language(":IVMain_cn.qm")

    def langEngl(self):
        self._switch_language(None)

    def open_help_dialog(self):
        help_dialog = HelpDialog(self)
        help_dialog.setModal(True)
        help_dialog.show()

    def on_about(self):
        msg = self.tr("Solar cell data analysis\nAuthor: Ronald Naber\nLicense: Public domain")
        QtWidgets.QMessageBox.about(self, self.tr("About the application"), msg)

    def _create_main_frame(self):
        self.setWindowTitle(self.tr("Solar cell data analysis"))
        self.main_frame = QtWidgets.QWidget()

        left_vbox = self._create_left_panel()
        mid_vbox = self._create_mid_panel()
        right_vbox = self._create_right_panel()

        hbox = QtWidgets.QHBoxLayout()
        hbox.addLayout(left_vbox, stretch=1)
        hbox.addLayout(mid_vbox, stretch=1)
        hbox.addLayout(right_vbox, stretch=2)

        self.main_frame.setLayout(hbox)
        self.setCentralWidget(self.main_frame)
        self.statusBar().addPermanentWidget(self.label_text)
        self.statusBar().addPermanentWidget(self.status_text, 1)

    def _create_left_panel(self):
        self.series_list_view = QtWidgets.QTreeView()
        self.series_list_view.setModel(self.series_list_model)
        self.series_list_model.setHorizontalHeaderLabels([self.tr('Data series')])
        self.series_list_view.setRootIsDecorated(False)
        self.series_list_view.setDragDropMode(QtWidgets.QAbstractItemView.NoDragDrop)
        self.series_list_view.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

        buttonbox = self._create_data_button_box()

        left_vbox = QtWidgets.QVBoxLayout()
        left_vbox.addWidget(self.series_list_view)
        left_vbox.addWidget(buttonbox)
        return left_vbox

    def _create_data_button_box(self):
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

        buttonbox = QtWidgets.QDialogButtonBox()
        buttonbox.addButton(open_files_button, QtWidgets.QDialogButtonBox.ActionRole)
        buttonbox.addButton(save_files_button, QtWidgets.QDialogButtonBox.ActionRole)
        buttonbox.addButton(combine_data_button, QtWidgets.QDialogButtonBox.ActionRole)
        buttonbox.addButton(clear_data_button, QtWidgets.QDialogButtonBox.ActionRole)
        return buttonbox

    def _create_mid_panel(self):
        self.filter_table_widget.setRowCount(12)
        self.filter_table_widget.setColumnCount(3)
        self.filter_table_widget.setHorizontalHeaderLabels(
            (self.tr('Parameter'), self.tr('< or >'), self.tr('Number'))
        )
        self.filter_table_widget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.filter_table_widget.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        buttonbox = self._create_filter_button_box()

        mid_vbox = QtWidgets.QVBoxLayout()
        mid_vbox.addWidget(self.filter_table_widget)
        mid_vbox.addWidget(buttonbox)
        return mid_vbox

    def _create_filter_button_box(self):
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
        default_filters_button.clicked.connect(self._set_default_filters)
        default_filters_button.setIcon(QtGui.QIcon(":revert.png"))
        default_filters_button.setToolTip(self.tr("Reload default filters"))
        default_filters_button.setStatusTip(self.tr("Reload default filters"))

        buttonbox = QtWidgets.QDialogButtonBox()
        buttonbox.addButton(open_filters_button, QtWidgets.QDialogButtonBox.ActionRole)
        buttonbox.addButton(save_filters_button, QtWidgets.QDialogButtonBox.ActionRole)
        buttonbox.addButton(check_filters_button, QtWidgets.QDialogButtonBox.ActionRole)
        buttonbox.addButton(execute_filters_button, QtWidgets.QDialogButtonBox.ActionRole)
        buttonbox.addButton(default_filters_button, QtWidgets.QDialogButtonBox.ActionRole)
        return buttonbox

    def _create_right_panel(self):
        top_buttonbox = self._create_top_button_box()

        self.param_one_combo = QtWidgets.QComboBox(self)
        self.plot_selection_combo = QtWidgets.QComboBox(self)
        self.plot_selection_combo.currentIndexChanged.connect(self._on_plot_selection_changed)

        for item in PlotParameters.SELECTION_LIST:
            self.param_one_combo.addItem(item)
        self.param_one_combo.setCurrentIndex(4)

        for item in PlotParameters.COMBO_LIST:
            self.plot_selection_combo.addItem(item)

        hbox1 = QtWidgets.QHBoxLayout()
        hbox1.addWidget(self.param_one_combo)
        hbox1.addWidget(self.plot_selection_combo)

        right_vbox = QtWidgets.QVBoxLayout()
        right_vbox.addWidget(top_buttonbox)
        right_vbox.addLayout(hbox1)
        right_vbox.addStretch(1)
        return right_vbox

    def _create_top_button_box(self):
        report_button = QtWidgets.QPushButton()
        report_button.clicked.connect(self.make_report)
        report_button.setIcon(QtGui.QIcon(":report.png"))
        report_button.setToolTip(self.tr("Make report"))
        report_button.setStatusTip(self.tr("Make report"))

        openreport_button = QtWidgets.QPushButton()
        openreport_button.clicked.connect(self.open_report)
        openreport_button.setIcon(QtGui.QIcon(":link.png"))
        openreport_button.setToolTip(self.tr("Open report"))
        openreport_button.setStatusTip(self.tr("Open report"))

        plotselection_button = QtWidgets.QPushButton()
        plotselection_button.clicked.connect(self.open_plot_selection)
        plotselection_button.setIcon(QtGui.QIcon(":chart.png"))
        plotselection_button.setToolTip(self.tr("Plot selection"))
        plotselection_button.setStatusTip(self.tr("Plot selection"))

        buttonbox = QtWidgets.QDialogButtonBox()
        buttonbox.addButton(report_button, QtWidgets.QDialogButtonBox.ActionRole)
        buttonbox.addButton(openreport_button, QtWidgets.QDialogButtonBox.ActionRole)
        buttonbox.addButton(plotselection_button, QtWidgets.QDialogButtonBox.ActionRole)
        return buttonbox

    def _create_menu(self):
        self._create_file_menu()
        self._create_edit_menu()
        self._create_view_menu()
        self._create_settings_menu()
        self._create_help_menu()

    def _create_file_menu(self):
        file_menu = self.menuBar().addMenu(self.tr("&File"))

        load_action = QtWidgets.QAction(self.tr("&Load files"), self)
        load_action.setIcon(QtGui.QIcon(":open.png"))
        load_action.triggered.connect(self.load_file)
        load_action.setShortcut('Ctrl+L')

        save_action = QtWidgets.QAction(self.tr("&Save files"), self)
        save_action.setIcon(QtGui.QIcon(":save.png"))
        save_action.triggered.connect(self.save_files)
        save_action.setShortcut('Ctrl+S')

        report_action = QtWidgets.QAction(self.tr("&Make report"), self)
        report_action.setIcon(QtGui.QIcon(":report.png"))
        report_action.triggered.connect(self.make_report)
        report_action.setShortcut('Ctrl+R')

        openreport_action = QtWidgets.QAction(self.tr("Open report"), self)
        openreport_action.setIcon(QtGui.QIcon(":link.png"))
        openreport_action.triggered.connect(self.open_report)
        openreport_action.setShortcut('Ctrl+Shift+R')

        clear_action = QtWidgets.QAction(self.tr("&Clear all data"), self)
        clear_action.setIcon(QtGui.QIcon(":erase.png"))
        clear_action.triggered.connect(self.clear_data)

        quit_action = QtWidgets.QAction(self.tr("&Quit"), self)
        quit_action.setIcon(QtGui.QIcon(":quit.png"))
        quit_action.triggered.connect(self.close)
        quit_action.setShortcut('Ctrl+Q')

        file_menu.addAction(load_action)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        file_menu.addAction(report_action)
        file_menu.addAction(openreport_action)
        file_menu.addSeparator()
        file_menu.addAction(clear_action)
        file_menu.addSeparator()
        file_menu.addAction(quit_action)

    def _create_edit_menu(self):
        edit_menu = self.menuBar().addMenu(self.tr("&Edit"))

        combine_action = QtWidgets.QAction(self.tr("&Combine data sets"), self)
        combine_action.setIcon(QtGui.QIcon(":combine.png"))
        combine_action.triggered.connect(self.combine_datasets)

        filter_action = QtWidgets.QAction(self.tr("&Filter data"), self)
        filter_action.setIcon(QtGui.QIcon(":filter.png"))
        filter_action.triggered.connect(self.filter_data)

        edit_menu.addAction(combine_action)
        edit_menu.addAction(filter_action)

    def _create_view_menu(self):
        view_menu = self.menuBar().addMenu(self.tr("&View"))

        plot_action = QtWidgets.QAction(self.tr("&Plot"), self)
        plot_action.setIcon(QtGui.QIcon(":chart.png"))
        plot_action.triggered.connect(self.open_plot_selection)
        plot_action.setShortcut('Ctrl+P')

        view_menu.addAction(plot_action)

    def _create_settings_menu(self):
        settings_menu = self.menuBar().addMenu(self.tr("&Settings"))
        self._create_label_submenu(settings_menu)
        self._create_language_submenu(settings_menu)

    def _create_label_submenu(self, parent_menu):
        label_submenu = parent_menu.addMenu(self.tr("&Label set"))

        label0_action = QtWidgets.QAction(self.tr("&A"), self)
        label0_action.triggered.connect(self.set_data_format0)

        label1_action = QtWidgets.QAction(self.tr("&B"), self)
        label1_action.triggered.connect(self.set_data_format1)

        label2_action = QtWidgets.QAction(self.tr("&C"), self)
        label2_action.triggered.connect(self.set_data_format2)

        label3_action = QtWidgets.QAction(self.tr("&D"), self)
        label3_action.triggered.connect(self.set_data_format3)

        label4_action = QtWidgets.QAction(self.tr("&Custom"), self)
        label4_action.triggered.connect(self.set_data_format4)

        label_submenu.addAction(label0_action)
        label_submenu.addAction(label1_action)
        label_submenu.addAction(label2_action)
        label_submenu.addAction(label3_action)
        label_submenu.addAction(label4_action)

    def _create_language_submenu(self, parent_menu):
        lang_submenu = parent_menu.addMenu(self.tr("&Language"))

        engl_action = QtWidgets.QAction(self.tr("&English"), self)
        engl_action.triggered.connect(self.langEngl)

        chin_action = QtWidgets.QAction(self.tr("&Chinese"), self)
        chin_action.triggered.connect(self.langChin)

        kor_action = QtWidgets.QAction(self.tr("&Korean"), self)
        kor_action.triggered.connect(self.langKor)

        lang_submenu.addAction(engl_action)
        lang_submenu.addAction(chin_action)
        lang_submenu.addAction(kor_action)

    def _create_help_menu(self):
        help_menu = self.menuBar().addMenu(self.tr("&Help"))

        help_action = QtWidgets.QAction(self.tr("&Help"), self)
        help_action.triggered.connect(self.open_help_dialog)
        help_action.setShortcut('F1')

        about_action = QtWidgets.QAction(self.tr("&About"), self)
        about_action.triggered.connect(self.on_about)

        help_menu.addAction(help_action)
        help_menu.addAction(about_action)
