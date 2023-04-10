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
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import sys

# Setting the Qt bindings for QtPy
import os
os.environ["QT_API"] = "pyqt5"

from qtpy import QtWidgets

import numpy as np

import pyvista as pv
from pyvistaqt import QtInteractor, MainWindow



from matplotlib import pyplot as plt 
import matplotlib as mpl










class slicing_window(QDialog):
    def __init__(self, config={}):
        super(slicing_window, self).__init__()
        self.setWindowTitle('Slice 3D Object Tool')
        #self.setMinimumSize(QSize(800, 800))
        
        self.config=config
        
        self.create_ui()

    def create_ui(self):
        layout = QGridLayout()
        
        r=0
        
        
        var_name_cb = QComboBox()
        var_name_cb.addItems(self.config['vars'])
        var_name_cb.setCurrentText(self.config['var'])
        var_name_cb.currentTextChanged.connect(lambda x: self.update_config('var', x))
        
        layout.addWidget(QLabel('Variable to plot:'), r, 0, 1, 1)
        layout.addWidget(var_name_cb, r, 1, 1, 1)

        
        r+=1
        p1x = QLineEdit()
        p1x.setValidator(QDoubleValidator())
        p1x.setText(str(self.config['p1x']))
        p1x.textChanged.connect(lambda x: self.update_config('p1x', x))
        p1y = QLineEdit()
        p1y.setValidator(QDoubleValidator())
        p1y.setText(str(self.config['p1y']))
        p1y.textChanged.connect(lambda x: self.update_config('p1y', x))
        layout.addWidget(QLabel('Point A (x,y)'), r, 0, 1, 1)
        layout.addWidget(p1x, r, 1, 1, 1)
        layout.addWidget(p1y, r, 2, 1, 1)
        
        r+=1
        p2x = QLineEdit()
        p2x.setValidator(QDoubleValidator())
        p2x.setText(str(self.config['p2x']))
        p2x.textChanged.connect(lambda x: self.update_config('p2x', x))
        p2y = QLineEdit()
        p2y.setValidator(QDoubleValidator())
        p2y.setText(str(self.config['p2y']))
        p2y.textChanged.connect(lambda x: self.update_config('p2y', x))
        layout.addWidget(QLabel('Point B (x,y)'), r, 0, 1, 1)
        layout.addWidget(p2x, r, 1, 1, 1)
        layout.addWidget(p2y, r, 2, 1, 1)
        
        r+=1
        z_top = QLineEdit()
        z_top.setValidator(QDoubleValidator())
        z_top.setText(str(self.config['z_top']))
        z_top.textChanged.connect(lambda x: self.update_config('z_top', x))
        z_bot = QLineEdit()
        z_bot.setValidator(QDoubleValidator())
        z_bot.setText(str(self.config['z_bot']))
        z_bot.textChanged.connect(lambda x: self.update_config('z_bot', x))
        layout.addWidget(QLabel('Z_min, Z_max'), r, 0, 1, 1)
        layout.addWidget(z_top, r, 1, 1, 1)
        layout.addWidget(z_bot, r, 2, 1, 1)



        r+=1
        nx = QLineEdit()
        nx.setValidator(QIntValidator())
        nx.setText(str(self.config['nx']))
        nx.textChanged.connect(lambda x: self.update_config('nx', x))
        ny = QLineEdit()
        ny.setValidator(QIntValidator())
        ny.setText(str(self.config['ny']))
        ny.textChanged.connect(lambda x: self.update_config('ny', x))
        layout.addWidget(QLabel('Nx, Ny'), r, 0, 1, 1)
        layout.addWidget(nx, r, 1, 1, 1)
        layout.addWidget(ny, r, 2, 1, 1)


        
        r+=1
        cmap_cb = QComboBox()
        cmap_cb.addItems(plt.colormaps())
        cmap_cb.currentTextChanged.connect(lambda x: self.update_config('cmap', x))
        cmap_cb.setCurrentText(self.config['cmap'])
        layout.addWidget(QLabel('Colormap:'), r, 0, 1, 1)
        layout.addWidget(cmap_cb, r, 1, 1, 1)        

        r+=1
        clim_low = QLineEdit()
        clim_low.setValidator(QDoubleValidator())
        clim_low.textChanged.connect(lambda x: self.update_config('clim_low', x))
        clim_high = QLineEdit()
        clim_high.setValidator(QDoubleValidator())
        clim_high.textChanged.connect(lambda x: self.update_config('clim_high', x))
        layout.addWidget(QLabel('Colorbar limits:\n(Leave blank for no limit)'), r, 0, 1, 1)
        layout.addWidget(clim_low, r, 1, 1, 1)
        layout.addWidget(clim_high, r, 2, 1, 1)
        
        
        
        
        
        
        
        
        

        r+=1
        log_cb = QCheckBox()
        log_cb.setChecked(self.config['log'])
        log_cb.stateChanged.connect(lambda x: self.update_config('log', log_cb.isChecked()))
        layout.addWidget(QLabel('Log scale:'), r, 0, 1, 1)
        layout.addWidget(log_cb, r, 1, 1, 1)
        
        r+=1
        dep_cb = QCheckBox()
        dep_cb.setChecked(self.config['to_depth'])
        dep_cb.stateChanged.connect(lambda x: self.update_config('to_depth', dep_cb.isChecked()))
        layout.addWidget(QLabel('Transform to depth:'), r, 0, 1, 1)
        layout.addWidget(dep_cb, r, 1, 1, 1)
        
        r+=1
        rot_cb = QSpinBox()
        rot_cb.setValue(self.config['rot90'])
        rot_cb.valueChanged.connect(lambda x: self.update_config('rot90', rot_cb.value()))
        layout.addWidget(QLabel('Data rotation:'), r, 0, 1, 1)
        layout.addWidget(rot_cb, r, 1, 1, 1)
        
        r+=1
        kind_cb = QComboBox()
        kind_cb.addItems(['pcolormesh', 'contourf'])
        kind_cb.setCurrentText(self.config['kind'])
        kind_cb.currentTextChanged.connect(lambda x: self.update_config('kind', x))
        kind_cb.setCurrentText(self.config['kind'])
        layout.addWidget(QLabel('Type of plot:'), r, 0, 1, 1)
        layout.addWidget(kind_cb, r, 1, 1, 1)   
        
        r+=1
        plot_cb = QCheckBox()
        plot_cb.setChecked(self.config['show_plot'])
        plot_cb.stateChanged.connect(lambda x: self.update_config('show_plot', plot_cb.isChecked()))
        layout.addWidget(QLabel('Show plot:'), r, 0, 1, 1)
        layout.addWidget(plot_cb, r, 1, 1, 1)
        
        r+=1
        save_cb = QCheckBox()
        save_cb.setChecked(self.config['save_plot'])
        save_cb.stateChanged.connect(lambda x: self.update_config('save_plot', save_cb.isChecked()))
        layout.addWidget(QLabel('Save plot:\n(Prompt will follow)'), r, 0, 1, 1)
        layout.addWidget(save_cb, r, 1, 1, 1)
        
        
        ok_cb = QPushButton('Accept')
        ok_cb.clicked.connect(self.accept)
        layout.addWidget(ok_cb, r+1, 0, 2, 1)
        
        self.setLayout(layout)


    def update_config(self, key, value):
        self.config[key]=value

    def closeEvent(self, event):
        QDialog.closeEvent(self, event)
        return


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

        self.load_action_slice = QtWidgets.QAction('3D Slice', self)
        self.load_action_slice.triggered.connect(self.get_data_3D_slice)
        meshMenu.addAction(self.load_action_slice)
        
        self.load_action_cross_section = QtWidgets.QAction('3D Cross-section', self)
        self.load_action_cross_section.triggered.connect(self.get_data_3D_cross_section)
        meshMenu.addAction(self.load_action_cross_section)

        self.show()

    def choose_3D_file(self):
        """
        get the filename from a file dialogue

        """

        files_types = "VTK (*.vtk);;VTR (*.vtr);;VTU (*.vtu)"                    
        fn = QFileDialog().getOpenFileName(self, 'Open 3D file', None, files_types)[0]

        return fn 
    
    def get_data_3D(self, *args, fn=''):
        """
        get the filename from a file dialogue

        """

        if fn=='':
            fn = self.choose_3D_file()
        
        if fn!='':
            """ add a 3d file to the pyqt frame """
            try: 
                mesh = pv.read(fn)
            except:
                print('unable to load mesh %s'%fn)
                return 
            self.plotter.add_mesh(mesh)#, show_edges=True)
            self.plotter.reset_camera()

    def get_data_3D_slice(self, *args, fn=''):
        """
        get the filename from a file dialogue

        """

        if fn=='':
            fn = self.choose_3D_file()
        
        if fn!='':
            """ add a 3d file to the pyqt frame with slicing"""
            try: 
                mesh = pv.read(fn)
            except:
                print('unable to load mesh %s'%fn)
                return 
            self.plotter.add_mesh_clip_plane(mesh)#, show_edges=True)
            self.plotter.show_grid()
            self.plotter.reset_camera()  
    
    def get_data_3D_cross_section(self, *args, fn=''):
        """
        get the filename from a file dialogue

        """

        if fn=='':
            fn = self.choose_3D_file()
        
        if fn!='':
            """ add a 3d file to the pyqt frame with slicing"""
            try: 
                mesh = pv.read(fn)
            except:
                print('unable to load mesh %s'%fn)
                return 
            

        
            config={}
            config['xmin'], config['xmax'], config['ymin'], config['ymax'], config['zmin'], config['zmax'] = mesh.bounds
            
            config['vars'] = mesh.cell_data.keys()
            
            config['var'] = config['vars'][0]
            
            config['p1x'] = config['xmin']
            config['p1y'] = config['ymin']
            config['p2x'] = config['xmax']
            config['p2y'] = config['ymax']
            config['z_top'] = config['zmax']
            config['z_bot'] = config['zmin']
            
            config['cmap'] = 'viridis'
            config['clim_low']=''
            config['clim_high']=''
            config['log']=False
            config['to_depth']=False
            
            config['kind']='pcolormesh'
            
            config['nx'] = config['ny'] = 50
            
            config['rot90'] = 0
            
            config['show_plot'] = True
            config['save_plot'] = False
            
            newWin = slicing_window(config)
            ret = newWin.exec_()
            
            if ret==0:
                return 
            
            config = newWin.config
            
                        
            to_depth = config['to_depth'] 
            cmap = config['cmap']
            log = config['log'] 
            var_name = config['var']
            clim_low = config['clim_low']
            clim_high = config['clim_high']
            
            nx = config['nx']
            ny = config['ny']
            
            p1x = config['p1x']
            p1y = config['p1y']
            p2x = config['p2x']
            p2y = config['p2y']
            z_top = config['z_top']
            z_bot = config['z_bot']
            
            ll = np.array([p1x, p1y, z_bot])
            lr = np.array([p2x, p2y, z_bot])
            ur = np.array([p2x, p2y, z_top])
            ul = np.array([p1x, p1y, z_top])
            
            p1 = ll
            p2 = lr
            p3 = ur
            
            #ul.............ur
            # .             .
            # .             .
            # .             .
            # .             .
            #ll.............lr
            
            
            # These two vectors are in the plane
            v1 = p3 - p1
            v2 = p2 - p1

            # the cross product is a vector normal to the plane
            cp = np.cross(v1, v2)
            a, b, c = cp

            #get origin of object 
            origin = mesh.center
            
            single_slice = mesh.slice(normal=[a, b, c])
            
            normal = [a,b,c]
            origin = single_slice.center
            
            values = self.slice_to_array(single_slice, normal, origin, name=var_name, )

            self.plotter.add_mesh(single_slice)
            
            points = np.array([[p1x, p1y, z_top],[p2x, p2y, z_top]])
            labels = ['A', 'B']
            
            self.plotter.add_point_labels(points, labels)
            
            self.plotter.reset_camera()  

            #####################
            #ALL PLOTTING STUFF HERE 
            ##################### 
            if config['show_plot'] or config['save_plot']:
                xs, zs, array = self.slice_to_array(single_slice, cp, origin, var_name, nx, ny)
                
                for i in range(config['rot90']):
                    array=np.rot90(array)
                
                if clim_low=='': clim_low=None
                if clim_high=='': clim_high=None

                if to_depth:
                    zs = np.subtract(zs[0][0], zs)
                    
                if log:
                    vmin=clim_low
                    vmax=clim_high
                    norm = mpl.colors.LogNorm(vmin=vmin, vmax=vmax)
                else:
                    vmin=clim_low
                    vmax=clim_high
                    norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

                fig, ax = plt.subplots()
                if config['kind']=='pcolormesh':
                    pc = ax.pcolormesh(xs, zs, array, norm=norm, cmap=cmap)
                elif config['kind']=='contourf':
                    pc = ax.contourf(xs, zs, array, vmin=vmin, vmax=vmax, norm=norm, cmap=cmap)
                
                fig.colorbar(pc, ax=ax)
                
                ax.set_title(var_name)
                ax.set_xlabel('Distance along line')
                
                if to_depth:
                    ax.invert_yaxis=True 
                    ax.set_ylabel('Depth')
                else:
                    ax.set_ylabel('Elevation')

                ax.text(0.0, 1.0, 'A',
                    horizontalalignment='left',
                    verticalalignment='bottom',
                    transform=ax.transAxes)
                
                ax.text(1.0, 1.0, 'B',
                    horizontalalignment='right',
                    verticalalignment='bottom',
                    transform=ax.transAxes)
                
                if config['show_plot']:
                    plt.show()
                if config['save_plot']:
                    files_types = "PNG (*.png);;PDF (*.pdf);;SVG (*.svg);;EPS (*.eps)"                    
                    fn = QFileDialog().getSaveFileName(self, 'Save as...', os.path.dirname(fn), files_types)[0]
                    if fn!='':
                        fmt = fn[-3:]
                        print(fmt)
                        #get resolution of save 
                        dpi, ok = QInputDialog.getInt(self, 'Image resolution', 'Figure resolution:', 500)
                        if ok:
                            plt.savefig(fn, dpi=dpi, format=fmt)
                        
                        
                    


            #self.get_data_3D_slice(fn=fn)

    def slice_to_array(self, slc, normal, origin, name, ni=50, nj=50):
        """Converts a PolyData slice to a 2D NumPy array.
        
        It is crucial to have the true normal and origin of
        the slicing plane
        
        Parameters
        ----------
        slc : PolyData
            The slice to convert.
        normal : tuple(float)
            the normal of the original slice
        origin : tuple(float)
            the origin of the original slice
        name : str
            The scalar array to fetch from the slice
        ni : int
            The resolution of the array in the i-direction
        nj : int
            The resolution of the array in the j-direction
        
        
        Modified from https://github.com/pyvista/pyvista-support/issues/89
        
        """
        # Make structured grid
        x = np.linspace(slc.bounds[0], slc.bounds[1], ni)
        y = np.linspace(slc.bounds[2], slc.bounds[3], nj)
        z = np.array([0])
        
        plane = pv.StructuredGrid(*np.meshgrid(x,y,z))

        # rotate and translate grid to be ontop of the slice
        vx = np.array([0., 0., 1.])
        direction = normal / np.linalg.norm(normal)
        vx -= vx.dot(direction) * direction
        vx /= np.linalg.norm(vx)
        vy = np.cross(direction, vx)
        rmtx = np.array([vx, vy, direction])
        plane.points = plane.points.dot(rmtx)
        plane.points -= plane.center
        plane.points += origin

        # resample the data
        sampled = plane.sample(slc, tolerance=slc.length*0.5)
        # Fill bad data
        sampled[name][~sampled["vtkValidPointMask"].view(bool)] = np.nan

        # plot the 2D array
        array = sampled[name].reshape(sampled.dimensions[0:2])
        xs = sampled.x.reshape(sampled.dimensions[0:2])
        ys = sampled.y.reshape(sampled.dimensions[0:2])
        zs = sampled.z.reshape(sampled.dimensions[0:2])

        dx = np.sqrt((xs-x[0])**2+(ys-y[0])**2)

        return dx, zs, array