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
        MainWindow.resize(889, 550)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setHorizontalSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.groupBoxReleases = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBoxReleases.setObjectName("groupBoxReleases")
        self.gridLayout.addWidget(self.groupBoxReleases, 2, 1, 1, 1)
        self.groupBoxPlaylist = QtWidgets.QGroupBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBoxPlaylist.sizePolicy().hasHeightForWidth())
        self.groupBoxPlaylist.setSizePolicy(sizePolicy)
        self.groupBoxPlaylist.setMaximumSize(QtCore.QSize(250, 16777215))
        self.groupBoxPlaylist.setObjectName("groupBoxPlaylist")
        self.gridLayout.addWidget(self.groupBoxPlaylist, 0, 0, 3, 1)
        self.groupBoxSongs = QtWidgets.QGroupBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBoxSongs.sizePolicy().hasHeightForWidth())
        self.groupBoxSongs.setSizePolicy(sizePolicy)
        self.groupBoxSongs.setObjectName("groupBoxSongs")
        self.gridLayout.addWidget(self.groupBoxSongs, 0, 1, 1, 1)
        self.groupBoxTest = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBoxTest.setMaximumSize(QtCore.QSize(100, 16777215))
        self.groupBoxTest.setObjectName("groupBoxTest")
        self.gridLayout.addWidget(self.groupBoxTest, 0, 3, 3, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 889, 24))
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
        self.groupBoxReleases.setTitle(_translate("MainWindow", "Releases"))
        self.groupBoxPlaylist.setTitle(_translate("MainWindow", "Playlist"))
        self.groupBoxSongs.setTitle(_translate("MainWindow", "Songs"))
        self.groupBoxTest.setTitle(_translate("MainWindow", "Test"))

