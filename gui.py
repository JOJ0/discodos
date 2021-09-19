#!/usr/bin/env python
import sys
import pandas as pd
import logging
import webbrowser
import re
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QSettings, QModelIndex
# import pprint

from discodos.qt.MainWindow import Ui_MainWindow
from discodos.model_mix import Mix
from discodos.model_collection import Collection
from discodos.config import Config
from discodos.ctrls import Ctrl_common
from discodos.view_common import View_common
from discodos.view_common import Mix_view_common, Collection_view_common

log = logging.getLogger('discodos')


class QtUtilsMixIn:
    """Provides common utils usable in TreeView and TableView instances.

    Currently this involves handling of column settings and context menus.
    """
    def _create_context_menu(self, header):
        """Creates context menu for TreeView or TableView headers

        Args:
            header (method): Either a reference to a treeview.header() or a
                tableview.horizontalHeader() method
        """
        pandas_header = self._data.columns
        header().setContextMenuPolicy(Qt.ActionsContextMenu)

        for idx, header_name in enumerate(pandas_header):
            header_name_stripped = header_name.replace("\n", " ")
            self.item = QtWidgets.QAction(header_name_stripped, self)
            self.item.setCheckable(True)
            result = self._make_colum_show_or_hide(idx)
            self.item.triggered.connect(result)
            header().addAction(self.item)

    def _make_colum_show_or_hide(self, column_idx):
        show_column = lambda checked: self.setColumnHidden(column_idx, not checked)
        return show_column

    def restore_column_settings(self, settings, setting_path, defaults=None,
                                header=None):
        """ Restores column width and visible-state from Qsettings

        or falls back to using defaults (if provided). Also sets check marks
        in right click on headers context menu according to visible-state of
        columns.

        Args:
            settings (object): A QSettings object.
            setting_path (string): The path to the setting in the Qsettings
                object aka the .ini file. Format: section/keyname.
            defaults (object): TableDefaults object containing
                width, hidden and editable state.
            header (method): Either a reference to a treeview.header() or a
                tableview.horizontalHeader() method

        Returns: None
        """
        if settings.value(setting_path):
            log.info("TableView.restore_column_settings: "
                     "Restoring from saved settings.")
            header().restoreState(settings.value(setting_path))
        else:
            log.info("TableView.restore_column_settings: "
                     "No saved settings found. Using defaults.")

            # pprint.pprint(defaults.cols)
            for settings in defaults.cols.values():
                if settings['width']:
                    self.setColumnWidth(
                        settings['order_id'],
                        settings['width']
                    )
                if settings['hidden']:
                    self.setColumnHidden(
                        settings['order_id'],
                        settings['hidden']
                    )

        # Set context menu check marks according to visible-state of columns
        for col, action in enumerate(header().actions()):
            action.setChecked(not header().isSectionHidden(col))


class TableViewModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        super(TableViewModel, self).__init__()
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
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled
        return Qt.ItemIsEnabled

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

    def sort(self, column, order):
        colname = self._data.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self._data.sort_values(colname, ascending=order == QtCore.Qt.AscendingOrder, inplace=True)
        # self._data.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()


class TableViewTracksModel(TableViewModel, Mix_view_common, View_common):
    def __init__(self, data):
        super().__init__(data)

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        if index.isValid():
            locked = self.cols_mixtracks.get_locked_columns()
            if index.column() in locked:
                return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled
            else:
                return Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled
        else:
            return Qt.ItemIsDropEnabled

    def setData(self, index: QModelIndex, value, role: int = ...) -> bool:
        if role == Qt.EditRole:
            self._data.iloc[index.row()][index.column()] = value
            self.dataChanged.emit(index, index, (Qt.DisplayRole, ))
        return True


class TableViewResultsModel(TableViewModel, Collection_view_common, View_common):
    def __init__(self, data):
        super().__init__(data)

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        if index.isValid():
            locked = self.cols_search_results.get_locked_columns()
            if index.column() in locked:
                return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled
            else:
                return Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled
        else:
            return Qt.ItemIsDropEnabled


class TableViewProxyStyle(QtWidgets.QProxyStyle):

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


