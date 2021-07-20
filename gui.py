#!/usr/bin/env python

import sys
import pandas as pd
import logging
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QSettings, QModelIndex

import webbrowser

from discodos.qt.MainWindow import Ui_MainWindow
from discodos.models import Mix, Collection
from discodos.config import Config
from discodos.utils import is_number
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

    def read_settings(self, settings, key):
        if settings.value(key):
            self.horizontalHeader().restoreState(settings.value(key))
            # Set check mark
            for col, action in enumerate(self.horizontalHeader().actions()):
                is_checked = not self.horizontalHeader().isSectionHidden(col)
                action.setChecked(is_checked)


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

    def read_settings(self, settings, key):
        if settings.value(key):
            self.header().restoreState(settings.value(key))
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
        self.groupBoxReleases.setLayout(self.vboxResults)

        self.vboxTest = QtWidgets.QVBoxLayout()
        self.vboxTest.setContentsMargins(0, 0, 0, 0)
        self.groupBoxTest.setLayout(self.vboxTest)

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
        vSpacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        self.TabWidgetSearch = GuiTabWidget(self)

        self.pushButtonOfflineSearch = QtWidgets.QPushButton('Search')
        self.pushButtonOfflineSearch.clicked.connect(self.tabwidgetsearch_pushbutton_offline_search)
        self.lineEditTrackOfflineSearchArtist = QtWidgets.QLineEdit()
        self.lineEditTrackOfflineSearchArtist.setPlaceholderText('Artist')
        self.lineEditTrackOfflineSearchRelease = QtWidgets.QLineEdit()
        self.lineEditTrackOfflineSearchRelease.setPlaceholderText('Release')
        self.lineEditTrackOfflineSearchTrack = QtWidgets.QLineEdit()
        self.lineEditTrackOfflineSearchTrack.setPlaceholderText('Track')

        self.TabWidgetSearch.TabWidgetSearchTab1.layout = QtWidgets.QGridLayout()
        self.TabWidgetSearch.TabWidgetSearchTab1.layout.setContentsMargins(0, 0, 0, 0)

        self.TabWidgetSearch.TabWidgetSearchTab1.layout.addWidget(self.lineEditTrackOfflineSearchArtist, 0, 0)
        self.TabWidgetSearch.TabWidgetSearchTab1.layout.addWidget(self.lineEditTrackOfflineSearchRelease, 1, 0)
        self.TabWidgetSearch.TabWidgetSearchTab1.layout.addWidget(self.lineEditTrackOfflineSearchTrack, 2, 0)
        self.TabWidgetSearch.TabWidgetSearchTab1.layout.addWidget(self.pushButtonOfflineSearch, 3, 0)
        self.TabWidgetSearch.TabWidgetSearchTab1.layout.addItem(vSpacer, 4, 0)
        self.TabWidgetSearch.TabWidgetSearchTab1.setLayout(self.TabWidgetSearch.TabWidgetSearchTab1.layout)

        self.vboxTest.addWidget(self.TabWidgetSearch)

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
        if self.settings.value('Vertical'):
            self.splitterVertical.restoreState(self.settings.value('Vertical'))
        self.settings.endGroup()
        self.settings.beginGroup('tableViewTracks')
        # if self.settings.value('ColumnWidth'):
        #     self.tableViewTracks.horizontalHeader().restoreState(self.settings.value('ColumnWidth'))
        self.tableViewTracks.read_settings(self.settings, 'ColumnWidth')
        self.settings.beginGroup('tableViewResults')
        self.tableViewResults.read_settings(self.settings, 'ColumnWidth')
        self.settings.endGroup()
        self.settings.beginGroup('treeViewMix')
        # if self.settings.value('ColumnWidth'):
        self.treeViewMix.read_settings(self.settings, 'ColumnWidth')


            # self.treeViewMix.header().restoreState(self.settings.value('ColumnWidth'))
            #
            # if self.settings.value('SelectedPlaylist'):
            #     # self.model.setRootPath(self.settings.value('TreeFileSystem'))
            #     # index = self.model.index(str(self.path))
            #
            #     # index = self.model.index(str(self.settings.value('TreeViewPlaylist1')))
            #     row = self.settings.value('SelectedPlaylist')
            #
            #     x = int(row) - 1
            #     index = self.treeViewPlaylist.model().index(int(x), 0)
            #     # print(index)
            #     self.treeViewPlaylist.scrollTo(index)
            #     self.treeViewPlaylist.setCurrentIndex(index)
            #     self.tableviewplaylistsongs_load_data(row)
            #     # print(self.settings.value('SelectedPlaylist'))
        self.settings.endGroup()

    def write_ui_settings(self):
        self.settings.beginGroup('MainWindow')
        self.settings.setValue('size', self.size())
        self.settings.setValue('pos', self.pos())
        self.settings.endGroup()
        self.settings.beginGroup('Splitter')
        self.settings.setValue('Horizontal', self.splitterHorizontal.saveState())
        self.settings.setValue('Vertical', self.splitterVertical.saveState())
        self.settings.endGroup()
        self.settings.beginGroup('tableViewTracks')
        self.settings.setValue('ColumnWidth', self.tableViewTracks.horizontalHeader().saveState())
        self.settings.endGroup()
        self.settings.beginGroup('tableViewResults')
        self.settings.setValue(
            'ColumnWidth',
            self.tableViewResults.horizontalHeader().saveState()
        )
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

    def closeEvent(self, e):
        """ On close saves window positions to ini file """
        self.write_ui_settings()
        e.accept()

    def keyPressEvent(self, event):
        if (event.key() == Qt.Key_Shift
                and self.treeViewMix.hasFocus() is True
                and self.treeViewMix.selectedIndexes()):
            mix_id = self.treeViewMix.selectedIndexes()[0].data(Qt.DisplayRole)
            self.tableviewtracks_load(mix_id)
            event.accept()

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
            self.treeViewMix.setColumnWidth(0, 30)     # Mix ID
            self.treeViewMix.setColumnHidden(0, True)  # Mix ID
            self.treeViewMix.setColumnWidth(2, 90)     # Played
            self.treeViewMix.setColumnHidden(4, True)  # Created
            self.treeViewMix.setColumnHidden(5, True)  # Updated
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
            # Set default column width and visible state
            self.tableViewTracks.setColumnWidth(0, 30)     # Track Pos.
            self.tableViewTracks.setColumnHidden(1, True)  # Release
            self.tableViewTracks.setColumnWidth(2, 120)    # Artist
            self.tableViewTracks.setColumnWidth(3, 180)    # Title
            self.tableViewTracks.setColumnWidth(4, 30)     # Trk No
            self.tableViewTracks.setColumnWidth(5, 50)     # Key
            self.tableViewTracks.setColumnWidth(6, 45)     # BPM
            self.tableViewTracks.setColumnWidth(7, 58)     # Key Notes
            self.tableViewTracks.setColumnWidth(8, 58)     # Transition Rating
            self.tableViewTracks.setColumnWidth(9, 58)     # Transition Notes
            self.tableViewTracks.setColumnWidth(10, 55)    # Track Notes
            self.vboxTracks.addWidget(self.tableViewTracks)
        else:
            self.tableViewTracks.model.update(self.tableViewTracksDataFrame)

    def tableviewresults_load(self):
        self.tableViewResultsDataFrame = pd.DataFrame(
            [], columns=self.tableViewResultsHeader)

        self.tableViewResults = GuiTableView(
            self, self.tableViewResultsDataFrame)
        # set default column width and visible state
        self.tableViewResults.setColumnWidth(0, 120)     # Artist
        self.tableViewResults.setColumnWidth(1, 180)     # Title
        self.tableViewResults.setColumnWidth(2, 90)      # Catalog
        self.tableViewResults.setColumnWidth(3, 30)      # Trk No
        self.tableViewResults.setColumnWidth(4, 50)      # Key
        self.tableViewResults.setColumnWidth(5, 45)      # BPM
        self.tableViewResults.setColumnWidth(6, 58)      # Key Notes
        self.tableViewResults.setColumnHidden(6, True)   # Key Notes
        self.tableViewResults.setColumnWidth(7, 58)      # Track Notes
        self.tableViewResults.setColumnHidden(7, True)   # Track Notes
        self.tableViewResults.setColumnWidth(8, 70)      # Discogs Release ID
        self.tableViewResults.setColumnHidden(8, True)   # Discogs Release ID
        self.tableViewResults.setColumnHidden(10, True)  # Release
        self.tableViewResults.setColumnWidth(11, 30)     # In Discogs Coll.
        self.tableViewResults.setColumnHidden(11, True)  # In Discogs Coll.
        self.tableViewResults.setColumnWidth(12, 80)     # MusicBrainz ID
        self.tableViewResults.setColumnWidth(13, 80)     # MusicBrainz ID Overr.
        self.tableViewResults.setColumnWidth(14, 100)    # MusicBrainz Match M.
        self.tableViewResults.setColumnWidth(15, 100)     # MusicBrainz Match T.
        self.vboxResults.addWidget(self.tableViewResults)
        self.tableViewResults.clicked.connect(self.tableViewResultsOnClick)

    def treeviewmix_on_clicked(self, index):
        index = index.sibling(index.row(), 0)
        playlist_id = self.treeViewMix.model.data(index, Qt.DisplayRole)
        self.tableviewtracks_load(playlist_id)
        print('playlist_id:', playlist_id)

    def tableviewresults_on_click(self, index):
        indexes = self.tableViewResults.selectionModel().selectedRows()
        for index in indexes:
            print(
                self.tableViewResults.model.data(
                    self.tableViewResults.model.index(index.row(), 3)
                )
            )

    def tableViewResultsOnClick(self, index):
        print(index.row())
        value = self.tableViewResults.model.index(index.row(), index.column()).data()
        if value.startswith("http://") or value.startswith("https://"):
            webbrowser.open(value)

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
