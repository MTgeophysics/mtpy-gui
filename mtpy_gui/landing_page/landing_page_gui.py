from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from mtpy_gui.__init__ import __version__ as gui_version

import mtpy as mtpy

#import modules. Issues with pyQt or other will be flagged here. 
import mtpy_gui.modeling.convert_model_to_vtk_qt5 as model_to_vtk
import mtpy_gui.modeling.modem_data_file_qt5 as modem_data_file
import mtpy_gui.modeling.modem_model_manipulator_qt5 as modem_model_manipulator
import mtpy_gui.modeling.modem_plot_pt_maps_qt5 as modem_plot_pt_maps
import mtpy_gui.modeling.modem_plot_response_qt5 as modem_plot_response
import mtpy_gui.modeling.view_vtk_qt5 as view_vtk

from matplotlib import pyplot as plt
import qdarkstyle

class MyMenuBar(QMenuBar):
    def __init__(self, parent):#, *args, **kwargs):
        super(MyMenuBar, self).__init__()#*args, **kwargs)
        
        self.app = parent
        
        settings = self.addMenu("&App")
        
        r'''
        save_action = QAction("&Save", parent)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("Save application")
        #save_action.triggered.connect(lambda: self.app.save_app())

        save_as_action = QAction("Save &As", parent)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.setStatusTip("Save application")
        #save_as_action.triggered.connect(lambda: self.app.save_app_as())

        open_action = QAction("&Open", parent)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Load application")
        #open_action.triggered.connect(lambda: self.app.load_app())

        settings_action = QAction("Settings", parent)
        settings_action.setStatusTip("Show application settings")
        #settings_action.triggered.connect(lambda: self.app.win_man.show_app_settings())
        
        settings.addAction(save_action)
        settings.addAction(save_as_action)
        settings.addAction(open_action)
        settings.addAction(settings_action)
        '''
        
        action = settings.addAction('Dark Theme')
        action.setCheckable(True)
        action.setChecked(False)
        action.triggered.connect(self.app.set_app_theme)
        

    
class mainScrollArea(QScrollArea):
    def __init__(self, app):
        super(mainScrollArea, self).__init__()
        widget = QWidget()
        layout = QVBoxLayout()
        ###########START LAYOUT################
        
        #https://stackoverflow.com/questions/51829622/group-buttons-aesthetically-in-pyqt5
        data = [
            {"title": "Data Manipulation",
            "buttons": 
                [{"text": "Modem Data File",
                "path_icon": "SP_DirHomeIcon", 
                'func': lambda: app.sigOpenModule.emit({"type":"modem_data_file"})},
                {"text": "Modem Plot Pt Maps",
                "path_icon": "SP_DirHomeIcon", 
                'func': lambda: app.sigOpenModule.emit({"type":"modem_plot_pt"})},
                {"text": "Modem Plot Response",
                "path_icon": "SP_DirHomeIcon", 
                'func': lambda: app.sigOpenModule.emit({"type":"modem_plot_response"})}]},
            {"title": "Model Manipulation",
            "buttons": 
                [{"text": "Modem Model Manipulator",
                "path_icon": "SP_DirHomeIcon",
                'func': lambda: app.sigOpenModule.emit({"type":"modem_model_manipulator"})}]}, 
            {"title": "3D Tools",
            "buttons": 
                [{"text": "Model to VTK",
                "path_icon": "SP_DirHomeIcon",
                'func': lambda: app.sigOpenModule.emit({"type":"model_to_vtk"})},
                {"text": "VTK Viewer",
                "path_icon": "SP_DirHomeIcon", 
                'func': lambda: app.sigOpenModule.emit({"type":"view_3d"})}]}]
        
        for val in data:
            gb = QGroupBox()
            gb.setTitle(val['title'])
            gb.setStyleSheet("QGroupBox { font-weight: bold; } ");
            hlay = QHBoxLayout(gb)
            for info_button in val['buttons']:
                text = info_button["text"]
                path_icon = info_button["path_icon"]
                function_connect = info_button['func']
                btn = QWidget()
                btn_lay = QVBoxLayout(btn)
                
                toolButton = QToolButton()
                pixmapi = getattr(QStyle, path_icon)
                icon = self.style().standardIcon(pixmapi)
                toolButton.setIcon(icon)
                toolButton.clicked.connect(function_connect)
                toolButton.setIconSize(QSize(35, 35))
                
                label = QLabel(text)
                
                btn_lay.addWidget(toolButton, 0, Qt.AlignCenter)
                btn_lay.addWidget(label, 0, Qt.AlignCenter)
                btn_lay.setContentsMargins(0, 0, 0, 0)
                
                hlay.addWidget(btn)
            hlay.setContentsMargins(5, 5, 5, 5)

            
            layout.addWidget(gb)
        
        ###########END LAYOUT##################
        
        widget.setLayout(layout)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setWidgetResizable(True)
        self.setWidget(widget)  


class landingPage(QMainWindow):
    #make some signals
    sigOpenModule = pyqtSignal(dict)

    def __init__(self, **args):
        super(landingPage, self).__init__(None)
        
        self.setWindowTitle('MtPy GUI (v%s)'%gui_version)
        self.window = mainScrollArea(self)
        self.setCentralWidget(self.window)
        self.setGeometry(50,50,800,600)

        bar = MyMenuBar(self)
        self.setMenuBar(bar)

        #link signals 
        self.sigOpenModule.connect(self.open_module)
        
        self.useDark=False
        self.open_windows = []

        self.setAcceptDrops(True)
        
        self.show()
    
    def open_module(self, d):
        newWin = None
        t = d['type']
        if t=="modem_data_file":
            newWin = modem_data_file.ModEMDataFile()
        elif t=="modem_plot_pt":
            newWin = modem_plot_pt_maps.ModEMPlotPTMap()
        elif t=="modem_plot_response":
            newWin = modem_plot_response.ModEMPlotResponse()
        elif t=="modem_model_manipulator":
            newWin = modem_model_manipulator.ModEM_Model_Manipulator()
        elif t=="model_to_vtk":
            newWin= model_to_vtk.ConvertModel2VTK()
        elif t=="view_3d":
            newWin= view_vtk.MyMainWindow()
        else:
            print('Unexpected window type: %s'%t)

        if newWin:
            newWin.closed.connect(lambda x=newWin: self.close_module(x))
            self.open_windows.append(newWin)
            newWin.show()

    def close_module(self, win):
        win.blockSignals(True)
        self.open_windows.remove(win)
        
    
    def set_app_theme(self, useDark):
        self.useDark=useDark
                
        if useDark: 
            QApplication.instance().setStyleSheet(qdarkstyle.load_stylesheet())
            plt.style.use('dark_background')
        else:
            QApplication.instance().setStyleSheet("")
            plt.style.use('default')
        
        
    def dragEnterEvent(self, event):
        #catch dropped files 
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        #catch dropped files 
        file = [str(u.toLocalFile()) for u in event.mimeData().urls()][0]
        print('The file you just dropped is:\n%s'%file)
        event.ignore()
        return 
    
    def closeEvent(self, event):
        for win in self.open_windows: 
            win.close()
        
        event.accept()
        
