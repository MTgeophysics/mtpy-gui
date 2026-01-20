# mt_multi_panel_app.py
import io
import os
import tempfile
import math
import numpy as np
import pandas as pd

import panel as pn
from bokeh.plotting import figure
from bokeh.layouts import gridplot
from bokeh.palettes import Category10
from bokeh.models import ColumnDataSource

# mtpy-v2 reading (MT inherits TF with read/write support across EDI/XML/J/Z/AVG)
try:
    from mtpy import MT
except ImportError:
    MT = None

pn.extension()

MU0 = 4e-7 * math.pi

SUPPORTED_EXTS = {".edi", ".xml", ".zmm", ".zss", ".zrr", ".avg", ".j"}


# -------------------------
# Helpers for MT extraction
# -------------------------
def _get_period(mt):
    p = getattr(mt, "period", None)
    if p is not None and len(p):
        return np.asarray(p)


def _get_rho_phase(mt):
    Z = getattr(mt, "Z", None)
    if Z is None:
        raise ValueError("MT object missing Z tensor.")
    rho_xy = getattr(Z, "res_xy", None)
    rho_yx = getattr(Z, "res_yx", None)
    ph_xy = getattr(Z, "phase_xy", None)
    ph_yx = getattr(Z, "phase_yx", None)

    if rho_xy is None or rho_yx is None or ph_xy is None or ph_yx is None:
        z = np.asarray(Z.z)
        period = _get_period(mt)
        omega = 2.0 * math.pi / period
        rho = (np.abs(z) ** 2) / (MU0 * omega)[:, None, None]
        rho_xy = rho[:, 0, 1]
        rho_yx = rho[:, 1, 0]
        ph = np.rad2deg(np.angle(z))
        ph_xy = ph[:, 0, 1]
        ph_yx = ph[:, 1, 0]
    # Add 180° to YX phase to match plot_mt_response convention
    ph_yx = np.asarray(ph_yx) + 180.0
    return np.asarray(rho_xy), np.asarray(rho_yx), np.asarray(ph_xy), np.asarray(ph_yx)


def _get_tipper_amplitude(mt):
    T = getattr(mt, "Tipper", None)
    if T is None:
        n = len(_get_period(mt))
        return np.zeros(n), np.zeros(n)
    amp = getattr(T, "amplitude", None)
    if amp is not None:
        amp = np.asarray(amp)  # shape: (n, 2)
        return amp[:, 0], amp[:, 1]
    tip = np.asarray(T.tipper)  # (n, 2) or (n, 1, 2)
    if tip.ndim == 3:
        tip = tip[:, 0, :]
    return np.abs(tip[:, 0]), np.abs(tip[:, 1])


def _label_for_mt(mt):
    for attr in ("station",):
        if hasattr(mt, attr) and getattr(mt, attr):
            return getattr(mt, attr)
    sm = getattr(mt, "station_metadata", None)
    if sm is not None:
        sid = getattr(sm, "id", None)
        if sid:
            return sid
    return "MT"


# -------------------------
# Data container per TF
# -------------------------
class TFSeries:
    def __init__(self, mt_obj, label=None, color=None):
        self.mt = mt_obj
        self.label = label or _label_for_mt(mt_obj)
        self.period = _get_period(mt_obj)
        rho_xy, rho_yx, ph_xy, ph_yx = _get_rho_phase(mt_obj)
        tip_zx, tip_zy = _get_tipper_amplitude(mt_obj)
        self.data = dict(
            period=self.period,
            rho_xy=rho_xy,
            rho_yx=rho_yx,
            ph_xy=ph_xy,
            ph_yx=ph_yx,
            tip_zx_amp=tip_zx,
            tip_zy_amp=tip_zy,
        )
        self.color = color


