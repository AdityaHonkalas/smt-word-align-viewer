from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import List


class ToolkitError(RuntimeError):
    pass


def run_command(cmd: List[str], cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        rendered = " ".join(shlex.quote(c) for c in cmd)
        raise ToolkitError(
            f"Command failed ({proc.returncode}): {rendered}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc


def moses_decode(moses_bin: str, moses_ini: str, sentence: str) -> str:
    cmd = [moses_bin, "-f", moses_ini]
    proc = subprocess.run(cmd, input=sentence + "\n", capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise ToolkitError(proc.stderr.strip() or "Moses decode failed")
    lines = proc.stdout.strip().splitlines()
    return lines[0].strip() if lines else ""


def fast_align_bidirectional(
    fast_align_bin: str,
    atools_bin: str,
    parallel_corpus: Path,
    out_forward: Path,
    out_reverse: Path,
    out_sym: Path,
) -> None:
    with out_forward.open("w", encoding="utf-8") as fwd:
        proc = subprocess.run(
            [fast_align_bin, "-i", str(parallel_corpus), "-d", "-o", "-v"],
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            raise ToolkitError(proc.stderr.strip() or "fast_align forward failed")
        fwd.write(proc.stdout)

    with out_reverse.open("w", encoding="utf-8") as rev:
        proc = subprocess.run(
            [fast_align_bin, "-i", str(parallel_corpus), "-d", "-o", "-v", "-r"],
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            raise ToolkitError(proc.stderr.strip() or "fast_align reverse failed")
        rev.write(proc.stdout)

    with out_sym.open("w", encoding="utf-8") as sym:
        proc = subprocess.run(
            [
                atools_bin,
                "-i",
                str(out_forward),
                "-j",
                str(out_reverse),
                "-c",
                "grow-diag-final-and",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            raise ToolkitError(proc.stderr.strip() or "atools symmetrization failed")
        sym.write(proc.stdout)
