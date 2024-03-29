# -*- coding: utf-8 -*-
"""
Created on Mon Nov 29 09:27:13 2022

:copyright: 
    Bennett Hoogenboom(bhoogenboom@usgs.gov)

:license: MIT

"""
# ==============================================================================
# Imports
# ==============================================================================

# This file will be the main dashboard for the GUI tools, such that
# all you need to do is run this one file and all the other GUIs
# are available. Set up signals to recieve data from one window and pass it to another.

#TODO mtpy setup: matplotlib 3.5 required 
#TODO mtpy setup: gdal is required 

__version__ = '0.0.2'


def checkCommandArguments():
    import argparse
    
    """Check the users command line arguments. """


    Parser = argparse.ArgumentParser(description="MtPy-gui",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    Parser.add_argument('-f', dest='inputFile', default=None, help='File to load.')
    
    args = Parser.parse_args()

    return args.inputFile

def make_dpi_aware(): 
    import ctypes
    import platform
    
    if int(platform.release()) >= 8:
        ctypes.windll.shcore.SetProcessDpiAwareness(True)

def main():
    """ Run the app."""
    
    inputFile = checkCommandArguments()
    
    print('starting application...')
    
    
    import sys
    import os
    from PyQt5.QtWidgets import QApplication, QStyleFactory
    from PyQt5.QtGui import QIcon

    from mtpy_gui.landing_page.landing_page_gui import landingPage

    sys.path.append(os.getcwd())
    
    make_dpi_aware()
    gui_app=QApplication(sys.argv)

    scriptDir = os.path.dirname(os.path.realpath(__file__))
    gui_app.setWindowIcon(QIcon(scriptDir + os.path.sep + 'window_icon.png'))
    
    GUI = landingPage()

    n = gui_app.exec_()
    sys.exit(n)