# -------------------------
# Plotting/Interaction core
# -------------------------
class MTMultiResponseApp:
    def __init__(self, tf_series):
        self.tf_series = tf_series[:]  # list[TFSeries]
        self.labels = [s.label for s in self.tf_series]
        self._build_controls()
        self._make_plots()
        self._wire_callbacks()
        self._build_composite()
        self.view = self._layout()

    def _build_controls(self):
        self.checkbox = pn.widgets.CheckBoxGroup(
            name="Transfer Functions",
            options=self.labels,
            value=list(self.labels),
            inline=False,
        )
        self.period_sliders = {
            s.label: pn.widgets.RangeSlider(
                name=f"Period band — {s.label}",
                start=float(np.min(s.period)),
                end=float(np.max(s.period)),
                value=(float(np.min(s.period)), float(np.max(s.period))),
                step=0.0,
                format="0.00a",
            )
            for s in self.tf_series
        }
        self.btn_build = pn.widgets.Button(
            name="Build merged composite", button_type="primary"
        )
        self.show_composite = pn.widgets.Checkbox(
            name="Show composite curve", value=True
        )

    def _make_fig(self, title, y_axis_type="linear", x_axis_type="log"):
        p = figure(
            height=300,
            width=400,
            title=title,
            x_axis_type=x_axis_type,
            y_axis_type=y_axis_type,
            toolbar_location="above",
            tools="pan,wheel_zoom,box_zoom,reset,save,hover",
        )
        p.xaxis.axis_label = "Period (s)"
        return p

    def _make_plots(self):
        self.fig_rho_xy = self._make_fig("Apparent Resistivity (XY)", y_axis_type="log")
        self.fig_ph_xy = self._make_fig("Phase (XY)", y_axis_type="linear")
        self.fig_tzx = self._make_fig("Tipper Amplitude (Tzx)", y_axis_type="linear")

        self.fig_rho_yx = self._make_fig("Apparent Resistivity (YX)", y_axis_type="log")
        self.fig_ph_yx = self._make_fig("Phase (YX) (+180°)", y_axis_type="linear")
        self.fig_tzy = self._make_fig("Tipper Amplitude (Tzy)", y_axis_type="linear")

        self.glyphs = {lbl: [] for lbl in self.labels}
        for s in self.tf_series:
            # Left column
            src = ColumnDataSource(dict(period=s.data["period"], y=s.data["rho_xy"]))
            g = self.fig_rho_xy.line(
                "period",
                "y",
                source=src,
                color=s.color,
                line_width=2,
                legend_label=s.label,
            )
            self.glyphs[s.label].append((g, src, "rho_xy"))
            src = ColumnDataSource(dict(period=s.data["period"], y=s.data["ph_xy"]))
            g = self.fig_ph_xy.line(
                "period",
                "y",
                source=src,
                color=s.color,
                line_width=2,
                legend_label=s.label,
            )
            self.glyphs[s.label].append((g, src, "ph_xy"))
            src = ColumnDataSource(
                dict(period=s.data["period"], y=s.data["tip_zx_amp"])
            )
            g = self.fig_tzx.line(
                "period",
                "y",
                source=src,
                color=s.color,
                line_width=2,
                legend_label=s.label,
            )
            self.glyphs[s.label].append((g, src, "tip_zx_amp"))

            # Right column
            src = ColumnDataSource(dict(period=s.data["period"], y=s.data["rho_yx"]))
            g = self.fig_rho_yx.line(
                "period",
                "y",
                source=src,
                color=s.color,
                line_width=2,
                legend_label=s.label,
            )
            self.glyphs[s.label].append((g, src, "rho_yx"))
            src = ColumnDataSource(dict(period=s.data["period"], y=s.data["ph_yx"]))
            g = self.fig_ph_yx.line(
                "period",
                "y",
                source=src,
                color=s.color,
                line_width=2,
                legend_label=s.label,
            )
            self.glyphs[s.label].append((g, src, "ph_yx"))
            src = ColumnDataSource(
                dict(period=s.data["period"], y=s.data["tip_zy_amp"])
            )
            g = self.fig_tzy.line(
                "period",
                "y",
                source=src,
                color=s.color,
                line_width=2,
                legend_label=s.label,
            )
            self.glyphs[s.label].append((g, src, "tip_zy_amp"))

        self.comp_srcs = dict(
            rho_xy=ColumnDataSource(dict(period=[], y=[])),
            ph_xy=ColumnDataSource(dict(period=[], y=[])),
            tip_zx_amp=ColumnDataSource(dict(period=[], y=[])),
            rho_yx=ColumnDataSource(dict(period=[], y=[])),
            ph_yx=ColumnDataSource(dict(period=[], y=[])),
            tip_zy_amp=ColumnDataSource(dict(period=[], y=[])),
        )
        comp_style = dict(
            color="black", line_width=4, line_alpha=0.8, line_dash="solid"
        )
        self.comp_glyphs = dict(
            rho_xy=self.fig_rho_xy.line(
                "period",
                "y",
                source=self.comp_srcs["rho_xy"],
                **comp_style,
                legend_label="Composite",
            ),
            ph_xy=self.fig_ph_xy.line(
                "period",
                "y",
                source=self.comp_srcs["ph_xy"],
                **comp_style,
                legend_label="Composite",
            ),
            tip_zx_amp=self.fig_tzx.line(
                "period",
                "y",
                source=self.comp_srcs["tip_zx_amp"],
                **comp_style,
                legend_label="Composite",
            ),
            rho_yx=self.fig_rho_yx.line(
                "period",
                "y",
                source=self.comp_srcs["rho_yx"],
                **comp_style,
                legend_label="Composite",
            ),
            ph_yx=self.fig_ph_yx.line(
                "period",
                "y",
                source=self.comp_srcs["ph_yx"],
                **comp_style,
                legend_label="Composite",
            ),
            tip_zy_amp=self.fig_tzy.line(
                "period",
                "y",
                source=self.comp_srcs["tip_zy_amp"],
                **comp_style,
                legend_label="Composite",
            ),
        )
        for f in (
            self.fig_rho_xy,
            self.fig_ph_xy,
            self.fig_tzx,
            self.fig_rho_yx,
            self.fig_ph_yx,
            self.fig_tzy,
        ):
            f.legend.click_policy = "hide"

        self.grid = gridplot(
            [
                [self.fig_rho_xy, self.fig_rho_yx],
                [self.fig_ph_xy, self.fig_ph_yx],
                [self.fig_tzx, self.fig_tzy],
            ],
            merge_tools=True,
        )

    def _wire_callbacks(self):
        self.checkbox.param.watch(self._update_visibility, "value")
        for sl in self.period_sliders.values():
            sl.param.watch(self._auto_rebuild_composite, "value")
        self.btn_build.on_click(self._build_composite)
        self.show_composite.param.watch(self._toggle_composite_visibility, "value")

    def _update_visibility(self, event):
        active = set(event.new)
        for label, g_list in self.glyphs.items():
            visible = label in active
            for g, _, _ in g_list:
                g.visible = visible

    def _toggle_composite_visibility(self, event):
        vis = bool(event.new)
        for g in self.comp_glyphs.values():
            g.visible = vis

    def _auto_rebuild_composite(self, _):
        self._build_composite()

    def _build_composite(self, *_):
        selected = set(self.checkbox.value)
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
        for s in self.tf_series:
            if s.label not in selected:
                continue
            pmin, pmax = self.period_sliders[s.label].value
            mask = (s.data["period"] >= pmin) & (s.data["period"] <= pmax)
            for k in comp:
                comp[k].append(s.data[k][mask])

        def _cat(key):
            return np.concatenate(comp[key]) if comp[key] else np.array([])

        period = _cat("period")
        if period.size:
            sort_idx = np.argsort(period)

            def _sorted(key):
                return _cat(key)[sort_idx]

            self.comp_srcs["rho_xy"].data = dict(
                period=period[sort_idx], y=_sorted("rho_xy")
            )
            self.comp_srcs["ph_xy"].data = dict(
                period=period[sort_idx], y=_sorted("ph_xy")
            )
            self.comp_srcs["tip_zx_amp"].data = dict(
                period=period[sort_idx], y=_sorted("tip_zx_amp")
            )
            self.comp_srcs["rho_yx"].data = dict(
                period=period[sort_idx], y=_sorted("rho_yx")
            )
            self.comp_srcs["ph_yx"].data = dict(
                period=period[sort_idx], y=_sorted("ph_yx")
            )
            self.comp_srcs["tip_zy_amp"].data = dict(
                period=period[sort_idx], y=_sorted("tip_zy_amp")
            )
        else:
            for k in self.comp_srcs:
                self.comp_srcs[k].data = dict(period=[], y=[])

    def _layout(self):
        sliders_col = pn.Column(
            "# Period bands per TF",
            *self.period_sliders.values(),
            sizing_mode="stretch_width",
        )
        controls = pn.Row(
            self.checkbox,
            pn.Spacer(width=20),
            pn.Column(self.btn_build, self.show_composite),
        )
        return pn.Column(
            "## MT Multi‑Response Viewer",
            controls,
            pn.Row(
                sliders_col,
                pn.Spacer(width=15),
                pn.pane.Bokeh(self.grid, sizing_mode="stretch_both"),
            ),
            sizing_mode="stretch_both",
        )

    # ---------------------
    # Export helpers
    # ---------------------
    def composite_dataframe(self):
        """Return a tidy DataFrame of the current composite lines (period + components)."""
        df = pd.DataFrame(
            {
                "period": self.comp_srcs["rho_xy"].data["period"],
                "rho_xy": self.comp_srcs["rho_xy"].data["y"],
                "ph_xy": self.comp_srcs["ph_xy"].data["y"],
                "tip_zx_amp": self.comp_srcs["tip_zx_amp"].data["y"],
                "rho_yx": self.comp_srcs["rho_yx"].data["y"],
                "ph_yx": self.comp_srcs["ph_yx"].data["y"],
                "tip_zy_amp": self.comp_srcs["tip_zy_amp"].data["y"],
            }
        )
        return df

    def save_composite_csv(self, output_path):
        df = self.composite_dataframe()
        if not len(df):
            raise RuntimeError(
                "Composite is empty; build composite or select TFs first."
            )
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        df.to_csv(output_path, index=False)


