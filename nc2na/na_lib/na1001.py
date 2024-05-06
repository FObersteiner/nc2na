# -*- coding: utf-8 -*-
"""NASA Ames FFI 1001 text file format reader / writer."""

import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Union

import numpy as np


class FFI1001(object):
    r"""
    A class to work with NASA Ames files with format index 1001.

    Parameters
    ----------
    file : str or pathlib.Path or file-like
        data source.
    sep : str, optional
        General delimiter. The default is " ".
    sep_data : str, optional
        Delimiter used exclusively in data block. The default is "\t".
    strip_lines : bool, optional
        Remove surrounding whitespaces from all lines before parsing.
        The default is True.
    auto_nncoml : bool, optional
        Automatically determine number of lines in comment blocks.
        The default is True.
    rmv_repeated_seps : bool, optional
        Remove repeated delimiters (e.g. double space). The default is False.
    vscale_vmiss_vertical : bool, optional
        VSCALE and VMISS parameters are arranged vertically over multiple
        lines (1 entry per line) instead of in one line each.
        The default is False.
    vmiss_to_None : bool, optional
        Set True if missing values should be replaced with None. The default is False.
    ensure_ascii : bool, optional
        Enforce ASCII-decoding of the input. The default is True.
    allow_emtpy_data : bool, optional
        Allow header-only input. The default is False.

    Returns
    -------
    FFI 1001 class instance.
    """

    def __init__(self, file=None, **kwargs):
        today = datetime.now(timezone.utc).date()
        self.NLHEAD = 14  # minimum number of header lines is 14
        self.ONAME = "data origin"
        self.ORG = "organization"
        self.SNAME = "sampling description"
        self.MNAME = "mission name"
        self.IVOL = 1
        self.NVOL = 1
        self.DATE = (1970, 1, 1)
        self.RDATE = (today.year, today.month, today.day)
        self.DX = 0
        self.XNAME = "x name"
        self.NV = 1
        self.VSCAL = ["1"]
        self.VMISS = ["-9999"]
        self._VNAME = ["v names"]
        self.NSCOML = 0
        self._SCOM = ["special comments"]
        self.NNCOML = 0
        self._NCOM = ["normal comments"]
        self._X = [""]
        self.V = [[""]]
        self._SRC = "path to file"
        self._HEADER = "file header"

        if file is not None:
            self.__from_file(file, **kwargs)

    @property
    def FFI(self):
        """FFI is always 1001, as the class name indicates..."""
        return 1001

    @property
    def SCOM(self) -> list[str]:
        """Special comments block"""
        return self._SCOM

    @SCOM.setter
    def SCOM(self, value: list[str]):
        self._SCOM, self.NSCOML = value, len(value)
        self.NLHEAD = 14 + self.NSCOML + self.NNCOML + self.NV

    @property
    def NCOM(self) -> list[str]:
        """Normal comments block"""
        return self._NCOM

    @NCOM.setter
    def NCOM(self, value: list[str]):
        self._NCOM, self.NNCOML = value, len(value)
        self.NLHEAD = 14 + self.NSCOML + self.NNCOML + self.NV

    @property
    def VNAME(self) -> list[str]:
        """Variables name block"""
        return self._VNAME

    @VNAME.setter
    def VNAME(self, value: list[str]):
        self._VNAME, self.NV = value, len(value)
        self.NLHEAD = 14 + self.NSCOML + self.NNCOML

    @property
    def X(self) -> list[str]:
        """Independent variable"""
        return self._X

    @X.setter
    def X(self, xarr: list[str]):
        self._X = xarr
        # calculate dx as unique diffs in X,
        # unique with floats might fail, so add a round to 4 decimals:
        dx = np.unique(np.diff(np.array(xarr, dtype=float)).round(4))
        # let dx be 0 if there's more than one unique diff
        dx = dx[0] if dx.size == 1 else 0
        # use an integer if dx is close to its integer value, else float:
        dx = int(dx) if np.isclose(dx, int(dx)) else dx
        self.DX = dx

    @property
    def V(self) -> list[list[str],]:
        """Dependent variable"""
        return self._V

    @V.setter
    def V(self, vlists: list[list[str],]):
        # assert (
        #     len(vlists) == self.NV
        # ), f"try to set {len(vlists)} dependent variables, but VNAMES specify {self.NV}"
        self._V = vlists

    # ------------------------------------------------------------------------------
    def __from_file(self, file: Union[str, Path], **kwargs):
        """Load NASA Ames 1001 from text file."""
        nadict = na1001_cls_read(file, **kwargs)
        for k in KEYS:
            setattr(self, k, nadict[k])

    # ------------------------------------------------------------------------------
    def to_file(self, file: Union[str, Path], **kwargs):
        """
        Write NASA Ames 1001 file from populated ffi_1001 class.

        Parameters
        ----------
        file : str or pathlib.Path
            filepath and -name of the destination.
        sep : str, optional
            General delimiter. The default is " ".
        sep_data : str, optional
            Delimiter to separate data columns. The default is "\t".
        overwrite : int, optional
            Set to 1 to overwrite existing files. The default is 0 (no overwrite).
        verbose : bool, optional
            Verbose print output if True. The default is False.

        Returns
        -------
        int
            0 -> failed, 1 -> successful write, 2 -> successful overwrite.

        """
        io = na1001_cls_write(file, self.__dict__, **kwargs)
        return io

    # ------------------------------------------------------------------------------
    def __repr__(self) -> str:
        s = f"NASA Ames {self.FFI}\n---\n"
        s += "".join(
            [
                f"{k.strip('_')} : {self.__dict__[k]}\n"
                for k in (
                    "_SRC",
                    "NLHEAD",
                    "ONAME",
                    "ORG",
                    "SNAME",
                    "MNAME",
                    "IVOL",
                    "NVOL",
                    "DATE",
                    "RDATE",
                    "DX",
                    "XNAME",
                    "NV",
                    "VSCAL",
                    "VMISS",
                    "_VNAME",
                    "NSCOML",
                    "_SCOM",
                    "NNCOML",
                    "_NCOM",
                )
            ]
        )
        return s

    def __str__(self) -> str:
        s = "NASA Ames 1001\n"
        s += f"SRC: {self._SRC}\n---\n"
        s += "\n".join(f"{k}: {getattr(self, k)}" for k in ["ONAME", "ORG", "SNAME"])
        s += "\n" + ", ".join(f"{k}: {getattr(self, k)}" for k in ["DATE", "RDATE"])
        return s


