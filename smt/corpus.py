from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from .config import AppConfig
from .tokenize import tokenize


PhraseTable = Dict[Tuple[str, ...], List[str]]
Lexicon = Dict[Tuple[str, str], float]


class CorpusError(RuntimeError):
    pass


class DynamicCorpusBuilder:
    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg

    def _load_pairs_hf_opus100(self, target_language: str) -> list[tuple[str, str]]:
        try:
            from datasets import load_dataset
        except Exception as exc:
            raise CorpusError(
                "datasets package is required for dynamic corpus mode. Install dependencies from requirements.txt."
            ) from exc

        src = self.cfg.source_language
        tgt = target_language
        ds_name = "opus100"
        config_candidates = [f"{src}-{tgt}", f"{tgt}-{src}"]
        split = f"train[:{self.cfg.corpus_max_sentences}]"
        last_error: Exception | None = None

        for conf in config_candidates:
            try:
                ds = load_dataset(ds_name, conf, split=split)
                pairs: list[tuple[str, str]] = []
                for row in ds:
                    tr = row.get("translation", {})
                    s = str(tr.get(src, "")).strip()
                    t = str(tr.get(tgt, "")).strip()
                    if s and t:
                        pairs.append((s, t))
                if pairs:
                    return pairs
            except Exception as exc:  # pragma: no cover
                last_error = exc

        raise CorpusError(
            f"Unable to load OPUS-100 corpus for {src}->{tgt}. "
            f"Last error: {last_error}"
        )

    def _load_pairs(self, target_language: str) -> list[tuple[str, str]]:
        if self.cfg.corpus_backend == "hf_opus100":
            return self._load_pairs_hf_opus100(target_language)
        raise CorpusError(f"Unsupported corpus backend: {self.cfg.corpus_backend}")

    def build_artifacts(self, target_language: str) -> tuple[PhraseTable, Lexicon]:
        pairs = self._load_pairs(target_language)
        if not pairs:
            raise CorpusError("No sentence pairs returned by corpus backend.")

        word_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        phrase_counts: Dict[Tuple[str, ...], Dict[Tuple[str, ...], int]] = defaultdict(
            lambda: defaultdict(int)
        )

        for src_text, tgt_text in pairs:
            src_toks = tokenize(src_text.lower())
            tgt_toks = tokenize(tgt_text.lower())
            if not src_toks or not tgt_toks:
                continue

            if len(src_toks) == 1:
                mapping = [0]
            else:
                mapping = [
                    min(
                        round(i * (len(tgt_toks) - 1) / (len(src_toks) - 1)),
                        len(tgt_toks) - 1,
                    )
                    for i in range(len(src_toks))
                ]

            for si, s_tok in enumerate(src_toks):
                t_tok = tgt_toks[mapping[si]]
                word_counts[s_tok][t_tok] += 1

            for n in (2, 3):
                for i in range(0, len(src_toks) - n + 1):
                    s_phrase = tuple(src_toks[i : i + n])
                    start = mapping[i]
                    end = mapping[min(i + n - 1, len(mapping) - 1)]
                    lo = min(start, end)
                    hi = max(start, end)
                    if hi - lo + 1 != n:
                        continue
                    t_phrase = tuple(tgt_toks[lo : hi + 1])
                    if len(t_phrase) == n:
                        phrase_counts[s_phrase][t_phrase] += 1

        phrase_table: PhraseTable = {}
        for s_phrase, tgt_map in phrase_counts.items():
            if not tgt_map:
                continue
            best_t = max(tgt_map.items(), key=lambda x: x[1])[0]
            phrase_table[s_phrase] = list(best_t)

        for s_word, tgt_map in word_counts.items():
            best_t = max(tgt_map.items(), key=lambda x: x[1])[0]
            phrase_table[(s_word,)] = [best_t]

        lexicon: Lexicon = {}
        for s_word, tgt_map in word_counts.items():
            total = sum(tgt_map.values())
            if total == 0:
                continue
            for t_word, count in tgt_map.items():
                lexicon[(s_word, t_word)] = count / total

        return phrase_table, lexicon

    def persist_artifacts(self, target_language: str, phrase_table: PhraseTable, lexicon: Lexicon) -> None:
        phrase_path = self.cfg.generated_phrase_table_for(target_language)
        lex_path = self.cfg.generated_lexicon_for(target_language)
        phrase_path.parent.mkdir(parents=True, exist_ok=True)

        with phrase_path.open("w", encoding="utf-8") as f:
            f.write("# src_phrase<TAB>tgt_phrase\n")
            for s_toks, t_toks in sorted(phrase_table.items(), key=lambda x: (len(x[0]), x[0])):
                f.write(f"{' '.join(s_toks)}\t{' '.join(t_toks)}\n")

        with lex_path.open("w", encoding="utf-8") as f:
            f.write("# src_word<TAB>tgt_word<TAB>probability\n")
            for (s_word, t_word), prob in sorted(lexicon.items(), key=lambda x: (x[0][0], -x[1], x[0][1])):
                f.write(f"{s_word}\t{t_word}\t{prob:.6f}\n")
