#!/usr/bin/env python

import sys
import pandas as pd
import logging
import webbrowser
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QSettings, QModelIndex

from discodos.qt.MainWindow import Ui_MainWindow
from discodos.models import Mix, Collection
from discodos.config import Config
from discodos.ctrls import Ctrl_common
from discodos.views import View_common, Mix_view_common, Collection_view_common


log = logging.getLogger('discodos')


# class GuiTableViewModel(QtGui.QStandardItemModel):
class GuiTableViewModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        super(GuiTableViewModel, self).__init__()
        self._data = data

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                value = self._data.iloc[index.row(), index.column()]
                return value

            if role == Qt.EditRole:
                value = self._data.iloc[index.row()][index.column()]
                return value

            if role == Qt.ForegroundRole:
                value = str(self._data.iloc[index.row()][index.column()])
                if value.startswith("https://") or value.startswith("http://"):
                    return QtGui.QColor("blue")

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return self._data.shape[0]

    def columnCount(self, parent: QModelIndex = ...) -> int:
        return self._data.shape[1]

    def setData(self, index: QModelIndex, value, role: int = ...) -> bool:
        if role == Qt.EditRole:
            self._data.iloc[index.row()][index.column()] = value
        return True

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        if not index.isValid():
            return Qt.ItemIsDropEnabled
        if index.row() < len(self._data):
            return Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled
        return Qt.ItemIsEnabled | Qt.ItemIsEditable

    def supportedDropActions(self) -> bool:
        return Qt.MoveAction | Qt.CopyAction

    def supportedDragActions(self):
        return Qt.MoveAction

    # def insertRows(self, position, rows, index=QModelIndex()):
    #     print('insertrows at position', position)
    #     self.beginInsertRows(QModelIndex(), position, position + rows - 1)
    #     # need to insert dragrow in _data
    #     self.endInsertRows()
    #     print(self._data)
    #     return True
    #
    # def removeRows(self, position, rows, index=QModelIndex()):
    #     print("removeRows() Starting position: '%s'"%position, 'with the total rows to be deleted: ', rows)
    #     self.beginRemoveRows(QModelIndex(), position, position + rows - 1)
    #     self._data = self._data.drop(self._data.index[position])
    #     self.endRemoveRows()
    #     print(self._data)
    #     return True

    def update(self, df):
        self.layoutAboutToBeChanged.emit()
        self._data = df
        self.layoutChanged.emit()

    def headerData(self, col, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[col])
            # if orientation == Qt.Vertical:
            #     return str(self._data.index[col])

    def dropMimeData(self, data, action, row, col, parent):
        """
        Always move the entire row, and don't allow column "shifting"
        """
        return super().dropMimeData(data, action, row, 0, parent)

    # def sort(self, column, order):
    #     colname = self._data.columns.tolist()[column]
    #     self.layoutAboutToBeChanged.emit()
    #     self._data.sort_values(colname, ascending=order == QtCore.Qt.AscendingOrder, inplace=True)
    #     self._data.reset_index(inplace=True, drop=True)
    #     self.layoutChanged.emit()


class GuiTableViewProxyStyle(QtWidgets.QProxyStyle):

    def drawPrimitive(self, element, option, painter, widget=None):
        """
        Draw a line across the entire row rather than just the column
        we're hovering over.  This may not always work depending on global
        style - for instance I think it won't work on OSX.
        """
        if element == self.PE_IndicatorItemViewItemDrop and not option.rect.isNull():
            option_new = QtWidgets.QStyleOption(option)
            option_new.rect.setLeft(0)
            if widget:
                option_new.rect.setRight(widget.width())
            option = option_new
        super().drawPrimitive(element, option, painter, widget)


