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
        #self.verticalHeader().hide()
        #self.horizontalHeader().hide()
        #self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.SingleSelection)
        self.setShowGrid(False)
        self.setDragDropMode(self.InternalMove)
        self.setDragDropOverwriteMode(False)

        self.setStyle(GuiTableViewProxyStyle())
        self.model = GuiTableViewModel(self._data)
        self.setModel(self.model)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self.conf = Config()

        self.settings = QSettings('discodos/qt/settings.ini', QSettings.IniFormat)
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

        # create treeview
        self.treeViewMix = QtWidgets.QTreeView()
        self.treeViewMixModel = QtGui.QStandardItemModel()
        self.treeViewMix.setModel(self.treeViewMixModel)
        self.treeViewMix.clicked.connect(self.treeviewmix_on_clicked)
        self.vboxMix.addWidget(self.treeViewMix)
        self.rootNode = self.treeViewMixModel.invisibleRootItem()

        # create tableviewplaylistsongs
        self.data_list = []
        self.TableViewTracksHeader = ['track_pos', 'discogs_title', 'd_artist', 'd_track_name', 'd_track_no', 'key',
                                      'bpm', 'key_notes', 'trans_rating', 'trans_notes', 'notes', 'a_key',
                                      'a_chords_key', 'a_bpm']
        self.TableViewTracksDataFrame = pd.DataFrame(self.data_list, columns=self.TableViewTracksHeader)
        self.TableViewTracks = GuiTableView(self, self.TableViewTracksDataFrame)
        self.vboxTracks.addWidget(self.TableViewTracks)

        # create tableviewreleases
        self.TableViewReleasesHeader = ['d_catno', 'd_artist', 'discogs_title', 'discogs_id', 'm_rel_id', 'm_rel_id_override']
        self.TableViewReleasesDataFrame = pd.DataFrame(self.data_list, columns=self.TableViewReleasesHeader)
        self.TableViewReleases = GuiTableView(self, self.TableViewReleasesDataFrame)
        self.TableViewReleases.clicked.connect(self.tableviewreleases_on_click)
        self.vboxReleases.addWidget(self.TableViewReleases)

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
        if self.settings.value('ColumnWidth'):
            self.TableViewTracks.horizontalHeader().restoreState(self.settings.value('ColumnWidth'))
        self.settings.endGroup()
        self.settings.beginGroup('TableViewReleases')
        if self.settings.value('ColumnWidth'):
            self.TableViewReleases.horizontalHeader().restoreState(self.settings.value('ColumnWidth'))
        self.settings.endGroup()

        self.settings.beginGroup('TreeViewMix')
        if self.settings.value('ColumnWidth'):
            self.treeViewMix.header().restoreState(self.settings.value('ColumnWidth'))
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

        # must be a better way to reload data on insert treeview_pushbutton_add_playlist?
        self.rootNode.model().clear()
        self.rootNode = self.treeViewMixModel.invisibleRootItem()

        row = ''
        if sql_result:
            for row in sql_result:
                sql_data.append([str(row[x]) for x in row.keys()])
            header = row.keys()

            for list_item in sql_data:
                list_qstandard_item = []
                for idx, result in enumerate(list_item):
                    item = QtGui.QStandardItem(result)
                    item.setEditable(False)
                    list_qstandard_item.append(item)
                    self.treeViewMixModel.setHeaderData(idx, Qt.Horizontal, header[idx])

                self.rootNode.appendRow(list_qstandard_item)

        self.treeViewMix.header().resizeSections(QtWidgets.QHeaderView.ResizeToContents)

    def tableviewtracks_load_data(self, mix_name):
        sql_data = []

        load_mix = Mix(False, mix_name, self.conf.discobase)
        sql_result = load_mix.get_full_mix(True)

        row = ''
        if sql_result:
            for row in sql_result:
                sql_data.append([ str(row[x]) for x in row.keys()])
            # header = row.keys()

        self.TableViewTracksDataFrame = pd.DataFrame(sql_data, columns=self.TableViewTracksHeader)
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
        playlist_id = self.treeViewMix.model().data(index, Qt.DisplayRole)
        self.tableviewtracks_load_data(playlist_id)
        print('playlist_id:', playlist_id)

    def tableviewreleases_on_click(self, index):
        indexes = self.TableViewReleases.selectionModel().selectedRows()
        for index in indexes:
            print(self.TableViewReleases.model.data(self.TableViewReleases.model.index(index.row(), 3)))

    def treeviewmix_pushbutton_del_mix(self, index):
        playlist_id = self.treeViewMix.model().data(self.treeViewMix.selectedIndexes()[0])
        row_id = self.treeViewMix.selectionModel().currentIndex().row()

        try:
            self.treeViewMix.model().removeRow(row_id)
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
            print(playlist_name)
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
    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()


if __name__ == '__main__':
    main()