from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    data_dir: Path
    phrase_table_path: Path
    lexicon_path: Path
    target_languages: tuple[str, ...]
    default_target_language: str
    source_language: str
    use_dynamic_corpus: bool
    corpus_backend: str
    corpus_max_sentences: int
    moses_path: str | None
    fast_align_path: str | None
    atools_path: str | None
    giza_root: str | None

    @staticmethod
    def from_env() -> "AppConfig":
        data_dir = Path(os.environ.get("SMT_DATA_DIR", "data")).resolve()
        phrase_table = Path(
            os.environ.get("SMT_PHRASE_TABLE", str(data_dir / "models" / "phrase_table.tsv"))
        )
        lexicon = Path(os.environ.get("SMT_LEXICON", str(data_dir / "models" / "lexicon.tsv")))
        langs = tuple(
            l.strip().lower()
            for l in os.environ.get("SMT_TARGET_LANGUAGES", "hi,bn,ta,te,mr,gu").split(",")
            if l.strip()
        )
        default_lang = os.environ.get("SMT_DEFAULT_TARGET_LANGUAGE", langs[0] if langs else "hi").strip().lower()
        source_language = os.environ.get("SMT_SOURCE_LANGUAGE", "en").strip().lower()
        use_dynamic_corpus = os.environ.get("SMT_USE_DYNAMIC_CORPUS", "0").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        corpus_backend = os.environ.get("SMT_CORPUS_BACKEND", "hf_opus100").strip().lower()
        corpus_max_sentences = int(os.environ.get("SMT_CORPUS_MAX_SENTENCES", "2000"))

        return AppConfig(
            data_dir=data_dir,
            phrase_table_path=phrase_table,
            lexicon_path=lexicon,
            target_languages=langs or ("hi",),
            default_target_language=default_lang,
            source_language=source_language,
            use_dynamic_corpus=use_dynamic_corpus,
            corpus_backend=corpus_backend,
            corpus_max_sentences=corpus_max_sentences,
            moses_path=os.environ.get("MOSES_BIN"),
            fast_align_path=os.environ.get("FAST_ALIGN_BIN"),
            atools_path=os.environ.get("ATOOLS_BIN"),
            giza_root=os.environ.get("GIZA_ROOT"),
        )

    def phrase_table_for(self, target_language: str) -> Path:
        candidate = self.data_dir / "models" / f"phrase_table.{target_language}.tsv"
        return candidate if candidate.exists() else self.phrase_table_path

    def lexicon_for(self, target_language: str) -> Path:
        candidate = self.data_dir / "models" / f"lexicon.{target_language}.tsv"
        return candidate if candidate.exists() else self.lexicon_path

    def moses_ini_for(self, target_language: str) -> Path:
        candidate = self.data_dir / "models" / f"moses.{target_language}.ini"
        if candidate.exists():
            return candidate
        return self.data_dir / "models" / "moses.ini"

    def generated_phrase_table_for(self, target_language: str) -> Path:
        return self.data_dir / "models" / "generated" / f"phrase_table.{target_language}.tsv"

    def generated_lexicon_for(self, target_language: str) -> Path:
        return self.data_dir / "models" / "generated" / f"lexicon.{target_language}.tsv"