class GuiTableView(QtWidgets.QTableView):

    def __init__(self, parent, data):
        super().__init__(parent)
        self._data = data
        # self.verticalHeader().hide()
        # self.horizontalHeader().hide()
        # self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.SingleSelection)
        self.setShowGrid(False)
        self.setDragDropMode(self.InternalMove)
        self.setDragDropOverwriteMode(False)

        self.setStyle(GuiTableViewProxyStyle())
        self.model = GuiTableViewModel(self._data)
        self.setModel(self.model)

        self.setAlternatingRowColors(True)

        self._create_context_menu()

    def _create_context_menu(self):
        horizontal_header = self._data.columns
        self.horizontalHeader().setContextMenuPolicy(Qt.ActionsContextMenu)
        for idx, header_item in enumerate(horizontal_header):
            self.item = QtWidgets.QAction(header_item, self)
            self.item.setCheckable(True)
            result = self._make_colum_show_or_hide(idx)
            self.item.triggered.connect(result)
            self.horizontalHeader().addAction(self.item)

    def _make_colum_show_or_hide(self, column_idx):
        show_column = lambda checked: self.setColumnHidden(column_idx, not checked)
        return show_column

    def restore_column_settings(self, settings, setting_path, defaults={}):
        """ Restores column width and visible-state from Qsettings

        or falls back to using defaults (if provided). Also sets check marks
        in right click on headers context menu according to visible-state of
        columns.

        Args:
            settings (object): A QSettings object.
            setting_path (string): The path to the setting in the Qsettings
                object aka the .ini file. Format: section/keyname.
            defaults (dict): Contains column ID and a subdict containing default
                width and hidden state. Format:
                0: {width: 50, hidden: True}, 1: {width: ...}, ...

        Returns: None
        """
        if settings.value(setting_path):
            log.info("GuiTableView.restore_column_settings: "
                     "Restoring from saved settings.")
            self.horizontalHeader().restoreState(settings.value(setting_path))
        else:
            log.info("GuiTableView.restore_column_settings: "
                     "No saved settings found. Using defaults.")
            for column_id in defaults:
                if defaults[column_id]['width']:
                    self.setColumnWidth(
                        column_id,
                        defaults[column_id]['width']
                    )
                if defaults[column_id]['hidden']:
                    self.setColumnHidden(
                        column_id,
                        defaults[column_id]['hidden']
                    )

        # Set context menu check marks according to visible-state of columns
        for col, action in enumerate(self.horizontalHeader().actions()):
            action.setChecked(not self.horizontalHeader().isSectionHidden(col))


class GuiTreeViewModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        super(GuiTreeViewModel, self).__init__()
        self._data = data

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                value = self._data.iloc[index.row(), index.column()]
                return value
            if role == Qt.EditRole:
                value = self._data.iloc[index.row()][index.column()]
                return value
            if role == Qt.TextAlignmentRole:
                return Qt.AlignLeft
                # if index.column() == 0:

    def headerData(self, col, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[col])
        if role == Qt.TextAlignmentRole:
            return Qt.AlignLeft
            # if col == 0:

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return self._data.shape[0]

    def columnCount(self, parent: QModelIndex = ...) -> int:
        return self._data.shape[1]

    def setData(self, index: QModelIndex, value, role: int = ...) -> bool:
        if role == Qt.EditRole:
            self._data.iloc[index.row()][index.column()] = value
        return True

    def removeRows(self, position, rows, index=QModelIndex()):
        self.beginRemoveRows(QModelIndex(), position, position + rows - 1)
        self._data = self._data.drop(self._data.index[position])
        self.endRemoveRows()
        return True

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        if not index.isValid():
            return Qt.ItemIsDropEnabled
        if index.row() < len(self._data):
            return Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemNeverHasChildren
        return Qt.ItemIsEnabled | Qt.ItemIsEditable

    def update(self, df):
        self.layoutAboutToBeChanged.emit()
        self._data = df
        self.layoutChanged.emit()


class GuiTreeView(QtWidgets.QTreeView):
    def __init__(self, parent, data):
        super().__init__(parent)
        self._data = data
        self.model = GuiTreeViewModel(self._data)
        self.setModel(self.model)

        self.setAlternatingRowColors(True)
        self._create_context_menu()
        self.setIndentation(0)

    def _create_context_menu(self):
        horizontal_header = self._data.columns
        self.header().setContextMenuPolicy(Qt.ActionsContextMenu)

        for idx, header_item in enumerate(horizontal_header):
            self.item = QtWidgets.QAction(header_item, self)
            self.item.setCheckable(True)
            result = self._make_colum_show_or_hide(idx)
            self.item.triggered.connect(result)
            self.header().addAction(self.item)

    def _make_colum_show_or_hide(self, column_idx):
        show_column = lambda checked: self.setColumnHidden(column_idx, not checked)
        return show_column

    def restore_column_settings(self, settings, setting_path, defaults={}):
        if settings.value(setting_path):
            self.header().restoreState(settings.value(setting_path))
        else:
            for key in defaults:
                if defaults[key]['width']:
                    self.setColumnWidth(key, defaults[key]['width'])
                if defaults[key]['hidden']:
                    self.setColumnHidden(key, defaults[key]['hidden'])
        # Set check mark
        for col, action in enumerate(self.header().actions()):
            is_checked = not self.header().isSectionHidden(col)
            action.setChecked(is_checked)


