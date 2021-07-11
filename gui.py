#!/usr/bin/env python

import sys
import pandas as pd
import logging
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QSettings, QModelIndex

from discodos.qt.MainWindow import Ui_MainWindow
from discodos.models import Mix, Collection
from discodos.config import Config
from discodos.utils import is_number
from discodos.ctrls import Ctrl_common
from discodos.views import View_common, Mix_view_common


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


class MainWindow(Mix_view_common, View_common, QtWidgets.QMainWindow,
                 Ui_MainWindow):

    def __init__(self, *args, obj=None, config_obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self.conf = config_obj
        self.splitter_vertical.setStretchFactor(1, 2)
        self.settings = QSettings(
            str(self.conf.discodos_data / 'gui_settings_autosave.ini'),
            QSettings.IniFormat
        )
        self.settings.setFallbacksEnabled(False)

        # create vbox layouts and add to setlayout groupbox
        self.vboxMix = QtWidgets.QVBoxLayout()
        self.vboxMix.setContentsMargins(0, 0, 0, 0)
        self.vboxMix.setSpacing(2)
        self.groupBoxMix.setLayout(self.vboxMix)

        self.vboxTracks = QtWidgets.QVBoxLayout()
        self.vboxTracks.setContentsMargins(0, 0, 0, 0)
        self.groupBoxTracks.setLayout(self.vboxTracks)

        self.vboxReleases = QtWidgets.QVBoxLayout()
        self.vboxReleases.setContentsMargins(0, 0, 0, 0)
        self.groupBoxReleases.setLayout(self.vboxReleases)

        self.vboxTest = QtWidgets.QVBoxLayout()
        self.vboxTest.setContentsMargins(0, 0, 0, 0)
        self.groupBoxTest.setLayout(self.vboxTest)

        # create treeviewmix
        # todo need suggestion for data_list
        self.data_list = []
        self.TreeViewMixHeader = self.headers_list_mixes
        self.TreeViewMixDataFrame = pd.DataFrame(
            self.data_list, columns=self.TreeViewMixHeader)
        self.treeViewMix = GuiTreeView(self, self.TreeViewMixDataFrame)
        # self.treeViewMixModel = QtGui.QStandardItemModel()
        # self.treeViewMix.setModel(self.treeViewMixModel)
        self.treeViewMix.clicked.connect(self.treeviewmix_on_clicked)
        self.treeViewMix.setColumnWidth(0, 30)
        self.vboxMix.addWidget(self.treeViewMix)

        # create tableviewtracks
        self.TableViewTracksHeader = self.headers_list_mixtracks_all
        self.tableviewtracks_load(None)

        # create tableviewreleases
        self.TableViewReleasesHeader = ['d_catno', 'd_artist', 'discogs_title', 'discogs_id', 'm_rel_id', 'm_rel_id_override']
        self.TableViewReleasesDataFrame = pd.DataFrame(
            self.data_list, columns=self.TableViewReleasesHeader)
        self.TableViewReleases = GuiTableView(
            self, self.TableViewReleasesDataFrame)
        self.TableViewReleases.clicked.connect(self.tableviewreleases_on_click)
        self.vboxReleases.addWidget(self.TableViewReleases)

        # Create TabWidget
        self.TabWidgetSearch = GuiTabWidget(self)
        self.vboxTest.addWidget(self.TabWidgetSearch)

        # create vbox formlayout for buttons and edit box
        self.vboxFormLayout = QtWidgets.QFormLayout()

        # lineedit mix
        self.lineEditAddMix = QtWidgets.QLineEdit()
        self.lineEditAddMix.setPlaceholderText('Mix name')
        self.vboxFormLayout.addRow(self.lineEditAddMix)

        # lineedit mixvenue
        self.lineEditAddMixVenue = QtWidgets.QLineEdit()
        self.lineEditAddMixVenue.setPlaceholderText('Venue')
        self.vboxFormLayout.addRow(self.lineEditAddMixVenue)

        # lineedit mixdate
        self.lineEditAddMixDate = QtWidgets.QLineEdit()
        self.lineEditAddMixDate.setPlaceholderText('2021-01-01')
        self.vboxFormLayout.addRow(self.lineEditAddMixDate)

        # pushbuttonadd
        self.pushButtonAddMix = QtWidgets.QPushButton()
        self.pushButtonAddMix.setText('Add')
        self.pushButtonAddMix.clicked.connect(self.treeviewmix_pushbutton_add_mix)

        #pushbuttondel
        self.pushButtonDelMix = QtWidgets.QPushButton()
        self.pushButtonDelMix.setText('Delete')
        self.pushButtonDelMix.clicked.connect(self.treeviewmix_pushbutton_del_mix)
        self.vboxFormLayout.addRow(self.pushButtonAddMix, self.pushButtonDelMix)

        # add formlayout to playlist boxlayout
        self.vboxMix.addLayout(self.vboxFormLayout)

        self.initUI()
        # Restore layout
        self.read_ui_settings()

    def read_ui_settings(self):
        # Load settings from settings.ini or default if no .ini found
        self.settings.beginGroup('MainWindow')
        self.resize(self.settings.value('size', QtCore.QSize(1280, 768)))
        self.move(self.settings.value('pos', QtCore.QPoint(50, 50)))
        self.settings.endGroup()
        self.settings.beginGroup('Splitter')
        if self.settings.value('Horizontal'):
            self.splitter_horizontal.restoreState(self.settings.value('Horizontal'))
        if self.settings.value('Vertical'):
            self.splitter_vertical.restoreState(self.settings.value('Vertical'))
        self.settings.endGroup()
        self.settings.beginGroup('TableViewTracks')
        # if self.settings.value('ColumnWidth'):
        #     self.TableViewTracks.horizontalHeader().restoreState(self.settings.value('ColumnWidth'))
        self.TableViewTracks.read_settings(self.settings, 'ColumnWidth')
        self.settings.endGroup()
        self.settings.beginGroup('TableViewReleases')
        # if self.settings.value('ColumnWidth'):
        #    self.TableViewReleases.horizontalHeader().restoreState(self.settings.value('ColumnWidth'))
        self.TableViewReleases.read_settings(self.settings, 'ColumnWidth')
        self.settings.endGroup()
        self.settings.beginGroup('TreeViewMix')
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
        self.settings.setValue('Horizontal', self.splitter_horizontal.saveState())
        self.settings.setValue('Vertical', self.splitter_vertical.saveState())
        self.settings.endGroup()
        self.settings.beginGroup('TableViewTracks')
        self.settings.setValue('ColumnWidth', self.TableViewTracks.horizontalHeader().saveState())
        self.settings.endGroup()
        self.settings.beginGroup('TableViewReleases')
        self.settings.setValue('ColumnWidth', self.TableViewReleases.horizontalHeader().saveState())
        self.settings.endGroup()
        self.settings.beginGroup('TreeViewMix')
        self.settings.setValue('ColumnWidth', self.treeViewMix.header().saveState())
        #
        # #self.settings.setValue('test', self.treeViewPlaylist.model().data(self.treeViewPlaylist.selectedIndexes()[1]))
        # #index = self.treeViewPlaylist.model().index(int(x), 0)
        # #playlist_id = self.treeViewPlaylist.model().data(index, Qt.DisplayRole)
        # self.settings.setValue("items", self.treeViewPlaylist.dataFromChild(self.invisibleRootItem()))
        #
        self.settings.endGroup()

    # on close save window positions
    def closeEvent(self, e):
        self.write_ui_settings()
        e.accept()

    def initUI(self):
        self.treeviewmix_load_data()
        self.tableviewreleases_load_data()

    def treeviewmix_load_data(self):
        sql_data = []

        load_mix = Mix(False, 'all', self.conf.discobase)
        sql_result = load_mix.get_all_mixes()

        row = ''
        if sql_result:
            timestamps_shortened = self.shorten_mixes_timestamps(sql_result)
            for row in timestamps_shortened:
                sql_data.append([str(row[x]) for x in row.keys()])

            self.TreeViewMixDataFrame = pd.DataFrame(sql_data, columns=self.TreeViewMixHeader)
            self.treeViewMix.model.update(self.TreeViewMixDataFrame)

    def tableviewtracks_load(self, mix_name):
        """ Loads mixtracks from database and initializes TableViewTracks

        Args:
            mix_name (str): The name of the mix to load from database.
                If a mix_name of None is given, it's assumed we initialize
                TableViewTracks and add it to vboxTracks.
                If an existing mix_name is given, it's assumed TableViewTracks
                is existing already and just has to be updated with the fetched
                data.
        Returns:
            None

        The following instance variables are created by this method:
            self.TableViewTracksDataFrame
            self.TableViewTracks
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

        self.TableViewTracksDataFrame = pd.DataFrame(
            mixtracks_list, columns=self.TableViewTracksHeader)

        if mix_name is None:
            self.TableViewTracks = GuiTableView(
                self, self.TableViewTracksDataFrame)
            self.vboxTracks.addWidget(self.TableViewTracks)
        else:
            self.TableViewTracks.model.update(self.TableViewTracksDataFrame)

    def tableviewreleases_load_data(self):
        sql_data = []

        load_mix = Collection(False, self.conf.discobase)
        sql_result = load_mix.get_all_db_releases()

        row = ''
        if sql_result:
            for row in sql_result:
                sql_data.append([ str(row[x]) for x in row.keys()])
            # header = row.keys()

        self.TableViewReleasesDataFrame = pd.DataFrame(sql_data, columns=self.TableViewReleasesHeader)
        self.TableViewReleases.model.update(self.TableViewReleasesDataFrame)

    def treeviewmix_on_clicked(self, index):
        index = index.sibling(index.row(), 0)
        playlist_id = self.treeViewMix.model.data(index, Qt.DisplayRole)
        self.tableviewtracks_load(playlist_id)
        print('playlist_id:', playlist_id)

    def tableviewreleases_on_click(self, index):
        indexes = self.TableViewReleases.selectionModel().selectedRows()
        for index in indexes:
            print(self.TableViewReleases.model.data(self.TableViewReleases.model.index(index.row(), 3)))

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

        # must be a better way to reload data on insert treeview_pushbutton_add_playlist?
        self.treeviewmix_load_data()


def main():
    # Base configuration and setup tasks run on the shell
    conf = Config()
    # Quickfix - Ctrl_common is an abstract class and not ment to be initialized
    # by itself, but rather be inherited by either a GUI controller or a CLI
    # controller class.
    ctrl_common = Ctrl_common()
    ctrl_common.setup_db(conf.discobase)

    # Initialize GUI
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(config_obj=conf)
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