class TableView(QtUtilsMixIn, QtWidgets.QTableView):
    """Initializes common settings used in all tableviews."""

    def __init__(self, parent, data):
        super().__init__(parent)
        self._data = data
        # self.verticalHeader().hide()
        # self.horizontalHeader().hide()
        # self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.SingleSelection)
        self.setShowGrid(False)

        # Original drag drop stuff from embee
        self.setDragDropMode(self.InternalMove)
        self.setDragDropOverwriteMode(False)
        # Enable drag drop of column headers (reorder columns position)
        self.horizontalHeader().setSectionsMovable(True)
        # Drag drop of lines (manual reordering) seems to work somehow,
        # even without these two settings:
        # self.horizontalHeader().setDropIndicatorShown(False)
        # print(self.horizontalHeader().showDropIndicator())
        # self.horizontalHeader().setDragEnabled(False)
        # print(self.horizontalHeader().dragEnabled())

        self.setStyle(TableViewProxyStyle())
        self.setAlternatingRowColors(True)
        self._create_context_menu(self.horizontalHeader)
        self.setSortingEnabled(True)
        # self.sortByColumn(1, Qt.AscendingOrder


class TableViewTracks(TableView):
    def __init__(self, parent, data):
        super().__init__(parent, data)
        self._data = data
        self.model = TableViewTracksModel(self._data)
        self.setModel(self.model)


class TableViewResults(TableView):
    def __init__(self, parent, data):
        super().__init__(parent, data)
        self._data = data
        self.model = TableViewResultsModel(self._data)
        self.setModel(self.model)


class TreeViewModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        super(TreeViewModel, self).__init__()
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

    def sort(self, column, order):
        colname = self._data.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self._data.sort_values(
            colname,
            ascending=order == QtCore.Qt.AscendingOrder,
            inplace=True
        )
        self.layoutChanged.emit()


class TreeView(QtUtilsMixIn, QtWidgets.QTreeView):
    def __init__(self, parent, data):
        super().__init__(parent)
        self._data = data
        self.model = TreeViewModel(self._data)
        self.setModel(self.model)
        self.setAlternatingRowColors(True)
        # Enable drag drop of column headers (reorder columns position), default
        # on in treeviews, set explicitely.
        self.header().setSectionsMovable(True)

        self._create_context_menu(self.header)
        self.setIndentation(0)

        # FIXME sorting not working yet.
        self.setSortingEnabled(True)
        # print(self.isSortingEnabled())
        self.header().setSortIndicatorShown(True)
        # print(self.header().isSortIndicatorShown())
        self.sortByColumn(1, Qt.AscendingOrder)


class TabWidget(QtWidgets.QTabWidget):

    def __init__(self, parent):
        super().__init__(parent)

        stylesheet = """
            QTabBar::tab:selected {background: gray;}
        """

        self.setStyleSheet(stylesheet)
        self.TabWidgetSearchTab1 = QtWidgets.QWidget()
        self.TabWidgetSearchTab2 = QtWidgets.QWidget()
        self.TabWidgetSearchTab3 = QtWidgets.QWidget()
        self.addTab(self.TabWidgetSearchTab1, 'Offline')
        self.addTab(self.TabWidgetSearchTab2, 'Online')
        self.addTab(self.TabWidgetSearchTab3, 'Suggest')


