# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'MainWindow.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1432, 906)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.splitter_vertical = QtWidgets.QSplitter(self.centralwidget)
        self.splitter_vertical.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_vertical.setObjectName("splitter_vertical")
        self.groupBoxPlaylist = QtWidgets.QGroupBox(self.splitter_vertical)
        self.groupBoxPlaylist.setObjectName("groupBoxPlaylist")
        self.splitter_horizontal = QtWidgets.QSplitter(self.splitter_vertical)
        self.splitter_horizontal.setOrientation(QtCore.Qt.Vertical)
        self.splitter_horizontal.setObjectName("splitter_horizontal")
        self.groupBoxSongs = QtWidgets.QGroupBox(self.splitter_horizontal)
        self.groupBoxSongs.setObjectName("groupBoxSongs")
        self.groupBoxReleases = QtWidgets.QGroupBox(self.splitter_horizontal)
        self.groupBoxReleases.setObjectName("groupBoxReleases")
        self.groupBoxTest = QtWidgets.QGroupBox(self.splitter_vertical)
        self.groupBoxTest.setObjectName("groupBoxTest")
        self.gridLayout.addWidget(self.splitter_vertical, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1432, 24))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.groupBoxPlaylist.setTitle(_translate("MainWindow", "Playlist"))
        self.groupBoxSongs.setTitle(_translate("MainWindow", "Songs"))
        self.groupBoxReleases.setTitle(_translate("MainWindow", "Releases"))
        self.groupBoxTest.setTitle(_translate("MainWindow", "Test"))

