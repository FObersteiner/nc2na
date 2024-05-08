# -*- coding: utf-8 -*-
import tkinter as tk
from datetime import datetime, timezone
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional

import numpy as np
import xarray as xr
from na_lib.na1001 import FFI1001

# CONSTANTS
# these are assumed to be the same for all files.
# could make those variables (configuration) from the GUI.
TIME_KEY = "time"
DATA_DELIMITER = "\t"
VSCAL, VMISS = (
    "1",
    "nan",
)  # Note : VMISS will be adjusted if input is an integer array and specifies a missing_value
FORMAT_DIRECITVE_IVAR = "g"  # time
FORMAT_DIRECTIVE_VAR = "g"


def find_files(src: Path) -> Optional[list[Path]]:
    """Input is directory with nc files or single nc file."""
    if not src.exists():
        messagebox.showerror("ERROR", f"path '{str(src)}' does not exist")
        return None

    if src.is_file():
        return [src]

    files = list(src.glob("*.nc"))
    if not files:
        messagebox.showerror("ERROR", f"no '*.nc' files found in '{str(src)}'")
        return None

    return files


def format_var(da: xr.DataArray) -> tuple[str, list[str]]:
    """
    Since input must not me masked or scaled, we need to apply that before
    output to text.
    """
    _scale = da.attrs.get("scale", 1)
    if not np.isclose(_scale, 1):
        da.values *= _scale

    # if vmiss is not specified, we have to short-cut...
    _vmiss = da.attrs.get("missing_value") or da.attrs.get("_FillValue")
    if _vmiss is None:
        return (VMISS, [f"{v:{FORMAT_DIRECTIVE_VAR}}" for v in da.values])

    # floating point arrays must have NaN set correctly
    if isinstance(da.values[0], np.floating):
        da.values[np.isclose(da.values, _vmiss)] = np.nan
        return (VMISS, [f"{v:{FORMAT_DIRECTIVE_VAR}}" for v in da.values])

    # otherwise, the type cannot represent NaN, so we need to return actual vmiss
    return (str(_vmiss), [f"{v:{FORMAT_DIRECTIVE_VAR}}" for v in da.values])


def nc2na(src: Path) -> None:
    """Actual netCDF to NASA Ames format conversion."""
    ds = xr.load_dataset(src, decode_times=True, use_cftime=False, mask_and_scale=False)
    dst = src.parent / src.name.replace(".nc", ".na", 1)

    assert TIME_KEY in ds.variables, f"failed to find nc variable '{TIME_KEY}' in dataset"
    assert TIME_KEY in ds.dims, f"failed to find nc dimension '{TIME_KEY}' in dataset"

    time_raw_ns = ds.variables[TIME_KEY].values
    # values might be datetime or timedelta type; make sure we have Unix nanoseconds
    if not isinstance(time_raw_ns[0], (int, np.int64)):  # type: ignore
        time_raw_ns = time_raw_ns.astype(np.int64)

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
    na.ONAME += ": nc 2 na converter, https://github.com/FObersteiner/nc2na"  # type: ignore
    na.XNAME = "seconds after midnight on DATE"  # type: ignore

    # all attributes that are just strings can be merged to into SCOM:
    na.SCOM = [": ".join([a, ds.attrs[a]]) for a in ds.attrs if isinstance(ds.attrs[a], str)]
    # NCOM is just a column header
    na.NCOM = [f"{TIME_KEY}{DATA_DELIMITER}" + DATA_DELIMITER.join(v for v in vnames)]

    # NASA Ames is ASCII-encoded!! --> use '?' for non-ASCII chars
    na.SCOM = [s.encode("ascii", "replace").decode("ascii") for s in na.SCOM]
    na.NCOM = [s.encode("ascii", "replace").decode("ascii") for s in na.NCOM]

    na.VNAME = vnames
    na.VSCAL = [VSCAL for _ in vnames]
    na.X = [f"{t:{FORMAT_DIRECITVE_IVAR}}" for t in seconds_after_midnight]

    na.VMISS = []
    na.V = []
    for n in vnames:
        _vmiss, _data = format_var(ds[n])
        na.VMISS.append(_vmiss)
        na.V.append(_data)

    na.to_file(dst, sep_data=DATA_DELIMITER, overwrite=1)


def convert() -> None:
    """Wrapper around file finder and nc-2-na conversion."""
    src = Path(entry1.get())
    files = find_files(src)
    if not files:
        return

    for f in files:
        nc2na(f)


def file_dialog():
    src = filedialog.askdirectory(
        parent=root,
        initialdir=Path().home(),
        title="Select folder..",
    )
    entry1.delete(0, tk.END)
    entry1.insert(0, src)


if __name__ == "__main__":
    root = tk.Tk()

    canvas1 = tk.Canvas(root, width=600, height=300)
    canvas1.pack()

    label1 = tk.Label(
        root,
        text="Path to folder with netCDF-files (*.nc) or single nc file:",
        fg="green",
        font=("helvetica", 12, "bold"),
    )
    canvas1.create_window(300, 100, window=label1)

    entry1 = tk.Entry(root)
    canvas1.create_window(300, 150, window=entry1, width=500)

    button0 = tk.Button(text="...", command=file_dialog)
    canvas1.create_window(550, 150, window=button0)

    button1 = tk.Button(text="Convert netCDF to AMES !", command=convert)
    canvas1.create_window(300, 200, window=button1)

    root.mainloop()
