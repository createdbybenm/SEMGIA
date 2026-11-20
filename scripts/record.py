"""Recording app: live signal + AI output, a "Collect sample" button, a metadata form,
and on-screen cues (REST 8 s / CONTRACT 8 s / REST 8 s). Each sample is saved to
data/raw/sample_NNN/ and uploaded to Azure if a connection string is set.

    python scripts/record.py --source mock
    python scripts/record.py --source serial --port COM3
    python scripts/record.py --source file --file data/raw/sample_001/signal.csv   # demo fallback

--source file replays a recorded sample: "Collect sample" restarts the file so the cues match it, and the
result goes to data/demo/ (gitignored), never into data/raw/.

Headless (no window, records --count samples with the metadata from the command line):
    python scripts/record.py --no-gui --source mock --subject P001 --operator OP01 --placement-id E01
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from semgia import config  # noqa: E402
from semgia.model import MLModel, ThresholdModel  # noqa: E402
from semgia.recorder import LivePredictor, SampleRecorder  # noqa: E402
from semgia.sources import FileSource, MockSource, SerialSource  # noqa: E402
from semgia.storage import AzureUploader, last_metadata, list_samples, make_metadata  # noqa: E402

CUE_TEXT = {config.REST: "REST", config.CONTRACT: "CONTRACT"}
# form fields: (metadata key, label, dropdown choices or None for a text box)
FORM = [
    ("subject_id", "Subject ID (P001)", None),
    ("operator_id", "Operator ID (OP01)", None),
    ("placement_id", "Electrode placement (E01)", None),
    ("muscle", "Muscle", config.MUSCLES),
    ("side", "Side", config.SIDES),
    ("sensor_id", "Sensor ID", None),
    ("electrode_type", "Electrode type", None),
    ("placement_notes", "Placement notes", None),
    ("effort", "Effort", config.EFFORTS),
    ("condition", "Condition", config.CONDITIONS),
    ("notes", "Notes (technical only)", None),
]


class App:
    """Shared by GUI and headless mode: read -> predict -> (record)."""

    def __init__(self, source, model, out: Path, upload: bool):
        self.source, self.out, self.upload = source, out, upload
        self.predictor = LivePredictor(model)
        self.recorder: SampleRecorder | None = None
        self.plot_buf = np.zeros(5 * config.FS)
        self.status = "Ready. Press 'Collect sample'."
        self.number = 0  # "sample <number> of SAMPLES_PER_PLACEMENT" for the running sample

    def count(self, placement_id: str) -> int:
        """Samples already saved for this placement."""
        return sum(json.loads((d / "metadata.json").read_text()).get("placement_id") == placement_id
                   for d in list_samples(self.out))

    def start_sample(self, **fields) -> None:
        meta = make_metadata(root=self.out, **fields)  # raises ValueError on bad IDs
        self.number = self.count(meta["placement_id"]) + 1
        if hasattr(self.source, "rewind"):  # replay: start the file again so the cues match it
            self.source.rewind()
        uploader = AzureUploader(meta, conn_str=None if self.upload else "")
        self.recorder = SampleRecorder(meta, self.predictor.total, self.out, uploader)
        self.status = f"Recording {meta['sample_id']} ..."
        logging.info(self.status)

    def tick(self) -> None:
        rec = self.recorder
        self.source.set_cue(rec.cue()[0] if rec else config.REST)  # only MockSource uses it
        x = self.source.read()
        if len(x) == 0:
            return
        windows = self.predictor.push(x)
        self.plot_buf = np.concatenate([self.plot_buf, self.predictor.filtered])[-len(self.plot_buf):]
        if rec:
            rec.push(x, windows)
            if rec.calib is not None:
                self.predictor.calib = rec.calib  # newest rest baseline is used from now on
            if rec.done:
                rec.close()
                self.status = f"Saved {rec.meta['sample_id']} -> {rec.writer.dir}"
                logging.info(self.status)
                self.recorder = None

    def close(self) -> None:
        if self.recorder:  # aborted: keep the partial files, but say so
            logging.warning("Sample %s ABORTED after %.1f s - delete the folder %s",
                            self.recorder.meta["sample_id"], self.recorder.n / config.FS,
                            self.recorder.writer.dir)
            self.recorder.close()
        self.source.close()


def run_gui(app: App, scale: float = 1.0) -> None:
    import tkinter as tk
    from tkinter import messagebox, ttk

    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure

    root = tk.Tk()
    root.title("SEMGIA recorder")
    # big coloured banner: the subject must read it from a distance
    cue_lbl = tk.Label(root, text="", font=("Helvetica", int(60 * scale), "bold"), fg="white", pady=20)
    cue_lbl.pack(fill="x")
    count_lbl = tk.Label(root, text="", font=("Helvetica", int(30 * scale), "bold"))
    count_lbl.pack()
    last_cue = [None]  # beep when the cue changes
    ai_lbl = tk.Label(root, text="", font=("Helvetica", int(26 * scale)), pady=8)
    ai_lbl.pack()

    fig = Figure(figsize=(9, 3.5))
    ax = fig.add_subplot()
    t = np.arange(len(app.plot_buf)) / config.FS - 5
    (line,) = ax.plot(t, app.plot_buf, lw=0.6)
    ax.set_xlabel("time [s]")
    canvas = FigureCanvasTkAgg(fig, root)
    canvas.get_tk_widget().pack(fill="both", expand=True)

    bottom = tk.Frame(root)
    bottom.pack(fill="x", pady=8)
    status_lbl = tk.Label(bottom, text="", anchor="w", font=("Helvetica", int(12 * scale)))
    status_lbl.pack(side="left", padx=10, fill="x", expand=True)
    collect_btn = tk.Button(bottom, text="Collect sample", font=("Helvetica", int(20 * scale), "bold"))
    collect_btn.pack(side="right", padx=10)

    def open_form():
        defaults = last_metadata(app.out)
        win = tk.Toplevel(root)
        win.title("Sample metadata")
        win.grab_set()
        widgets = {}
        for r, (key, label, choices) in enumerate(FORM):
            tk.Label(win, text=label, anchor="w").grid(row=r, column=0, sticky="w", padx=8, pady=2)
            var = tk.StringVar(value=defaults.get(key) or (choices[0] if choices else ""))
            w = ttk.Combobox(win, textvariable=var, values=choices, state="readonly") if choices \
                else tk.Entry(win, textvariable=var, width=30)
            w.grid(row=r, column=1, padx=8, pady=2, sticky="we")
            widgets[key] = var
        tk.Label(win, text="New electrodes? -> increase the placement number (E01 -> E02).",
                 fg="gray").grid(row=len(FORM), column=0, columnspan=2, pady=4)

        def start():
            try:
                app.start_sample(**{k: v.get().strip() for k, v in widgets.items()})
            except ValueError as e:
                messagebox.showerror("Check the form", str(e), parent=win)
                return
            win.destroy()

        tk.Button(win, text="Start recording (24 s)", command=start).grid(
            row=len(FORM) + 1, column=0, columnspan=2, pady=8)

    collect_btn.configure(command=open_form)

    def update():
        app.tick()
        rec = app.recorder
        if rec:
            cue, left = rec.cue()
            cue_lbl.configure(text=f"{CUE_TEXT[cue]}  {left:4.1f} s",
                              bg="#c0392b" if cue == config.CONTRACT else "#27ae60")
            count_lbl.configure(text=f"Sample {app.number} of {config.SAMPLES_PER_PLACEMENT}"
                                     f"  ·  {rec.meta['placement_id']}")
            collect_btn.configure(state="disabled")
        else:
            cue = None
            cue_lbl.configure(text="ready", bg="#7f8c8d")
            count_lbl.configure(text="")
            collect_btn.configure(state="normal")
        if cue != last_cue[0]:
            root.bell()  # start, every REST <-> CONTRACT switch, and the end
            last_cue[0] = cue
        pred = app.predictor.pred
        if app.predictor.calib is None:
            ai_lbl.configure(text="AI: waiting for a rest baseline (first 8 s of a sample)", fg="gray")
        else:
            ai_lbl.configure(text=f"AI says: {'CONTRACTION' if pred == config.CONTRACT else 'rest'}",
                             fg="red" if pred == config.CONTRACT else "green")
        status_lbl.configure(text=app.status)
        line.set_ydata(app.plot_buf)
        lim = max(np.abs(app.plot_buf).max() * 1.1, 10)
        ax.set_ylim(-lim if config.RAW_SIGNAL else 0, lim)
        canvas.draw_idle()
        root.after(50, update)

    def on_close():
        if app.recorder and not messagebox.askyesno("Quit", "A sample is being recorded. Quit anyway?"):
            return
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.after(50, update)
    root.mainloop()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--source", choices=["mock", "serial", "file"], default="mock")
    p.add_argument("--port", default="/dev/ttyACM0", help="serial port (Windows: COM3)")
    p.add_argument("--file", help="signal.csv to replay with --source file")
    p.add_argument("--model", choices=["threshold", "ml"], default="threshold")
    p.add_argument("--out", help="where samples are saved (default data/raw, with --source file data/demo)")
    p.add_argument("--no-upload", action="store_true")
    p.add_argument("--font-scale", type=float, default=1.0, help="bigger/smaller text, e.g. 2 on a 4K screen")
    g = p.add_argument_group("headless mode")
    g.add_argument("--no-gui", action="store_true", help="no window, record --count samples")
    g.add_argument("--count", type=int, default=1)
    g.add_argument("--subject", default="P000", help="P000 = test")
    g.add_argument("--operator", default="OP00")
    g.add_argument("--placement-id", default="E00")
    g.add_argument("--muscle", default=config.MUSCLES[0])
    g.add_argument("--side", default=config.SIDES[0])
    a = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load_dotenv()

    if a.source == "mock":
        source = MockSource()
    elif a.source == "file":
        if not a.file:
            p.error("--source file needs --file data/raw/sample_NNN/signal.csv")
        source = FileSource(a.file)
    else:
        source = SerialSource(a.port)
    model = MLModel.load() if a.model == "ml" else ThresholdModel()
    out = Path(a.out) if a.out else config.DATA_DEMO if a.source == "file" else config.DATA_RAW
    app = App(source, model, out, upload=not a.no_upload and a.source != "file")

    try:
        if a.no_gui:
            for _ in range(a.count):
                app.start_sample(subject_id=a.subject, operator_id=a.operator, placement_id=a.placement_id,
                                 muscle=a.muscle, side=a.side, sensor_id=a.source)
                while app.recorder:
                    app.tick()
                    time.sleep(0.02)
        else:
            run_gui(app, a.font_scale)
    finally:
        app.close()


if __name__ == "__main__":
    main()
