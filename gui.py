import sys


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QSettings
from discodos.qt.MainWindow import Ui_MainWindow
from discodos.models import Mix, log, Collection
from discodos.config import Config
from discodos.utils import is_number

class GuiTableViewModel(QtGui.QStandardItemModel):
#class MyModel(QtCore.QAbstractTableModel):

    def __init__(self, header=None):
        super(GuiTableViewModel, self).__init__()

    def dropMimeData(self, data, action, row, col, parent):
        """
        Always move the entire row, and don't allow column "shifting"
        """
        return super().dropMimeData(data, action, row, 0, parent)


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

    def __init__(self, parent):
        super().__init__(parent)
        #self.verticalHeader().hide()
        #self.horizontalHeader().hide()
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.SingleSelection)
        self.setShowGrid(False)
        self.setDragDropMode(self.InternalMove)
        self.setDragDropOverwriteMode(False)

        self.setStyle(GuiTableViewProxyStyle())
        self.model = GuiTableViewModel()
        self.setModel(self.model)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self.settings = QSettings('discodos/qt/settings.ini', QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False)

        # Load settings from settings.ini or default if no .ini found
        self.resize(self.settings.value('size', QtCore.QSize(1280, 768)))
        self.move(self.settings.value('pos', QtCore.QPoint(50, 50)))

        # create vbox layouts and add to setlayout groupbox
        self.vboxPlaylist = QtWidgets.QVBoxLayout()
        self.vboxPlaylist.setContentsMargins(0, 0, 0, 0)
        self.vboxPlaylist.setSpacing(2)
        self.groupBoxPlaylist.setLayout(self.vboxPlaylist)

        self.vboxSongs = QtWidgets.QVBoxLayout()
        self.vboxSongs.setContentsMargins(0, 0, 0, 0)
        self.groupBoxSongs.setLayout(self.vboxSongs)

        self.vboxReleases = QtWidgets.QVBoxLayout()
        self.vboxReleases.setContentsMargins(0, 0, 0, 0)
        self.groupBoxReleases.setLayout(self.vboxReleases)

        # create treeview
        self.treeViewPlaylist = QtWidgets.QTreeView()
        self.treeViewPlaylistModel = QtGui.QStandardItemModel()
        self.treeViewPlaylist.setModel(self.treeViewPlaylistModel)
        self.treeViewPlaylist.clicked.connect(self.treeview_on_clicked)
        self.vboxPlaylist.addWidget(self.treeViewPlaylist)
        self.rootNode = self.treeViewPlaylistModel.invisibleRootItem()

        # create tableviewplaylistsongs
        self.TableViewPlaylistSongs = GuiTableView(self)
        self.vboxSongs.addWidget(self.TableViewPlaylistSongs)

        # create tableviewreleases
        self.TableViewReleases = GuiTableView(self)
        self.TableViewReleases.clicked.connect(self.tableviewreleases_on_click)
        self.vboxReleases.addWidget(self.TableViewReleases)

        # create vbox formlayout for buttons and edit box
        self.vboxFormLayout = QtWidgets.QFormLayout()

        # lineedit playlistname
        self.lineEditAddPlaylistName = QtWidgets.QLineEdit()
        self.lineEditAddPlaylistName.setPlaceholderText('Playlist name')
        self.vboxFormLayout.addRow(self.lineEditAddPlaylistName)

        # lineedit playlistvenue
        self.lineEditAddPlaylistVenue = QtWidgets.QLineEdit()
        self.lineEditAddPlaylistVenue.setPlaceholderText('Venue')
        self.vboxFormLayout.addRow(self.lineEditAddPlaylistVenue)

        # lineedit playlistdate
        self.lineEditAddPlaylistDate = QtWidgets.QLineEdit()
        self.lineEditAddPlaylistDate.setPlaceholderText('2021-01-01')
        self.vboxFormLayout.addRow(self.lineEditAddPlaylistDate)

        # pushbuttonadd
        self.pushButtonAddPlaylist = QtWidgets.QPushButton()
        self.pushButtonAddPlaylist.setText('Add')
        self.pushButtonAddPlaylist.clicked.connect(self.treeview_pushbutton_add_playlist)

        #pushbuttondel
        self.pushButtonDelPlaylist = QtWidgets.QPushButton()
        self.pushButtonDelPlaylist.setText('Delete')
        self.pushButtonDelPlaylist.clicked.connect(self.treeview_pushbutton_del_playlist)
        self.vboxFormLayout.addRow(self.pushButtonAddPlaylist, self.pushButtonDelPlaylist)

        # add formlayout to playlist boxlayout
        self.vboxPlaylist.addLayout(self.vboxFormLayout)

        self.initUI()

    # on close save window positions
    def closeEvent(self, e):
        self.settings.setValue('size', self.size())
        self.settings.setValue('pos', self.pos())
        e.accept()

    def initUI(self):
        self.treeview_load_data()
        self.tableviewreleases_load_data()

    def treeview_load_data(self):
        sql_data = []

        load_mix = Mix(False, 'all')
        sql_result = load_mix.get_all_mixes()

        # must be a better way to reload data on insert treeview_pushbutton_add_playlist?
        self.rootNode.model().clear()
        self.rootNode = self.treeViewPlaylistModel.invisibleRootItem()

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
                    self.treeViewPlaylistModel.setHeaderData(idx, Qt.Horizontal, header[idx])

                self.rootNode.appendRow(list_qstandard_item)

        self.treeViewPlaylist.header().resizeSections(QtWidgets.QHeaderView.ResizeToContents)


    def tableviewplaylistsongs_load_data(self, mix_name):
        sql_data = []
        self.TableViewPlaylistSongs.model.clear()

        load_mix = Mix(False, mix_name)
        sql_result = load_mix.get_full_mix(True)

        row = ''
        if sql_result:
            for row in sql_result:
                sql_data.append([ str(row[x]) for x in row.keys()])
            header = row.keys()

            for list_item in sql_data:
                list_qstandard_item = []
                for idx, result in enumerate(list_item):
                    item = QtGui.QStandardItem(result)
                    item.setEditable(False)
                    item.setDropEnabled(False)
                    list_qstandard_item.append(item)
                    self.TableViewPlaylistSongs.model.setHeaderData(idx, Qt.Horizontal, header[idx])
                self.TableViewPlaylistSongs.model.appendRow(list_qstandard_item)

    def tableviewreleases_load_data(self):
        sql_data = []

        load_mix = Collection(False)
        sql_result = load_mix.get_all_db_releases()

        row = ''
        if sql_result:
            for row in sql_result:
                sql_data.append([ str(row[x]) for x in row.keys()])
            header = row.keys()

            for list_item in sql_data:
                list_qstandard_item = []
                for idx, result in enumerate(list_item):
                    item = QtGui.QStandardItem(result)
                    item.setEditable(False)
                    item.setDropEnabled(False)
                    list_qstandard_item.append(item)
                    self.TableViewReleases.model.setHeaderData(idx, Qt.Horizontal, header[idx])
                self.TableViewReleases.model.appendRow(list_qstandard_item)

    def treeview_on_clicked(self, index):
        index = index.sibling(index.row(), 0)
        playlist_id = self.treeViewPlaylist.model().data(index, Qt.DisplayRole)
        self.tableviewplaylistsongs_load_data(playlist_id)
        print('playlist_id:', playlist_id)

    def tableviewreleases_on_click(self, index):
        indexes = self.TableViewReleases.selectionModel().selectedRows()
        for index in indexes:
            print(self.TableViewReleases.model.data(self.TableViewReleases.model.index(index.row(), 3)))

    def treeview_pushbutton_del_playlist(self, index):
        playlist_id = self.treeViewPlaylist.model().data(self.treeViewPlaylist.selectedIndexes()[0])
        row_id = self.treeViewPlaylist.selectionModel().currentIndex().row()

        try:
            self.treeViewPlaylist.model().removeRow(row_id)
            playlist = Mix(False, playlist_id)
            playlist.delete()
            log.info("GUI: Deleted Mix %s, from list and removed rowid %d from treeview", playlist_id, row_id)
        except:
            log.error("GUI; Failed to delete Mix! %s", playlist_id)

    def treeview_pushbutton_add_playlist(self):
        playlist_name = self.lineEditAddPlaylistName.text()
        playlist_venue = self.lineEditAddPlaylistVenue.text()
        playlist_date = self.lineEditAddPlaylistDate.text()
        if playlist_name != '':
            print(playlist_name)
            playlist = Mix(False, 'all')
            playlist.create(playlist_date, playlist_venue, playlist_name)
            # self.lineEditAddPlaylistName.setText('')
            # self.lineEditAddPlaylistVenue.setText('')
            # self.lineEditAddPlaylistDate.setText('')
        else:
            print('no playlist name')

        # must be a better way to reload data on insert treeview_pushbutton_add_playlist?
        self.treeview_load_data()


def main():
    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()


if __name__ == '__main__':
    main()