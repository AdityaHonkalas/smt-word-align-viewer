from __future__ import annotations

import re
from typing import List

_TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall(text.strip())


def detokenize(tokens: List[str]) -> str:
    out: List[str] = []
    no_space_before = {".", ",", "!", "?", ":", ";", ")", "]", "}"}
    no_space_after = {"(", "[", "{"}

    for tok in tokens:
        if not out:
            out.append(tok)
            continue

        prev = out[-1]
        if tok in no_space_before or prev in no_space_after:
            out[-1] = prev + tok
        else:
            out.append(" " + tok)

    return "".join(out)