# -------------------------
# App shell: file picking + export
# -------------------------
class AppShell:
    def __init__(self, root_dir="."):
        # --- File selection widgets ---
        # Server-side selection
        self.file_selector = pn.widgets.FileSelector(
            directory=root_dir,
            root_directory=root_dir,
            only_files=True,
            show_hidden=False,
        )  # Allows picking multiple files on server [1](https://panel.holoviz.org/reference/widgets/FileSelector.html)

        # Client uploads
        self.file_input = pn.widgets.FileInput(
            accept=".edi,.xml,.zmm,.zss,.zrr,.avg,.j", multiple=True
        )  # [2](https://panel.holoviz.org/reference/widgets/FileInput.html)

        self.btn_load = pn.widgets.Button(
            name="Load selected/uploaded files", button_type="primary"
        )
        self.btn_clear = pn.widgets.Button(
            name="Clear current plots", button_type="warning"
        )

        # Export widgets
        self.export_download = pn.widgets.FileDownload(
            filename="merged_composite.csv",
            button_type="primary",
            label="Download Composite CSV",
            callback=self._download_callback,
        )  # dynamic callback returns BytesIO [3](https://panel.holoviz.org/reference/widgets/FileDownload.html)[4](https://docs.holoviz.org/panel/0.14.4/gallery/simple/file_download_examples.html)

        self.output_path = pn.widgets.TextInput(
            name="Server output path (CSV)",
            placeholder="./outputs/merged_composite.csv",
        )
        self.btn_save_server = pn.widgets.Button(
            name="Save Composite to Server Path", button_type="default"
        )

        # Container for the plotting app
        self.inner = None
        self.inner_box = pn.Column(height=0)  # placeholder

        # Wire
        self.btn_load.on_click(self._load_files)
        self.btn_clear.on_click(self._clear)
        self.btn_save_server.on_click(self._save_to_server)

        # Layout
        self.view = pn.Column(
            "## File Picker + MT Multi‑Response App",
            pn.Row(
                pn.Column(
                    "### Pick files on server",
                    self.file_selector,
                    sizing_mode="stretch_both",
                ),
                pn.Spacer(width=20),
                pn.Column(
                    "### Or upload files", self.file_input, sizing_mode="stretch_both"
                ),
            ),
            pn.Row(self.btn_load, self.btn_clear, sizing_mode="stretch_width"),
            pn.Row(self.export_download, self.output_path, self.btn_save_server),
            pn.Spacer(height=10),
            self.inner_box,
            sizing_mode="stretch_both",
        )

    def _load_files(self, *_):
        paths = []
        # From FileSelector (server-side)
        if self.file_selector.value:
            for p in self.file_selector.value:
                ext = os.path.splitext(p)[1].lower()
                if ext in SUPPORTED_EXTS:
                    paths.append(p)

        # From FileInput (uploads)
        if self.file_input.value is not None:
            # Multiple uploads => lists of filenames & bytes; write to tmp files
            filenames = self.file_input.filename
            values = self.file_input.value
            if isinstance(filenames, list) and isinstance(values, list):
                for fname, val in zip(filenames, values):
                    ext = os.path.splitext(fname)[1].lower()
                    if ext in SUPPORTED_EXTS:
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                        tmp.write(val)
                        tmp.close()
                        paths.append(tmp.name)
            else:
                # single file
                fname = self.file_input.filename
                val = self.file_input.value
                if fname and val:
                    ext = os.path.splitext(fname)[1].lower()
                    if ext in SUPPORTED_EXTS:
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                        tmp.write(val)
                        tmp.close()
                        paths.append(tmp.name)

        if not paths:
            pn.notification(
                "No valid TF files selected or uploaded.",
                title="Warning",
                severity="warning",
            ).push()
            return

        # Build TFSeries list
        if MT is None:
            pn.notification(
                "mtpy‑v2 not installed; cannot read MT files.",
                title="Error",
                severity="error",
            ).push()
            return

        tf_series = []
        palette = Category10[10]
        for i, path in enumerate(paths):
            mt = MT(
                fn=path
            )  # MT can read various TF formats; call read() to populate TF data [5](http://mtpy-v2.readthedocs.io/)
            mt.read()
            tf_series.append(TFSeries(mt_obj=mt, color=palette[i % len(palette)]))

        # Instantiate plotting app
        self.inner = MTMultiResponseApp(tf_series)
        self.inner_box.objects = [self.inner.view]

    def _clear(self, *_):
        self.inner = None
        self.inner_box.objects = []
        self.file_selector.value = []
        self.file_input.clear()

    def _download_callback(self):
        """Return composite CSV as BytesIO for FileDownload."""
        if self.inner is None:
            return io.BytesIO(b"")
        df = self.inner.composite_dataframe()
        out = io.BytesIO()
        df.to_csv(out, index=False)
        out.seek(0)
        return out

    def _save_to_server(self, *_):
        if self.inner is None:
            pn.notification(
                "No plots loaded; load files first.",
                title="Warning",
                severity="warning",
            ).push()
            return
        path = self.output_path.value.strip()
        if not path:
            pn.notification(
                "Provide an output path.", title="Warning", severity="warning"
            ).push()
            return
        try:
            self.inner.save_composite_csv(path)
            pn.notification(
                f"Saved composite CSV → {path}", title="Saved", severity="success"
            ).push()
        except Exception as err:
            pn.notification(
                f"Failed to save: {err}", title="Error", severity="error"
            ).push()


# -------------------------
# Entrypoint
# -------------------------
def create_app(root_dir="."):
    shell = AppShell(root_dir=root_dir)
    return shell.view


# Serve
create_app().servable()
