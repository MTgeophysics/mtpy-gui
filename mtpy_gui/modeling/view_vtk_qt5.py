# -*- coding: utf-8 -*-
"""
Created on Mon Nov 29 18:25:22 2022

@author: bhoogenboom

Gui to view 3D files.
"""

# ==============================================================================
# Imports
# ==============================================================================
# standard packages
import os
import sys

# 3rd party packages
from PyQt5 import QtCore, QtGui, QtWidgets


import sys

# Setting the Qt bindings for QtPy
import os
os.environ["QT_API"] = "pyqt5"

from qtpy import QtWidgets

import numpy as np

import pyvista as pv
from pyvistaqt import QtInteractor, MainWindow

from PyQt5.QtCore import pyqtSignal

class MyMainWindow(MainWindow):
    closed = pyqtSignal()
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        
        self.setWindowTitle("3D Object Viewer")
        #self.setWindowState(QtCore.Qt.WindowMaximized)
        
        
        #create the frame
        self.frame = QtWidgets.QFrame()
        vlayout = QtWidgets.QVBoxLayout()

        # add the pyvista interactor object
        self.plotter = QtInteractor(self.frame)
        vlayout.addWidget(self.plotter.interactor)
        self.signal_close.connect(self.plotter.close)
        self.signal_close.connect(lambda: self.closed.emit())
        
        self.frame.setLayout(vlayout)
        self.setCentralWidget(self.frame)

        # simple menu
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('File')
        exitButton = QtWidgets.QAction('Exit', self)
        exitButton.setShortcut('Ctrl+Q')
        exitButton.triggered.connect(self.close)
        fileMenu.addAction(exitButton)

        # add load options
        meshMenu = mainMenu.addMenu('Load')
        self.load_action = QtWidgets.QAction('3D File', self)
        self.load_action.triggered.connect(self.get_data_3D)
        meshMenu.addAction(self.load_action)


        self.show()

    def get_data_3D(self):
        """
        get the filename from a file dialogue

        """

        fn_dialog = QtWidgets.QFileDialog()
        #fn = str(
        #    fn_dialog.getOpenFileName(
        #        caption="Choose 3D file", filter="(*.vtk);; (*.vtk)"
        #    )[0]
        #)
        
        #no filter
        fn = str(fn_dialog.getOpenFileName(caption="Choose 3D file")[0])
        
        if fn!='':
            self.load_3D(fn)

    
    def load_3D(self, filename):
        """ add a 3d file to the pyqt frame """
        try: 
            mesh = pv.read(filename)
        except:
            print('unable to load mesh %s'%filename)
            return 
        self.plotter.add_mesh(mesh)#, show_edges=True)
        self.plotter.reset_camera()


