from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class AlignmentPoint:
    src_index: int
    tgt_index: int


@dataclass
class TranslationResult:
    source_tokens: List[str]
    target_tokens: List[str]
    target_text: str
    alignments: List[AlignmentPoint]
    backend: str


def matrix_for_viewer(
    source_tokens: List[str],
    target_tokens: List[str],
    points: List[AlignmentPoint],
) -> List[List[bool]]:
    aligned = {(p.src_index, p.tgt_index) for p in points}
    return [
        [(si, ti) in aligned for ti in range(len(target_tokens))]
        for si in range(len(source_tokens))
    ]


def positional_align(source_tokens: List[str], target_tokens: List[str]) -> List[AlignmentPoint]:
    if not source_tokens or not target_tokens:
        return []
    if len(source_tokens) == 1:
        return [AlignmentPoint(src_index=0, tgt_index=0)]

    points: List[AlignmentPoint] = []
    for si in range(len(source_tokens)):
        ti = round(si * (len(target_tokens) - 1) / (len(source_tokens) - 1))
        points.append(AlignmentPoint(src_index=si, tgt_index=ti))
    return points