###############################################################################

KEYS = [
    "NLHEAD",
    "ONAME",
    "ORG",
    "SNAME",
    "MNAME",
    "IVOL",
    "NVOL",
    "DATE",
    "RDATE",
    "DX",
    "XNAME",
    "NV",
    "VSCAL",
    "VMISS",
    "_VNAME",
    "NSCOML",
    "_SCOM",
    "NNCOML",
    "_NCOM",
    "_X",
    "_V",
    "_SRC",
    "_HEADER",
]


def na1001_cls_read(
    file,
    sep=" ",
    sep_data="\t",
    auto_nncoml=True,
    strip_lines=True,
    rmv_repeated_seps=False,
    vscale_vmiss_vertical=False,
    vmiss_to_None=False,
    ensure_ascii=True,
    allow_emtpy_data=False,
):
    """
    Read NASA Ames 1001 formatted text file. Expected encoding is ASCII.

    See class method for detailled docstring.
    """
    na_1001 = {}
    if hasattr(file, "read"):  # if it has a read method, assume buffered IO
        na_1001["_SRC"] = "BaseIO"
        data = file.read()
        if not isinstance(data, bytes):
            data = bytes(data, "utf-8")
    else:
        file = Path(file)
        na_1001["_SRC"] = file.as_posix()
        with open(file, "rb") as f:
            data = f.read()

    # by definition, NASA Ames 1001 is pure ASCII. the following lines allow
    # to read files with other encodings; use with caution
    encodings = ("ascii",) if ensure_ascii else ("ascii", "utf-8", "cp1252", "latin-1")

    decoded = False
    for enc in encodings:
        try:
            decoded = data.decode(enc)
        except ValueError:  # invalid encoding, try next
            pass
        else:
            if enc != "ascii":
                print(f"warning: non-ascii encoding '{enc}' used in file {na_1001['SRC']}")
            break  # found a working encoding
    if not decoded:
        raise ValueError(f"could not decode input (ASCII-only: {ensure_ascii})")

    file_content = decoded.split("\n")

    if strip_lines:
        for i, line in enumerate(file_content):
            file_content[i] = line.strip()

    if rmv_repeated_seps:
        for i, line in enumerate(file_content):
            while sep + sep in line:
                line = line.replace(sep + sep, sep)
            file_content[i] = line

    tmp = list(map(int, file_content[0].split()))
    assert len(tmp) == 2, f"invalid format in line 1: '{file_content[0]}'"
    assert tmp[0] >= 15, f"NASA Ames FFI 1001 has a least 15 header lines (specified: {tmp[0]})"
    assert tmp[1] == 1001, f"reader is for FFI 1001 only, got {tmp[1]}"

    nlhead = tmp[0]
    na_1001["NLHEAD"] = nlhead

    header = file_content[:nlhead]
    data = file_content[nlhead:]
    if all(x == "" for x in data) or data == ["\n"]:
        data = None

    if not allow_emtpy_data:
        assert data, "no data found."

    na_1001["ONAME"] = header[1]
    na_1001["ORG"] = header[2]
    na_1001["SNAME"] = header[3]
    na_1001["MNAME"] = header[4]

    tmp = list(map(int, header[5].split()))
    assert len(tmp) == 2, f"invalid format in line 6: '{header[5]}'"
    na_1001["IVOL"], na_1001["NVOL"] = tmp[0], tmp[1]

    tmp = list(map(int, header[6].split()))
    assert len(tmp) == 6, f"invalid format line 7: '{header[6]}'"

    # check for valid date in line 7 (yyyy mm dd)
    assert date(*tmp[:3]) <= date(
        *tmp[3:6]
    ), f"RDATE must be greater or equal to DATE, have DATE {date(*tmp[:3])}, RDATE {date(*tmp[3:6])}"
    na_1001["DATE"], na_1001["RDATE"] = tmp[:3], tmp[3:6]

    # DX check if the line contains a decimal separator; if so use float else int
    na_1001["DX"] = float(header[7]) if "." in header[7] else int(header[7])
    na_1001["XNAME"] = header[8]  # .rsplit(sep=sep_com)

    n_vars = int(header[9])
    na_1001["NV"] = n_vars

    if vscale_vmiss_vertical:
        offset = n_vars * 2
        na_1001["VSCAL"] = header[10 : 10 + n_vars]
        na_1001["VMISS"] = header[10 + n_vars : 10 + n_vars * 2]
    else:
        offset = 2
        na_1001["VSCAL"] = header[10].split()
        na_1001["VMISS"] = header[11].split()

    assert (
        len(na_1001["VSCAL"]) == na_1001["NV"]
    ), f"number of elements in VSCAL (have: {len(na_1001['VSCAL'])}) must match number of variables specified ({na_1001['NV']})"
    assert (
        len(na_1001["VMISS"]) == na_1001["NV"]
    ), f"number of elements in VMISS (have: {len(na_1001['VMISS'])}) must match number of variables specified ({na_1001['NV']})"
    assert (
        n_vars == len(na_1001["VSCAL"]) == len(na_1001["VMISS"])
    ), "VSCAL, VMISS and NV must have equal number of elements"

    na_1001["_VNAME"] = header[10 + offset : 10 + n_vars + offset]

    nscoml = int(header[10 + n_vars + offset])
    na_1001["NSCOML"] = nscoml
    if nscoml > 0:  # read special comment if nscoml>0
        na_1001["_SCOM"] = header[n_vars + 11 + offset : n_vars + nscoml + 11 + offset]
    else:
        na_1001["_SCOM"] = ""

    msg = "nscoml not equal n elements in list na_1001['_SCOM']"
    assert nscoml == len(na_1001["_SCOM"]), msg

    # read normal comment if nncoml>0
    if auto_nncoml is True:
        nncoml = nlhead - (n_vars + nscoml + 12 + offset)
    else:
        nncoml = int(header[n_vars + nscoml + 11 + offset])
    na_1001["NNCOML"] = nncoml

    if nncoml > 0:
        na_1001["_NCOM"] = header[
            n_vars + nscoml + 12 + offset : n_vars + nscoml + nncoml + 12 + offset
        ]
    else:
        na_1001["_NCOM"] = ""

    msg = "nncoml not equal n elements in list na_1001['_NCOM']"
    assert nncoml == len(na_1001["_NCOM"]), msg

    msg = "nlhead must be equal to nncoml + nscoml + n_vars + 14"
    assert nncoml + nscoml + n_vars + 14 == nlhead, msg

    # done with header, we can set HEADER variable now
    na_1001["_HEADER"] = header

    # continue with variables
    na_1001["_X"] = []  # holds independent variable
    na_1001["_V"] = [[] for _ in range(n_vars)]  # list for each dependent variable

    if data is not None:
        for ix, line in enumerate(data):
            if line == "" or line == "\n":  # skip empty lines or trailing newline
                continue

            parts = line.rsplit(sep=sep_data)
            assert (
                len(parts) == n_vars + 1
            ), f"invalid number of parameters in line {ix+nlhead+1}, have {len(parts)} ({parts}), want {n_vars+1}"

            na_1001["_X"].append(parts[0].strip())
            if vmiss_to_None:
                for j in range(n_vars):
                    na_1001["_V"][j].append(
                        parts[j + 1].strip()
                        if parts[j + 1].strip() != na_1001["VMISS"][j]
                        else None
                    )
            else:
                for j in range(n_vars):
                    na_1001["_V"][j].append(parts[j + 1].strip())

    return na_1001


