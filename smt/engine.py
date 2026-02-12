from __future__ import annotations

from dataclasses import asdict
from typing import List

from .alignment import TranslationResult, matrix_for_viewer, positional_align
from .config import AppConfig
from .library_translate import LibrarySentenceTranslator
from .tokenize import tokenize


class SMTTranslator:
    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        self.supported_languages = set(cfg.target_languages)
        self.library_translator = LibrarySentenceTranslator(cfg.source_language)

    def translate_with_alignment(self, source_text: str, target_language: str | None = None) -> dict:
        lang = (target_language or self.cfg.default_target_language).lower()
        if self.supported_languages and lang not in self.supported_languages:
            raise ValueError(f"Unsupported target language: {lang}")

        source_tokens = tokenize(source_text)
        translated_sentence = self.library_translator.translate(source_text, lang)
        target_tokens: List[str] = tokenize(translated_sentence)
        alignments = positional_align(source_tokens, target_tokens)

        result = TranslationResult(
            source_tokens=source_tokens,
            target_tokens=target_tokens,
            target_text=translated_sentence,
            alignments=alignments,
            backend=self.library_translator.backend,
        )

        payload = asdict(result)
        payload["alignment_grid"] = matrix_for_viewer(
            result.source_tokens,
            result.target_tokens,
            result.alignments,
        )
        payload["alignment_pairs"] = [
            {
                "source_word": result.source_tokens[p.src_index],
                "target_word": result.target_tokens[p.tgt_index],
                "source_index": p.src_index,
                "target_index": p.tgt_index,
            }
            for p in result.alignments
            if p.src_index < len(result.source_tokens) and p.tgt_index < len(result.target_tokens)
        ]
        payload["target_language"] = lang
        payload["giza_alignment"] = " ".join(f"{p.src_index}-{p.tgt_index}" for p in result.alignments)
        return payload
