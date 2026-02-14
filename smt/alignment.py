from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

from .tokenize import is_punctuation


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


def _init_translation_table(
    source_tokens: List[str],
    target_tokens: List[str],
) -> Dict[Tuple[int, int], float]:
    src_n = max(1, len(source_tokens))
    tgt_n = max(1, len(target_tokens))
    table: Dict[Tuple[int, int], float] = {}

    for si, s_tok in enumerate(source_tokens):
        for ti, t_tok in enumerate(target_tokens):
            pos_src = (si + 1) / (src_n + 1)
            pos_tgt = (ti + 1) / (tgt_n + 1)
            pos_prior = math.exp(-8.0 * abs(pos_src - pos_tgt))
            punct_match = 1.0
            if is_punctuation(s_tok) or is_punctuation(t_tok):
                punct_match = 4.0 if s_tok == t_tok else 0.05
            table[(si, ti)] = (0.15 + pos_prior) * punct_match
    return table


def em_word_align(
    source_tokens: List[str],
    target_tokens: List[str],
    iterations: int = 8,
) -> List[AlignmentPoint]:
    if not source_tokens or not target_tokens:
        return []

    table = _init_translation_table(source_tokens, target_tokens)

    for _ in range(max(1, iterations)):
        count: Dict[Tuple[int, int], float] = defaultdict(float)
        total_s: Dict[int, float] = defaultdict(float)
        total_t: Dict[int, float] = defaultdict(float)

        for ti in range(len(target_tokens)):
            z = 0.0
            for si in range(len(source_tokens)):
                z += table[(si, ti)]
            if z <= 0.0:
                continue
            for si in range(len(source_tokens)):
                posterior = table[(si, ti)] / z
                count[(si, ti)] += posterior
                total_s[si] += posterior
                total_t[ti] += posterior

        # Agreement-style update: source-normalized * target-normalized.
        for si in range(len(source_tokens)):
            for ti in range(len(target_tokens)):
                p_t_given_s = count[(si, ti)] / total_s[si] if total_s[si] > 0 else 0.0
                p_s_given_t = count[(si, ti)] / total_t[ti] if total_t[ti] > 0 else 0.0
                table[(si, ti)] = max(1e-12, p_t_given_s * p_s_given_t)

    raw_links: Set[Tuple[int, int]] = set()
    for si, s_tok in enumerate(source_tokens):
        # Enforce punctuation-only matching.
        punct_targets = [ti for ti, t_tok in enumerate(target_tokens) if is_punctuation(t_tok)]
        non_punct_targets = [ti for ti, t_tok in enumerate(target_tokens) if not is_punctuation(t_tok)]
        candidates = punct_targets if is_punctuation(s_tok) else non_punct_targets
        if not candidates:
            continue

        best_ti = max(candidates, key=lambda ti: table[(si, ti)])
        best_score = table[(si, best_ti)]
        raw_links.add((si, best_ti))

        # Keep strong secondary links for one-to-many mappings.
        for ti in candidates:
            if ti == best_ti:
                continue
            score = table[(si, ti)]
            if best_score > 0 and score / best_score >= 0.92:
                raw_links.add((si, ti))

    # Ensure punctuation marks with exact match are linked when possible.
    used_targets = {ti for _, ti in raw_links}
    for si, s_tok in enumerate(source_tokens):
        if not is_punctuation(s_tok):
            continue
        exact = [ti for ti, t_tok in enumerate(target_tokens) if t_tok == s_tok and ti not in used_targets]
        if exact:
            closest = min(exact, key=lambda ti: abs(ti - si))
            raw_links.add((si, closest))
            used_targets.add(closest)

    return [AlignmentPoint(src_index=si, tgt_index=ti) for si, ti in sorted(raw_links)]


def extract_phrase_pairs(
    source_tokens: List[str],
    target_tokens: List[str],
    points: List[AlignmentPoint],
    max_phrase_len: int = 4,
) -> List[dict]:
    if not source_tokens or not target_tokens or not points:
        return []

    aligned_s_to_t: Dict[int, Set[int]] = defaultdict(set)
    aligned_t_to_s: Dict[int, Set[int]] = defaultdict(set)
    for p in points:
        aligned_s_to_t[p.src_index].add(p.tgt_index)
        aligned_t_to_s[p.tgt_index].add(p.src_index)

    phrases: List[dict] = []
    seen: Set[Tuple[int, int, int, int]] = set()
    src_len = len(source_tokens)

    for s_start in range(src_len):
        for s_end in range(s_start, min(src_len, s_start + max_phrase_len)):
            tgt_positions = [
                t
                for s in range(s_start, s_end + 1)
                for t in aligned_s_to_t.get(s, set())
            ]
            if not tgt_positions:
                continue

            t_start = min(tgt_positions)
            t_end = max(tgt_positions)

            # Consistency: no target token in range aligns to source outside source span.
            consistent = True
            for t in range(t_start, t_end + 1):
                for s in aligned_t_to_s.get(t, set()):
                    if s < s_start or s > s_end:
                        consistent = False
                        break
                if not consistent:
                    break
            if not consistent:
                continue

            if (t_end - t_start + 1) > max_phrase_len:
                continue

            key = (s_start, s_end, t_start, t_end)
            if key in seen:
                continue
            seen.add(key)
            phrases.append(
                {
                    "source_phrase": " ".join(source_tokens[s_start : s_end + 1]),
                    "target_phrase": " ".join(target_tokens[t_start : t_end + 1]),
                    "source_span": f"{s_start}-{s_end}",
                    "target_span": f"{t_start}-{t_end}",
                    "source_start": s_start,
                    "source_end": s_end,
                    "target_start": t_start,
                    "target_end": t_end,
                }
            )

    return phrases


def phrase_based_projection(
    source_tokens: List[str],
    target_tokens: List[str],
    points: List[AlignmentPoint],
    phrase_pairs: List[dict],
) -> str:
    if not source_tokens or not target_tokens:
        return ""

    by_source_start: Dict[int, List[dict]] = defaultdict(list)
    for p in phrase_pairs:
        by_source_start[p["source_start"]].append(p)
    for start in by_source_start:
        by_source_start[start].sort(
            key=lambda p: (
                -(p["source_end"] - p["source_start"]),
                p["target_start"],
            )
        )

    align_by_src: Dict[int, List[int]] = defaultdict(list)
    for ap in points:
        align_by_src[ap.src_index].append(ap.tgt_index)
    for si in align_by_src:
        align_by_src[si].sort()

    out_tokens: List[str] = []
    i = 0
    while i < len(source_tokens):
        chosen = None
        for candidate in by_source_start.get(i, []):
            if candidate["source_end"] < len(source_tokens):
                chosen = candidate
                break
        if chosen:
            out_tokens.extend(target_tokens[chosen["target_start"] : chosen["target_end"] + 1])
            i = chosen["source_end"] + 1
            continue

        tgt_ids = align_by_src.get(i, [])
        if tgt_ids:
            out_tokens.extend(target_tokens[t] for t in tgt_ids)
        i += 1

    # Deduplicate immediate repeats from many-to-one links.
    compact: List[str] = []
    for tok in out_tokens:
        if compact and compact[-1] == tok:
            continue
        compact.append(tok)
    return " ".join(compact).strip()
