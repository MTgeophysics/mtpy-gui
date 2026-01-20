### class for plotting transfer functions
import numpy as np
from bokeh.plotting import figure
from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource


class PlotView:
    def __init__(self):
        self.fig_rho_xy = self._make_fig("Apparent Resistivity (XY)", "log")
        self.fig_ph_xy = self._make_fig("Phase (XY)", "linear")
        self.fig_tzx = self._make_fig("Tipper Amplitude (Tzx)", "linear")
        self.fig_rho_yx = self._make_fig("Apparent Resistivity (YX)", "log")
        self.fig_ph_yx = self._make_fig("Phase (YX) (+180°)", "linear")
        self.fig_tzy = self._make_fig("Tipper Amplitude (Tzy)", "linear")

        self.grid = gridplot(
            [
                [self.fig_rho_xy, self.fig_rho_yx],
                [self.fig_ph_xy, self.fig_ph_yx],
                [self.fig_tzx, self.fig_tzy],
            ],
            merge_tools=True,
        )

        self.sources = {}  # label -> dict of ColumnDataSource per component

    def _make_fig(self, title, y_type):
        p = figure(
            height=300,
            width=400,
            title=title,
            x_axis_type="log",
            y_axis_type=y_type,
            tools="pan,wheel_zoom,box_zoom,reset,save,hover",
        )
        p.xaxis.axis_label = "Period (s)"
        return p

    def add_series(self, tf_series, color):
        """Create sources & lines for a TFSeries."""
        lbl = tf_series.label
        self.sources[lbl] = {}

        def _add(fig, key):
            src = ColumnDataSource(
                dict(period=tf_series.data["period"], y=tf_series.data[key])
            )
            fig.line(
                "period", "y", source=src, color=color, line_width=2, legend_label=lbl
            )
            self.sources[lbl][key] = src

        # Expect tf_series.data keys: rho_xy, ph_xy, tip_zx_amp, rho_yx, ph_yx, tip_zy_amp
        _add(self.fig_rho_xy, "rho_xy")
        _add(self.fig_ph_xy, "ph_xy")
        _add(self.fig_tzx, "tip_zx_amp")
        _add(self.fig_rho_yx, "rho_yx")
        _add(self.fig_ph_yx, "ph_yx")
        _add(self.fig_tzy, "tip_zy_amp")


class Controller:
    def __init__(self, tf_series_list):
        labels = [s.label for s in tf_series_list]
        self.checkbox = pn.widgets.CheckBoxGroup(
            name="Transfer Functions", options=labels, value=labels
        )
        self.sliders = {
            s.label: pn.widgets.RangeSlider(
                name=f"Period band — {s.label}",
                start=float(np.min(s.period)),
                end=float(np.max(s.period)),
                value=(float(np.min(s.period)), float(np.max(s.period))),
                step=0.0,
                format="0.00a",
            )
            for s in tf_series_list
        }


class CompositeBuilder:
    def build(self, tf_series_list, active_labels, slider_ranges):
        comp = {
            k: []
            for k in [
                "period",
                "rho_xy",
                "rho_yx",
                "ph_xy",
                "ph_yx",
                "tip_zx_amp",
                "tip_zy_amp",
            ]
        }
        for s in tf_series_list:
            if s.label not in active_labels:
                continue
            pmin, pmax = slider_ranges[s.label]
            mask = (s.data["period"] >= pmin) & (s.data["period"] <= pmax)
            for k in comp:
                comp[k].append(s.data[k][mask])

        def _cat(k):
            return np.concatenate(comp[k]) if comp[k] else np.array([])

        period = _cat("period")
        if not period.size:
            return pd.DataFrame()
        sort_idx = np.argsort(period)
        df = pd.DataFrame(
            {
                "period": period[sort_idx],
                "rho_xy": _cat("rho_xy")[sort_idx],
                "ph_xy": _cat("ph_xy")[sort_idx],
                "tip_zx_amp": _cat("tip_zx_amp")[sort_idx],
                "rho_yx": _cat("rho_yx")[sort_idx],
                "ph_yx": _cat("ph_yx")[sort_idx],
                "tip_zy_amp": _cat("tip_zy_amp")[sort_idx],
            }
        )


import io
import panel as pn


class Exporter:
    def __init__(self, get_dataframe_callable):
        self.file_download = pn.widgets.FileDownload(
            filename="merged_composite.csv",
            button_type="primary",
            label="Download Composite CSV",
            callback=lambda: self._to_bytes(get_dataframe_callable()),
        )

    @staticmethod
    def _to_bytes(df):
        out = io.BytesIO()
        df.to_csv(out, index=False)
        out.seek(0)
        return out