class MainWindow(Collection_view_common, Mix_view_common, View_common,
                 QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self, *args, obj=None, config_obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self.conf = config_obj  # Save passed DiscoDOS config object
        self.splitterVertical.setStretchFactor(1, 2)
        ini_file = str(self.conf.discodos_data / 'gui_settings_autosave.ini')
        log.info("GUI: Initializing self.settings from %s", ini_file)
        self.settings = QSettings(ini_file, QSettings.IniFormat)
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
        self.treeViewMixHeader = self.cols_mixes.headers_list()
        self.treeViewMixLoad()

        # Create tableviewtracks
        self.tableViewTracksHeader = self.cols_mixtracks.headers_list()
        self.tableViewTracksLoad(None)

        # Create tableviewresults
        self.tableViewResultsHeader = self.cols_search_results.headers_list()
        self.tableViewResultsLoad()

        # Create TabWidget
        self.vboxTabWidgetSearchHorizontal = QtWidgets.QHBoxLayout()
        self.TabWidgetSearch = TabWidget(self)

        self.pushButtonOfflineSearch = QtWidgets.QPushButton('Search')
        self.pushButtonOfflineSearch.clicked.connect(self.tabWidgetOfflineSearchButtonOnClick)
        self.pushButtonOfflineSearch.setShortcut('Shift+S')
        self.lineEditOfflineSearchArtist = QtWidgets.QLineEdit()
        self.lineEditOfflineSearchArtist.setPlaceholderText('Artist')
        self.lineEditOfflineSearchArtist.returnPressed.connect(self.tabWidgetOfflineSearchButtonOnClick)
        self.lineEditOfflineSearchRelease = QtWidgets.QLineEdit()
        self.lineEditOfflineSearchRelease.setPlaceholderText('Release')
        self.lineEditOfflineSearchRelease.returnPressed.connect(self.tabWidgetOfflineSearchButtonOnClick)
        self.lineEditOfflineSearchTrack = QtWidgets.QLineEdit()
        self.lineEditOfflineSearchTrack.setPlaceholderText('Track')
        self.lineEditOfflineSearchTrack.returnPressed.connect(self.tabWidgetOfflineSearchButtonOnClick)

        self.TabWidgetSearch.TabWidgetSearchTab1.layout = QtWidgets.QGridLayout()
        self.TabWidgetSearch.TabWidgetSearchTab1.layout.setContentsMargins(0, 0, 0, 0)
        self.TabWidgetSearch.TabWidgetSearchTab1.layout.addWidget(self.lineEditOfflineSearchArtist, 0, 0)
        self.TabWidgetSearch.TabWidgetSearchTab1.layout.addWidget(self.lineEditOfflineSearchRelease, 1, 0)
        self.TabWidgetSearch.TabWidgetSearchTab1.layout.addWidget(self.lineEditOfflineSearchTrack, 2, 0)
        verticaSpacerTabWidget = QtWidgets.QSpacerItem(
            0, 0,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding
        )
        horizontalSpacerTabWidget = QtWidgets.QSpacerItem(
            0, 0,
            QtWidgets.QSizePolicy.Expanding
        )
        self.vboxTabWidgetSearchHorizontal.addItem(horizontalSpacerTabWidget)
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
        # only after after adding the scroll widget we can scucessfully set the
        # default stretchfactor
        self.splitterHorizontal2.setStretchFactor(1, 1)

        self.label_list_box = dict()
        self.populate_info_box(self.tableViewResultsHeader)


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
        self.pushButtonAddMix.clicked.connect(self.treeViewMixButtonAdd)

        # Create pushbutton del
        self.pushButtonDelMix = QtWidgets.QPushButton()
        self.pushButtonDelMix.setText('Delete')
        self.pushButtonDelMix.clicked.connect(self.treeViewMixButtonDel)
        self.vboxFormLayout.addRow(self.pushButtonAddMix, self.pushButtonDelMix)

        # Add formlayout to mixes boxlayout
        self.vboxMix.addLayout(self.vboxFormLayout)

        # on first load, only mixes are fetched and displayed in vboxMix
        self.treeViewMixLoad()
        # Restore layout from autosaved ini file
        self.readSettings()

    def readSettings(self):
        """ Load settings from self.settings.

        If a settings key could not be loaded (reading ini file happens in
        __init__) then some settings will use built-in defaults, others use
        provided defaults saved in views.py.
        """
        log.info("GUI: Loading settings from self.settings.")
        self.resize(self.settings.value('MainWindow/size',
                                        QtCore.QSize(1280, 768)))
        self.move(self.settings.value('MainWindow/pos',
                                      QtCore.QPoint(50, 50)))
        if self.settings.value('Splitter/Horizontal'):
            self.splitterHorizontal.restoreState(self.settings.value(
                'Splitter/Horizontal'
            ))
        if self.settings.value('Splitter/Horizontal2'):
            self.splitterHorizontal2.restoreState(self.settings.value(
                'Splitter/Horizontal2'
            ))
        if self.settings.value('Splitter/Vertical'):
            self.splitterVertical.restoreState(self.settings.value(
                'Splitter/Vertical'
            ))
        self.tableViewTracks.restore_column_settings(
            self.settings,
            "tableViewTracks/ColumnWidth",
            defaults=self.cols_mixtracks,
            header=self.tableViewTracks.horizontalHeader,
        )
        self.tableViewResults.restore_column_settings(
            self.settings,
            "tableViewResults/ColumnWidth",
            defaults=self.cols_search_results,
            header=self.tableViewResults.horizontalHeader,
        )
        self.treeViewMix.restore_column_settings(
            self.settings,
            'treeViewMix/ColumnWidth',
            defaults=self.cols_mixes,
            header=self.treeViewMix.header,
        )

    def writeSettings(self):
        log.info("GUI: Saving settings to self.settings.")
        self.settings.setValue('MainWindow/size', self.size())
        self.settings.setValue('MainWindow/pos', self.pos())
        self.settings.setValue('Splitter/Horizontal',
                               self.splitterHorizontal.saveState())
        self.settings.setValue('Splitter/Horizontal2',
                               self.splitterHorizontal2.saveState())
        self.settings.setValue('Splitter/Vertical',
                               self.splitterVertical.saveState())
        self.settings.setValue(
            'tableViewTracks/ColumnWidth',
            self.tableViewTracks.horizontalHeader().saveState())
        self.settings.setValue(
            'tableViewResults/ColumnWidth',
            self.tableViewResults.horizontalHeader().saveState())
        self.settings.setValue(
            'treeViewMix/ColumnWidth',
            self.treeViewMix.header().saveState())
        self.settings.sync()

    def closeEvent(self, e):
        """ When application closes this method calls writeSettings """
        # todo Question: When using cmd + q on a mac this closeEvent is called
        #  twice when using keyPressEventTreeViewMix and keyPressEventTableViewResults.
        #  Also changes are not saved in ini file.
        #  If you disable keyPressEventTreeViewMix and keyPressEventTableViewResults
        #  then settings are saved in .ini file
        #  Need to use self.settings.sync() in combination with
        #  keyPressEventTreeViewMix and keyPressEventTableViewResults
        #  Why is that?
        log.info("GUI: Application is closing.")
        self.writeSettings()
        e.accept()

    def keyPressEventTreeViewMix(self, e: QtGui.QKeyEvent) -> None:
        if e.key() == QtCore.Qt.Key_Down or e.key() == QtCore.Qt.Key_Up:
            # It's important to send the event first before do the action
            # else you get the info from the selected row before or after
            QtWidgets.QTreeView.keyPressEvent(self.treeViewMix, e)
            self.treeViewMixOnClick(self.treeViewMix.currentIndex())

    def keyPressEventTableViewResults(self, e: QtGui.QKeyEvent) -> None:
        if e.key() == QtCore.Qt.Key_Down or e.key() == QtCore.Qt.Key_Up:
            # It's important to send the event first before do the action
            # else you get the info from the selected row before or after
            QtWidgets.QTableView.keyPressEvent(self.tableViewResults, e)
            index = self.tableViewResults.currentIndex()
            self.tableViewResultsOnClick(index)

    def treeViewMixLoad(self):
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
            self.treeViewMix = TreeView(self, self.treeViewMixDataFrame)
            self.treeViewMix.clicked.connect(self.treeViewMixOnClick)
            self.treeViewMix.keyPressEvent = self.keyPressEventTreeViewMix
            self.vboxMix.addWidget(self.treeViewMix)
        else:
            self.treeViewMix.model.update(self.treeViewMixDataFrame)

    def tableViewTracksLoad(self, mix_id):
        """ Loads mixtracks from database and initializes tableViewTracks

        Args:
            mix_id (str): The ID of the mix to load from database.
                If mix_id is not None we fetch from db.
                If vboxTracks is still empty we initialize tableViewTracks and
                add it to the vbox, otherwise we assume it's there already and
                update it with the fetched data or an empty list.
        Returns: None

        The following instance variables are created by this method:
            self.tableViewTracksDataFrame
            self.tableViewTracks
        """
        mixtracks = None
        mixtracks_list = []
        if mix_id is not None:
            mix = Mix(False, mix_id, db_file=self.conf.discobase)
            self.active_mix_id = mix.id
            mixtracks = mix.get_full_mix(verbose=True)

        if mixtracks:
            mixtracks_key_bpm_replaced = self.replace_key_bpm(mixtracks)
            for row in mixtracks_key_bpm_replaced:
                mixtracks_list.append(
                    [str(self.none_replace(row[key])) for key in row.keys()]
                )

        self.tableViewTracksDataFrame = pd.DataFrame(
            mixtracks_list, columns=self.tableViewTracksHeader)

        if self.vboxTracks.isEmpty():
            self.tableViewTracks = TableViewTracks(
                self, self.tableViewTracksDataFrame
            )
            self.vboxTracks.addWidget(self.tableViewTracks)
            self.tableViewTracks.model.dataChanged.connect(self.tableViewTracksWrite)
        else:
            self.tableViewTracks.model.update(self.tableViewTracksDataFrame)

    def tableViewResultsLoad(self):
        self.tableViewResultsDataFrame = pd.DataFrame(
            [], columns=self.tableViewResultsHeader)

        self.tableViewResults = TableViewResults(self, self.tableViewResultsDataFrame)
        self.vboxResults.addWidget(self.tableViewResults)
        self.tableViewResults.clicked.connect(self.tableViewResultsOnClick)
        self.tableViewResults.keyPressEvent = self.keyPressEventTableViewResults

    def treeViewMixOnClick(self, index):
        mix_id = self.treeViewMix.model.data(
            index.sibling(index.row(), 0),
            Qt.DisplayRole
        )
        self.tableViewTracksLoad(mix_id)

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

    def treeViewMixButtonDel(self, index):
        playlist_id = self.treeViewMix.model.data(self.treeViewMix.selectedIndexes()[0])
        row_id = self.treeViewMix.selectionModel().currentIndex().row()
        try:
            self.treeViewMix.model.removeRow(row_id)

            playlist = Mix(False, playlist_id, self.conf.discobase)
            playlist.delete()
            log.info("GUI: Deleted Mix %s, from list and removed rowid %d from treeview", playlist_id, row_id)
        except:
            log.error("GUI; Failed to delete Mix! %s", playlist_id)

    def treeViewMixButtonAdd(self):
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
        self.treeViewMixLoad()

    def tabWidgetOfflineSearchButtonOnClick(self):
        search_results_list = []
        collection = Collection(False, self.conf.discobase)
        search_results = collection.search_release_track_offline(
            self.lineEditOfflineSearchArtist.text(),
            self.lineEditOfflineSearchRelease.text(),
            self.lineEditOfflineSearchTrack.text()
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

    def populate_info_box(self, headers_list):
        for idx, header_name in enumerate(headers_list):
            for idx2 in range(2):
                label = QtWidgets.QLabel()
                name_parts = re.findall(r'\S+|\s', header_name)
                new_header_name = ''
                for pidx, part in enumerate(name_parts):
                    if pidx < 3:
                        if part == '\n':
                            new_header_name += ' '
                        else:
                            new_header_name += part
                    else:
                        if len(header_name) < 20 and part == '\n':
                            new_header_name += ' '
                        else:
                            new_header_name += part
                label.setObjectName(new_header_name + str(idx2))

                if idx2 == 0:  # only show first column with text
                    label.setText(new_header_name + ':')

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

    def tableViewTracksWrite(self, index):
        track_pos = index.model().data(
            self.tableViewTracks.selectedIndexes()[0]
        )
        # print(track_pos)
        # print(index.column())
        mix = Mix(False, self.active_mix_id, db_file=self.conf.discobase)
        track_details = mix.get_one_mix_track(track_pos)
        headerCaption = index.model().headerData(index.column(), Qt.Horizontal)
        for col, caption in self.headers_dict_mixtracks_all.items():
            if caption == headerCaption:
                edited_col = col
        edited_value = index.model()._data.iloc[index.row()][index.column()]
        mix.update_mix_track_and_track_ext(
            track_details, {edited_col: edited_value}
        )
        self.tableViewTracksLoad(self.active_mix_id)


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