class GuiTabWidget(QtWidgets.QTabWidget):

    def __init__(self, parent):
        super().__init__(parent)

        stylesheet = """
            QTabBar::tab:selected {background: gray;}
        """

        self.setStyleSheet(stylesheet)
        self.TabWidgetSearchTab1 = QtWidgets.QWidget()
        self.TabWidgetSearchTab2 = QtWidgets.QWidget()
        self.TabWidgetSearchTab3 = QtWidgets.QWidget()
        self.addTab(self.TabWidgetSearchTab1, 'Offline Search')
        self.addTab(self.TabWidgetSearchTab2, 'Online Search')
        self.addTab(self.TabWidgetSearchTab3, 'Suggest')


class MainWindow(Collection_view_common, Mix_view_common, View_common,
                 QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self, *args, obj=None, config_obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self.conf = config_obj  # Save passed DiscoDOS config object
        self.splitterVertical.setStretchFactor(1, 2)
        self.settings = QSettings(  # Initialize saving settings to ini file
            str(self.conf.discodos_data / 'gui_settings_autosave.ini'),
            QSettings.IniFormat
        )
        self.settings.setFallbacksEnabled(False)

        # Create vbox layouts and add to setlayout groupbox
        self.vboxMix = QtWidgets.QVBoxLayout()
        self.vboxMix.setContentsMargins(0, 0, 0, 0)
        self.vboxMix.setSpacing(2)
        self.groupBoxMix.setLayout(self.vboxMix)

        self.vboxTracks = QtWidgets.QVBoxLayout()
        self.vboxTracks.setContentsMargins(0, 0, 0, 0)
        self.groupBoxTracks.setLayout(self.vboxTracks)

        self.vboxResults = QtWidgets.QVBoxLayout()
        self.vboxResults.setContentsMargins(0, 0, 0, 0)
        self.groupBoxResults.setLayout(self.vboxResults)

        self.vboxSearch = QtWidgets.QVBoxLayout()
        self.vboxSearch.setContentsMargins(0, 0, 0, 0)
        self.groupBoxSearch.setLayout(self.vboxSearch)

        # Create treeviewmix
        self.treeViewMixHeader = self.headers_list_mixes
        self.treeviewmix_load()

        # Create tableviewtracks
        self.tableViewTracksHeader = self.headers_list_mixtracks_all
        self.tableviewtracks_load(None)

        # Create tableviewresults
        self.tableViewResultsHeader = self.headers_list_search_results
        self.tableviewresults_load()

        # Create TabWidget
        self.vboxTabWidgetSearchHorizontal = QtWidgets.QHBoxLayout()

        self.TabWidgetSearch = GuiTabWidget(self)

        self.pushButtonOfflineSearch = QtWidgets.QPushButton('Search')
        self.pushButtonOfflineSearch.clicked.connect(self.tabwidgetsearch_pushbutton_offline_search)
        self.pushButtonOfflineSearch.setShortcut('Shift+S')
        self.lineEditTrackOfflineSearchArtist = QtWidgets.QLineEdit()
        self.lineEditTrackOfflineSearchArtist.setPlaceholderText('Artist')
        self.lineEditTrackOfflineSearchArtist.returnPressed.connect(self.tabwidgetsearch_pushbutton_offline_search)
        self.lineEditTrackOfflineSearchRelease = QtWidgets.QLineEdit()
        self.lineEditTrackOfflineSearchRelease.setPlaceholderText('Release')
        self.lineEditTrackOfflineSearchRelease.returnPressed.connect(self.tabwidgetsearch_pushbutton_offline_search)
        self.lineEditTrackOfflineSearchTrack = QtWidgets.QLineEdit()
        self.lineEditTrackOfflineSearchTrack.setPlaceholderText('Track')
        self.lineEditTrackOfflineSearchTrack.returnPressed.connect(self.tabwidgetsearch_pushbutton_offline_search)

        self.TabWidgetSearch.TabWidgetSearchTab1.layout = QtWidgets.QGridLayout()
        self.TabWidgetSearch.TabWidgetSearchTab1.layout.setContentsMargins(0, 0, 0, 0)
        self.TabWidgetSearch.TabWidgetSearchTab1.layout.addWidget(self.lineEditTrackOfflineSearchArtist, 0, 0)
        self.TabWidgetSearch.TabWidgetSearchTab1.layout.addWidget(self.lineEditTrackOfflineSearchRelease, 1, 0)
        self.TabWidgetSearch.TabWidgetSearchTab1.layout.addWidget(self.lineEditTrackOfflineSearchTrack, 2, 0)

        verticaSpacerTabWidget = QtWidgets.QSpacerItem(0, 0,
                                                       QtWidgets.QSizePolicy.Minimum,
                                                       QtWidgets.QSizePolicy.Expanding)
        horizontalSpecerTabWidget = QtWidgets.QSpacerItem(0, 0,
                                                       QtWidgets.QSizePolicy.Expanding)

        self.vboxTabWidgetSearchHorizontal.addItem(horizontalSpecerTabWidget)
        self.vboxTabWidgetSearchHorizontal.addWidget(self.pushButtonOfflineSearch)
        self.TabWidgetSearch.TabWidgetSearchTab1.layout.addItem(
            self.vboxTabWidgetSearchHorizontal, 3, 0)

        self.TabWidgetSearch.TabWidgetSearchTab1.layout.addItem(
            verticaSpacerTabWidget, 4, 0)

        self.TabWidgetSearch.TabWidgetSearchTab1.setLayout(
            self.TabWidgetSearch.TabWidgetSearchTab1.layout)

        self.vboxSearch.addWidget(self.TabWidgetSearch)

        # Create Labels for info
        self.vboxLabelInfo = QtWidgets.QGridLayout()
        self.groupBoxInfo = QtWidgets.QGroupBox()
        self.groupBoxInfo.setObjectName('groupBoxInfo')
        self.groupBoxInfo.setTitle('Info')
        self.groupBoxInfo.setLayout(self.vboxLabelInfo)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidget(self.groupBoxInfo)
        scroll.setWidgetResizable(True)

        self.splitterHorizontal2.addWidget(scroll)

        self.label_list_box = dict()
        for idx, header_name in enumerate(self.tableViewResultsHeader):
            for idx2 in range(2):
                label = QtWidgets.QLabel()
                # Not sure if you want this, just an example
                header_name_text = header_name.replace('\n', ' ')
                label.setObjectName(header_name + str(idx2))

                if idx2 == 0:  # only show first column with text
                    label.setText(header_name_text + ':')

                # Keep referencs
                self.label_list_box[header_name + str(idx2)] = label

                self.vboxLabelInfo.addWidget(label, idx, idx2)

        verticalSpacervboxLabelInfo = QtWidgets.QSpacerItem(0, 0,
                                                    QtWidgets.QSizePolicy.Maximum,
                                                    QtWidgets.QSizePolicy.Expanding)

        horizontalSpacervboxLabelInfo = QtWidgets.QSpacerItem(0, 0,
                                                    QtWidgets.QSizePolicy.Expanding)
        # idx+1 add verticalSpacer on last row
        # This crops all labels to above
        self.vboxLabelInfo.addItem(verticalSpacervboxLabelInfo, idx+1, 0)
        # Horizontal spacer so text don't get stretched when moving
        # splitterHorizontal2 to left/right
        self.vboxLabelInfo.addItem(horizontalSpacervboxLabelInfo, idx, 2)

        # Create vbox formlayout for mixes buttons and edit boxes
        self.vboxFormLayout = QtWidgets.QFormLayout()

        # Create lineedit mix
        self.lineEditAddMix = QtWidgets.QLineEdit()
        self.lineEditAddMix.setPlaceholderText('Mix name')
        self.vboxFormLayout.addRow(self.lineEditAddMix)

        # Create lineedit mixvenue
        self.lineEditAddMixVenue = QtWidgets.QLineEdit()
        self.lineEditAddMixVenue.setPlaceholderText('Venue')
        self.vboxFormLayout.addRow(self.lineEditAddMixVenue)

        # Create lineedit mixdate
        self.lineEditAddMixDate = QtWidgets.QLineEdit()
        self.lineEditAddMixDate.setPlaceholderText('2021-01-01')
        self.vboxFormLayout.addRow(self.lineEditAddMixDate)

        # Create pushbutton add
        self.pushButtonAddMix = QtWidgets.QPushButton()
        self.pushButtonAddMix.setText('Add')
        self.pushButtonAddMix.clicked.connect(self.treeviewmix_pushbutton_add_mix)

        # Create pushbutton del
        self.pushButtonDelMix = QtWidgets.QPushButton()
        self.pushButtonDelMix.setText('Delete')
        self.pushButtonDelMix.clicked.connect(self.treeviewmix_pushbutton_del_mix)
        self.vboxFormLayout.addRow(self.pushButtonAddMix, self.pushButtonDelMix)

        # Add formlayout to mixes boxlayout
        self.vboxMix.addLayout(self.vboxFormLayout)

        # on first load, only mixes and releases are fetched and displayed
        self.initUI()
        # Restore layout from autosaved ini file
        self.read_ui_settings()

    def read_ui_settings(self):
        # Load settings from settings.ini or default if no .ini found
        self.settings.beginGroup('MainWindow')
        self.resize(self.settings.value('size', QtCore.QSize(1280, 768)))
        self.move(self.settings.value('pos', QtCore.QPoint(50, 50)))
        self.settings.endGroup()
        self.settings.beginGroup('Splitter')
        if self.settings.value('Horizontal'):
            self.splitterHorizontal.restoreState(self.settings.value('Horizontal'))
        if self.settings.value('Horizontal2'):
            self.splitterHorizontal2.restoreState(self.settings.value('Horizontal2'))
        if self.settings.value('Vertical'):
            self.splitterVertical.restoreState(self.settings.value('Vertical'))
        self.settings.endGroup()

        self.tableViewTracks.restore_column_settings(
            self.settings,
            "tableViewTracks/ColumnWidth",
            defaults=self.column_defaults_mixtracks
        )
        self.tableViewResults.restore_column_settings(
            self.settings,
            "tableViewResults/ColumnWidth",
            defaults=self.column_defaults_search_results
        )

        self.settings.beginGroup('treeViewMix')
        self.treeViewMix.restore_column_settings(
            self.settings,
            'ColumnWidth',
            defaults=self.column_defaults_treeview
        )
        self.settings.endGroup()

    def write_ui_settings(self):
        self.settings.beginGroup('MainWindow')
        self.settings.setValue('size', self.size())
        self.settings.setValue('pos', self.pos())
        self.settings.endGroup()
        self.settings.beginGroup('Splitter')
        self.settings.setValue('Horizontal', self.splitterHorizontal.saveState())
        self.settings.setValue('Horizontal2', self.splitterHorizontal2.saveState())
        self.settings.setValue('Vertical', self.splitterVertical.saveState())
        self.settings.endGroup()
        self.settings.beginGroup('tableViewTracks')
        self.settings.setValue('ColumnWidth', self.tableViewTracks.horizontalHeader().saveState())
        self.settings.endGroup()
        self.settings.beginGroup('tableViewResults')
        self.settings.setValue('ColumnWidth',self.tableViewResults.horizontalHeader().saveState())
        self.settings.endGroup()
        self.settings.beginGroup('treeViewMix')
        self.settings.setValue('ColumnWidth', self.treeViewMix.header().saveState())
        #
        # #self.settings.setValue('test', self.treeViewPlaylist.model().data(self.treeViewPlaylist.selectedIndexes()[1]))
        # #index = self.treeViewPlaylist.model().index(int(x), 0)
        # #playlist_id = self.treeViewPlaylist.model().data(index, Qt.DisplayRole)
        # self.settings.setValue("items", self.treeViewPlaylist.dataFromChild(self.invisibleRootItem()))
        #
        self.settings.endGroup()
        self.settings.sync()

    def closeEvent(self, e):
        """ On close saves window positions to ini file """
        # todo Question: When using cmd + q on a mac this closeEvent is called
        #  twice when using keyPressEventtreeViewMix and keyPressEventTableViewResults.
        #  Also changes are not saved in ini file.
        #  If you disable keyPressEventtreeViewMix and keyPressEventTableViewResults
        #  then settings are saved in .ini file
        #  Need to use self.settings.sync() in combination with
        #  keyPressEventtreeViewMix and keyPressEventTableViewResults
        #  Why is that?
        self.write_ui_settings()
        e.accept()

    def keyPressEventtreeViewMix(self, e: QtGui.QKeyEvent) -> None:
        if e.key() == QtCore.Qt.Key_Down or e.key() == QtCore.Qt.Key_Up:
            # It's important to send the event first before do the action
            # else you get the info from the selected row before or after
            QtWidgets.QTreeView.keyPressEvent(self.treeViewMix, e)
            # if you dont use this if and starts the app and press up then the app
            # crashes because of IndexError: list index out of range
            if self.treeViewMix.selectedIndexes():
                mix_id = self.treeViewMix.selectedIndexes()[0].data(Qt.DisplayRole)
                self.tableviewtracks_load(mix_id)

    def keyPressEventTableViewResults(self, e: QtGui.QKeyEvent) -> None:
        if e.key() == QtCore.Qt.Key_Down or e.key() == QtCore.Qt.Key_Up:
            # It's important to send the event first before do the action
            # else you get the info from the selected row before or after
            QtWidgets.QTableView.keyPressEvent(self.tableViewResults, e)
            index = self.tableViewResults.currentIndex()
            self.tableViewResultsOnClick(index)

    def initUI(self):
        self.treeviewmix_load()

    def treeviewmix_load(self):
        """ Loads mixes list from database and initializes treeViewMix.

        If vboxMix is empty, treeViewMix is created and added. Otherwise data
        is updated only.

        Returns: None

        The following instance variables are created by this method:
            self.treeViewMixDataFrame
            self.treeViewMix
        """
        mix = Mix(False, "all", db_file=self.conf.discobase)
        all_mixes = mix.get_all_mixes()
        all_mixes_list = []

        if all_mixes:
            timestamps_shortened = self.shorten_mixes_timestamps(all_mixes)
            for row in timestamps_shortened:
                all_mixes_list.append(
                    [str(row[key]) for key in row.keys()]
                )

        self.treeViewMixDataFrame = pd.DataFrame(
            all_mixes_list, columns=self.treeViewMixHeader)

        if self.vboxMix.isEmpty():
            # self.treeViewMixModel = QtGui.QStandardItemModel()
            # self.treeViewMix.setModel(self.treeViewMixModel)
            self.treeViewMix = GuiTreeView(self, self.treeViewMixDataFrame)
            self.treeViewMix.clicked.connect(self.treeviewmix_on_clicked)
            self.treeViewMix.keyPressEvent = self.keyPressEventtreeViewMix
            self.vboxMix.addWidget(self.treeViewMix)
        else:
            self.treeViewMix.model.update(self.treeViewMixDataFrame)

    def tableviewtracks_load(self, mix_name):
        """ Loads mixtracks from database and initializes tableViewTracks

        Args:
            mix_name (str): The name of the mix to load from database.
                If a mix_name of None is given, it's assumed we initialize
                tableViewTracks and add it to vboxTracks.
                If an existing mix_name is given, it's assumed tableViewTracks
                is existing already and just has to be updated with the fetched
                data.
        Returns: None

        The following instance variables are created by this method:
            self.tableViewTracksDataFrame
            self.tableViewTracks
        """
        mixtracks = None
        mixtracks_list = []
        if mix_name is not None:
            mix = Mix(False, mix_name, db_file=self.conf.discobase)
            mixtracks = mix.get_full_mix(verbose=True)

        if mixtracks:
            mixtracks_key_bpm_replaced = self.replace_key_bpm(mixtracks)
            for row in mixtracks_key_bpm_replaced:
                mixtracks_list.append(
                    [str(self.none_replace(row[key])) for key in row.keys()]
                )

        self.tableViewTracksDataFrame = pd.DataFrame(
            mixtracks_list, columns=self.tableViewTracksHeader)

        if mix_name is None:
            self.tableViewTracks = GuiTableView(
                self, self.tableViewTracksDataFrame)
            self.vboxTracks.addWidget(self.tableViewTracks)
        else:
            self.tableViewTracks.model.update(self.tableViewTracksDataFrame)

    def tableviewresults_load(self):
        self.tableViewResultsDataFrame = pd.DataFrame(
            [], columns=self.tableViewResultsHeader)

        self.tableViewResults = GuiTableView(
            self, self.tableViewResultsDataFrame)
        self.vboxResults.addWidget(self.tableViewResults)
        self.tableViewResults.clicked.connect(self.tableViewResultsOnClick)
        self.tableViewResults.keyPressEvent = self.keyPressEventTableViewResults

    def treeviewmix_on_clicked(self, index):
        index = index.sibling(index.row(), 0)
        playlist_id = self.treeViewMix.model.data(index, Qt.DisplayRole)
        self.tableviewtracks_load(playlist_id)
        print('playlist_id:', playlist_id)

    def tableViewResultsOnClick(self, index):
        row = index.row()
        value = self.tableViewResults.model.index(index.row(),
                                                  index.column()).data()
        if value.startswith('http://') or value.startswith('https://'):
            webbrowser.open(value)

        for idx, header_name in enumerate(self.tableViewResultsHeader):
            result = self.tableViewResults.model.index(row, idx).data()
            if result.startswith('http://') or result.startswith('https://'):
                url_link = " <a href=" + result + "> <color=blue>" + result + \
                           "</font> </a>"
                self.label_list_box[header_name + str(1)].setText(url_link)
                self.label_list_box[
                    header_name + str(1)].setOpenExternalLinks(
                    True)
            else:
                self.label_list_box[header_name + str(1)].setText(result)

    def treeviewmix_pushbutton_del_mix(self, index):
        playlist_id = self.treeViewMix.model.data(self.treeViewMix.selectedIndexes()[0])
        row_id = self.treeViewMix.selectionModel().currentIndex().row()
        try:
            self.treeViewMix.model.removeRow(row_id)

            playlist = Mix(False, playlist_id, self.conf.discobase)
            playlist.delete()
            log.info("GUI: Deleted Mix %s, from list and removed rowid %d from treeview", playlist_id, row_id)
        except:
            log.error("GUI; Failed to delete Mix! %s", playlist_id)

    def treeviewmix_pushbutton_add_mix(self):
        playlist_name = self.lineEditAddMix.text()
        playlist_venue = self.lineEditAddMixVenue.text()
        playlist_date = self.lineEditAddMixDate.text()
        if playlist_name != '':
            playlist = Mix(False, 'all', self.conf.discobase)
            playlist.create(playlist_date, playlist_venue, playlist_name)
            # self.lineEditAddPlaylistName.setText('')
            # self.lineEditAddPlaylistVenue.setText('')
            # self.lineEditAddPlaylistDate.setText('')
        else:
            print('no playlist name')

        # must be a better way to reload data on insert
        self.treeviewmix_load()

    def tabwidgetsearch_pushbutton_offline_search(self):
        search_results_list = []
        collection = Collection(False, self.conf.discobase)
        search_results = collection.search_release_track_offline(
            self.lineEditTrackOfflineSearchArtist.text(),
            self.lineEditTrackOfflineSearchRelease.text(),
            self.lineEditTrackOfflineSearchTrack.text()
        )
        if search_results:
            search_results_key_bpm_replaced = self.replace_key_bpm(
                search_results
            )
            for row in search_results_key_bpm_replaced:
                keys_list = []
                #print(row)
                for key, value in row.items():
                    if key == 'm_rel_id' and value is not None:
                        keys_list.append(
                            str(self.link_to("musicbrainz release", value))
                        )
                    elif key == 'm_rec_id' and value is not None and value != 0:
                        keys_list.append(
                            str(self.link_to("musicbrainz recording", value))
                        )
                    elif key == 'discogs_id' and value is not None:
                        keys_list.append(
                            str(self.link_to("discogs release", value))
                        )
                    else:
                        keys_list.append(
                            str(self.none_replace(value))
                        )
                search_results_list.append(keys_list)

            self.tableViewResultsDataFrame = pd.DataFrame(
                search_results_list,
                columns=self.tableViewResultsHeader
            )
            self.tableViewResults.model.update(self.tableViewResultsDataFrame)
        else:
            # Clear tableview when nothing found
            self.tableViewResultsDataFrame = pd.DataFrame(
                [], columns=self.tableViewResultsHeader)
            self.tableViewResults.model.update(self.tableViewResultsDataFrame)


def main():
    # Base configuration and setup tasks run on the shell
    conf = Config()
    # Initialize a Ctrl_common object - contains general DiscoDOS utils
    ctrl_common = Ctrl_common()
    ctrl_common.setup_db(conf.discobase)

    # Initialize GUI
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(config_obj=conf)
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
