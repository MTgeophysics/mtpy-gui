# stage1_loader.py
import os
from pathlib import Path
import tempfile
import numpy as np
import pandas as pd
import panel as pn

# mtpy-v2 for MT read; install via conda-forge or pip
from mtpy import MT

pn.extension()  # Bokeh loads by default; do NOT pass 'bokeh'

SUPPORTED_EXTS = [".edi", ".xml", ".zmm", ".zss", ".zrr", ".avg", ".j"]


# ---------- Model wrapper ----------
class TFSeries:
    """Thin wrapper over mtpy-v2 MT object that extracts arrays for plotting/summary."""

    def __init__(self, mt_object: MT):
        self.mt_object = mt_object
        self.label = self._get_label(mt_object)
        self.period = self._get_period(mt_object)

    @staticmethod
    def _get_label(mt_object: MT) -> str:
        return f"{mt_object.survey}_{mt_object.station}"

    @staticmethod
    def _get_period(mt_object):
        p = getattr(mt_object, "period", None)
        if p is not None and len(p):
            return np.asarray(p)
        else:
            raise ValueError("MT object has no period data.")


# ---------- IO / Loader ----------
class TFLoader:
    """Manages file picking/upload & converts files to TFSeries."""

    def __init__(self, start_dir=None):
        start_dir = start_dir or str(Path.home())
        self.dir_input = Path(
            pn.widgets.TextInput(name="Directory", value=start_dir).value.strip()
        )
        self.btn_set_dir = pn.widgets.Button(
            name="Set directory", button_type="default"
        )

        self.file_selector = pn.widgets.FileSelector(
            directory=start_dir,
            root_directory=start_dir,
            only_files=True,
            show_hidden=False,
        )

        self.file_input = pn.widgets.FileInput(
            accept=",".join(SUPPORTED_EXTS), multiple=True
        )

        self.btn_load = pn.widgets.Button(name="Load files", button_type="primary")
        self.btn_clear = pn.widgets.Button(name="Clear", button_type="warning")

        self.status = pn.pane.Alert("Ready.", alert_type="success")
        self.summary = pn.pane.DataFrame(pd.DataFrame(), height=240)

        self.tf_series = []  # list[TFSeries]

        # Wire events
        self.btn_set_dir.on_click(self._set_directory)
        self.btn_load.on_click(self._load_files)
        self.btn_clear.on_click(self._clear)

        # Layout
        self.view = pn.Column(
            "## Stage 1 — File Selection",
            pn.Row(
                pn.Column(
                    "### Pick files on server",
                    pn.Row(self.dir_input, self.btn_set_dir),
                    self.file_selector,
                ),
                pn.Spacer(width=15),
                pn.Column("### Or upload files", self.file_input),
            ),
            pn.Row(self.btn_load, self.btn_clear),
            self.status,
            pn.pane.Markdown("### Loaded Transfer Functions (summary)"),
            self.summary,
            sizing_mode="stretch_width",
        )

    # ---- handlers ----
    def _set_directory(self, *_):
        new_dir = self.dir_input
        if not new_dir.is_dir():
            self.status.object = f"Not a directory: {new_dir}"
            self.status.alert_type = "danger"
            return
        self.file_selector.directory = new_dir.as_posix()
        self.file_selector.root_directory = new_dir.as_posix()
        self.status.object = f"Directory set: {new_dir}"
        self.status.alert_type = "info"

    def _load_files(self, *_):
        paths = []
        # From FileSelector
        for p in self.file_selector.value or []:
            fn = Path(p)
            if fn.suffix.lower() in SUPPORTED_EXTS:
                paths.append(fn)
        # From FileInput
        fnames = self.file_input.filename
        vals = self.file_input.value
        if isinstance(fnames, list) and isinstance(vals, list):
            for fname, data in zip(fnames, vals):
                ext = os.path.splitext(fname)[1].lower()
                if ext in SUPPORTED_EXTS:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                    tmp.write(data)
                    tmp.close()
                    paths.append(tmp.name)
        elif fnames and vals:
            ext = os.path.splitext(fnames)[1].lower()
            if ext in SUPPORTED_EXTS:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                tmp.write(vals)
                tmp.close()
                paths.append(tmp.name)

        if not paths:
            self.status.object = (
                "No valid .edi/.xml/.j/.zmm/.zss/.zrr/.avg files selected or uploaded."
            )
            self.status.alert_type = "warning"
            return

        # Read files into MT objects (mtpy-v2 uses MT(fn=...).read())
        self.tf_series.clear()
        for path in paths:
            mt = MT(fn=path)
            mt.read()  # populate TF data  # [4](https://discourse.holoviz.org/t/create-a-save-as-button/8819)
            self.tf_series.append(TFSeries(mt))

        self._refresh_summary()
        self.status.object = f"Loaded {len(self.tf_series)} transfer function(s)."
        self.status.alert_type = "success"

    def _clear(self, *_):
        self.tf_series.clear()
        self.file_selector.value = []
        self.file_input.clear()
        self.summary.object = pd.DataFrame(
            columns=["label", "n_periods", "period_min", "period_max", "has_tipper"]
        )
        self.status.object = "Cleared."
        self.status.alert_type = "info"

    def _refresh_summary(self):
        rows = []
        for s in self.tf_series:
            rows.append(
                dict(
                    label=s.label,
                    n_periods=len(s.period),
                    period_min=float(np.min(s.period)),
                    period_max=float(np.max(s.period)),
                    has_impedance=bool(s.mt_object.has_impedance()),
                    has_tipper=bool(s.mt_object.has_tipper()),
                )
            )
        self.summary.object = pd.DataFrame(rows)


# ---------- Entrypoint ----------
def serveable():
    loader = TFLoader()
    return loader.view


# IMPORTANT: make discoverable to 'panel serve'
serveable().servable()
