# -*- coding: utf-8 -*-
"""
Created on Tue Jan 19 22:47:32 2021

:copyright: 
    Jared Peacock (jpeacock@usgs.gov)

:license: MIT

"""

# =============================================================================
# Imports
# =============================================================================
import sys

try:
    from PyQt5 import QtCore, QtWidgets
except ImportError:
    raise ImportError("This version needs PyQt5")

try:
    import contextily as cx

    has_cx = True
except ModuleNotFoundError:
    has_cx = False

import numpy as np
from pyproj import CRS
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure

# =============================================================================
# Plot stations
# =============================================================================


class PlotStations(QtWidgets.QWidget):
    """
    plot station locations
    """

    stationChanged = QtCore.pyqtSignal()

    def __init__(self, station_locations):
        self.station_locations = station_locations
        self.plot_crs = None
        self.current_station = None
        self.current_index = 0
        self.previous_index = 0
        self.text_offset = 0.0015
        self.marker_dict = {
            "ls": "None",
            "ms": 3,
            "color": "k",
            "mfc": "k",
            "marker": "o",
        }
        self.current_marker_dict = {
            "ls": "None",
            "ms": 3,
            "color": "r",
            "mfc": "r",
            "marker": "o",
        }
        self.text_dict = {
            "size": 8,
            "weight": None,
            "rotation": 0,
            "color": "k",
            "ha": "center",
            "va": "baseline",
        }
        self.current_text_dict = {
            "size": 8,
            "weight": None,
            "rotation": 0,
            "color": "r",
            "ha": "center",
            "va": "baseline",
        }

        self.cx_source = None
        self.cx_zoom = None
        self.map_crs = CRS.from_epsg(4326)
        if has_cx:
            self.cx_source = cx.providers.USGS.USTopo

        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.figure = Figure(dpi=150)
        self.mpl_widget = FigureCanvas(self.figure)
        self.mpl_widget.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.mpl_widget.setFocus()

        # be able to edit the data
        self.mpl_widget.mpl_connect("pick_event", self.on_pick)
        # self.mpl_widget.mpl_connect("button_press_event", self.on_pick)

        # make sure the figure takes up the entire plottable space
        self.mpl_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.mpl_toolbar = NavigationToolbar(self.mpl_widget, self)

        # set the layout for the plot
        mpl_vbox = QtWidgets.QVBoxLayout()
        mpl_vbox.addWidget(self.mpl_toolbar)
        mpl_vbox.addWidget(self.mpl_widget)

        self.setLayout(mpl_vbox)
        self.mpl_widget.updateGeometry()

    @staticmethod
    def get_text_pad(latitude):
        span = latitude.max() - latitude.min()
        return span * 0.005

    def plot(self):
        """
        Plot stations with names
        """

        plt.rcParams["font.size"] = 10

        label_font_dict = {"size": 12, "weight": "bold"}

        xlabel = "Longitude (deg)"
        ylabel = "Latitude (deg)"

        # add and axes
        self.figure.clf()
        self.ax = self.figure.add_subplot(1, 1, 1, aspect="equal")
        self.ax.plot(
            self.station_locations.longitude,
            self.station_locations.latitude,
            picker=True,
            pickradius=10,
            **self.marker_dict,
        )
        self.text_offset = self.get_text_pad(self.station_locations.latitude)
        for station, x, y in zip(
            self.station_locations.station,
            self.station_locations.longitude,
            self.station_locations.latitude,
        ):
            self.ax.annotate(
                station,
                xy=(x, y),
                ha=self.text_dict["ha"],
                va=self.text_dict["va"],
                xytext=(x, y + self.text_offset),
                color=self.text_dict["color"],
                fontsize=self.text_dict["size"],
                fontweight=self.text_dict["weight"],
                clip_on=True,
            )

        if has_cx:
            try:
                cx_kwargs = {
                    "crs": self.map_crs.to_string(),
                    "source": self.cx_source,
                }
                if self.cx_zoom is not None:
                    cx_kwargs["zoom"] = self.cx_zoom
                cx.add_basemap(
                    self.ax,
                    **cx_kwargs,
                )
            except Exception as error:
               print(f"Could not add base map because {error}")

        # set axis properties
        self.ax.set_xlabel(xlabel, fontdict=label_font_dict)
        self.ax.set_ylabel(ylabel, fontdict=label_font_dict)
        self.ax.grid(alpha=0.35, color=(0.25, 0.25, 0.25), lw=0.25)
        self.ax.set_axisbelow(True)
        self.figure.tight_layout()

        self.mpl_widget.draw()

    def plot_new_station(self):
        self.ax.plot(
            self.station_locations.longitude[self.previous_index],
            self.station_locations.latitude[self.previous_index],
            **self.marker_dict,
        )

        self.ax.text(
            self.station_locations.longitude[self.previous_index],
            self.station_locations.latitude[self.previous_index]
            + self.text_offset
            * np.sign(self.station_locations.latitude[self.previous_index]),
            self.station_locations.station[self.previous_index],
            fontdict=self.text_dict,
        )

        self.ax.plot(
            self.station_locations.longitude[self.current_index],
            self.station_locations.latitude[self.current_index],
            **self.current_marker_dict,
        )

        self.ax.text(
            self.station_locations.longitude[self.current_index],
            self.station_locations.latitude[self.current_index]
            + self.text_offset
            * np.sign(self.station_locations.latitude[self.current_index]),
            self.station_locations.station[self.current_index],
            **self.current_text_dict,
        )
        self.ax.figure.canvas.draw()

    def redraw_plot(self, new_station_locations):
        """

        :param new_station_locations: DESCRIPTION
        :type new_station_locations: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
        self.station_locations = new_station_locations
        self.plot()

    def on_pick(self, event):
        try:
            data_point = event.artist
            data_lon = data_point.get_xdata()[event.ind][0]
            data_lat = data_point.get_ydata()[event.ind][0]
            print(f"picked {data_lat}, {data_lon}")
        except AttributeError:
            print("No item to be picked")
            return

        if event.mouseevent.button == 1:
            self.previous_index = int(self.current_index)

            # get the indicies where the data point has been edited
            self.current_index = np.where(
                (self.station_locations.latitude == data_lat)
                & (self.station_locations.longitude == data_lon)
            )[0][0]
            self.current_station = (
                f"{self.station_locations.survey[self.current_index]}."
                f"{self.station_locations.station[self.current_index]}"
            )

            self.plot_new_station()

            self.stationChanged.emit()
            print(f"station changed to: {self.current_station}")

    def in_axes(self, event):
        pass


# ==============================================================================
# Def Main
# ==============================================================================
def main():
    app = QtWidgets.QApplication(sys.argv)
    ui = PlotStations(None)
    ui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
