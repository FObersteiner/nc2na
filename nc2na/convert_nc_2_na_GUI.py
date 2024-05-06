# -*- coding: utf-8 -*-
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from typing import Optional
from datetime import datetime, timezone
import xarray as xr

from na_lib.na1001 import FFI1001

# CONSTANTS
# these are assumed to be the same for all files.
# could make those variables (configuration) from the GUI.
TIME_KEY = "time"
DATA_DELIMITER = "\t"
VSCAL, VMISS = "1", "nan"
FORMAT_DIRECITVE_IVAR = "g"  # time
FORMAT_DIRECTIVE_VAR = "g"


def find_files(src: Path) -> Optional[list[Path]]:
    if not src.exists():
        messagebox.showerror("ERROR", f"path '{str(src)}' does not exist")
        return None
    files = list(src.glob("*.nc"))
    if not files:
        messagebox.showerror("ERROR", f"no nc files found in '{str(src)}'")
        return None
    return files


def nc2na(src: Path) -> None:
    ds = xr.load_dataset(src, decode_times=True, use_cftime=False)
    dst = src.parent / src.name.replace(".nc", ".na", 1)

    assert TIME_KEY in ds.variables, f"failed to find nc variable '{TIME_KEY}' in dataset"
    assert TIME_KEY in ds.dims, f"failed to find nc dimension '{TIME_KEY}' in dataset"

    # values might be datetime or timedelta type; make sure we have Unix nanoseconds
    time_raw_ns = ds.variables[TIME_KEY].values
    if not isinstance(time_raw_ns[0], int):  # type: ignore
        time_raw_ns = time_raw_ns.astype(int)

    # convert to seconds after midnight
    time_unix_s = time_raw_ns / 1e9  # type: ignore
    t_0 = datetime.fromtimestamp(time_unix_s[0], timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    t0 = t_0.timestamp()
    seconds_after_midnight = time_unix_s - t0

    vnames = [str(v) for v in ds.variables if v != TIME_KEY and ds.variables[v].dims[0] == TIME_KEY]

    na = FFI1001()

    na.DATE = (t_0.year, t_0.month, t_0.day)  # type: ignore
    na.ONAME += ": nc 2 na converter"  # type: ignore
    na.XNAME = "seconds after midnight on DATE"  # type: ignore

    # all attributes that are just strings can be merged to into SCOM:
    na.SCOM = [": ".join([a, ds.attrs[a]]) for a in ds.attrs if isinstance(ds.attrs[a], str)]
    # NCOM is just a column header
    na.NCOM = [f"{TIME_KEY}{DATA_DELIMITER}" + DATA_DELIMITER.join(v for v in vnames)]

    # NASA Ames is ASCII-encoded!! --> use '?' for non-printable chars
    na.SCOM = [s.encode("ascii", "replace").decode("ascii") for s in na.SCOM]
    na.NCOM = [s.encode("ascii", "replace").decode("ascii") for s in na.NCOM]

    na.VNAME = vnames
    na.VSCAL = [VSCAL for _ in vnames]
    na.VMISS = [VMISS for _ in vnames]
    na.X = [f"{t:{FORMAT_DIRECITVE_IVAR}}" for t in seconds_after_midnight]
    na.V = [[f"{v:{FORMAT_DIRECTIVE_VAR}}" for v in ds.variables[n]] for n in vnames]

    na.to_file(dst, sep_data=DATA_DELIMITER, overwrite=1)


def convert() -> None:
    src = Path(entry1.get())
    files = find_files(src)
    if not files:
        return

    for f in files:
        nc2na(f)


root = tk.Tk()
canvas1 = tk.Canvas(root, width=600, height=300)
canvas1.pack()
label1 = tk.Label(
    root,
    text="Ordner mit NetCDF-Files (*.nc) angeben:",
    fg="green",
    font=("helvetica", 12, "bold"),
)
canvas1.create_window(300, 100, window=label1)
entry1 = tk.Entry(root)
canvas1.create_window(300, 150, window=entry1, width=500)
button1 = tk.Button(text="Convert netCDF to AMES !", command=convert)
canvas1.create_window(300, 200, window=button1)

root.mainloop()