###############################################################################


def na1001_cls_write(
    file_path,
    na_1001,
    sep=" ",
    sep_data="\t",
    overwrite=0,
    verbose=False,
):
    """
    Write content of na1001 class instance to file in NASA Ames 1001 format. Encoding is ASCII.

    See class method for detailled docstring.
    """
    verboseprint = print if verbose else lambda *a, **k: None

    # check if directory exists, create if not.
    if not os.path.isdir(os.path.dirname(file_path)):
        os.mkdir(os.path.dirname(file_path))

    # check if file exists, act according to overwrite keyword
    if os.path.isfile(file_path):
        if not overwrite:
            verboseprint(
                f"write failed: {file_path} already exists.\n" "set overwrite keyword to overwrite."
            )
            return 0  # write failed / forbidden
        write = 2  # overwriting
    write = 1  # normal writing

    # check n variables and comment lines; adjust values if incorrect
    n_vars_named = len(na_1001["_VNAME"])
    n_vars_data = len(na_1001["_V"])
    if n_vars_named != n_vars_data:
        raise ValueError(
            "NA error: n vars in V and VNAME not equal, " f"{n_vars_data} vs. {n_vars_named}!"
        )

    if n_vars_named - na_1001["NV"] != 0:
        verboseprint("NA output: NV corrected")
        na_1001["NV"] = n_vars_named

    nscoml_is = len(na_1001["_SCOM"])
    if (nscoml_is - na_1001["NSCOML"]) != 0:
        verboseprint("NA output: NSCOML corrected")
        na_1001["NSCOML"] = nscoml_is

    nncoml_is = len(na_1001["_NCOM"])
    if (nncoml_is - na_1001["NNCOML"]) != 0:
        verboseprint("NA output: NNCOML corrected")
        na_1001["NNCOML"] = nncoml_is

    nlhead_is = 14 + n_vars_named + nscoml_is + nncoml_is
    if (nlhead_is - na_1001["NLHEAD"]) != 0:
        verboseprint("NA output: NLHEAD corrected")
        na_1001["NLHEAD"] = nlhead_is

    # begin the actual writing process
    with open(file_path, "w", encoding="ascii") as file_obj:
        block = str(na_1001["NLHEAD"]) + sep + "1001\n"
        file_obj.write(block)

        block = str(na_1001["ONAME"]) + "\n"
        file_obj.write(block)

        block = str(na_1001["ORG"]) + "\n"
        file_obj.write(block)

        block = str(na_1001["SNAME"]) + "\n"
        file_obj.write(block)

        block = str(na_1001["MNAME"]) + "\n"
        file_obj.write(block)

        block = str(na_1001["IVOL"]) + sep + str(na_1001["NVOL"]) + "\n"
        file_obj.write(block)

        # dates: assume "yyyy m d" in tuple
        block = (
            "%4.4u" % na_1001["DATE"][0]
            + sep
            + "%2.2u" % na_1001["DATE"][1]
            + sep
            + "%2.2u" % na_1001["DATE"][2]
            + sep
            + "%4.4u" % na_1001["RDATE"][0]
            + sep
            + "%2.2u" % na_1001["RDATE"][1]
            + sep
            + "%2.2u" % na_1001["RDATE"][2]
            + "\n"
        )
        file_obj.write(block)

        file_obj.write(f"{na_1001['DX']}" + "\n")

        # obsolete: CARIBIC
        # file_obj.write(sep_com.join(na_1001["XNAME"]) + "\n")
        file_obj.write(na_1001["XNAME"] + "\n")

        n_vars = na_1001["NV"]  # get number of variables
        block = str(n_vars) + "\n"
        file_obj.write(block)

        line = ""
        for i in range(n_vars):
            line += str(na_1001["VSCAL"][i]) + sep
        line = line[0:-1] if line.endswith("\n") else line[0:-1] + "\n"
        file_obj.write(line)

        line = ""
        for i in range(n_vars):
            line += str(na_1001["VMISS"][i]) + sep
        line = line[0:-1] if line.endswith("\n") else line[0:-1] + "\n"
        file_obj.write(line)

        block = na_1001["_VNAME"]
        for i in range(n_vars):
            file_obj.write(block[i] + "\n")

        nscoml = na_1001["NSCOML"]  # get number of special comment lines
        line = str(nscoml) + "\n"
        file_obj.write(line)

        block = na_1001["_SCOM"]
        for i in range(nscoml):
            file_obj.write(block[i] + "\n")

        nncoml = na_1001["NNCOML"]  # get number of normal comment lines
        line = str(nncoml) + "\n"
        file_obj.write(line)

        block = na_1001["_NCOM"]
        for i in range(nncoml):
            file_obj.write(block[i] + "\n")

        for i, x in enumerate(na_1001["_X"]):
            line = str(x) + sep_data
            for j in range(n_vars):
                line += str(na_1001["_V"][j][i]) + sep_data
            file_obj.write(line[0:-1] + "\n")

    return write


###############################################################################
