from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    data_dir: Path
    target_languages: tuple[str, ...]
    default_target_language: str
    source_language: str
    moses_path: str | None
    fast_align_path: str | None
    atools_path: str | None
    giza_root: str | None

    @staticmethod
    def from_env() -> "AppConfig":
        data_dir = Path(os.environ.get("SMT_DATA_DIR", "data")).resolve()
        langs = tuple(
            l.strip().lower()
            for l in os.environ.get("SMT_TARGET_LANGUAGES", "hi,bn,ta,te,mr,gu").split(",")
            if l.strip()
        )
        default_lang = os.environ.get("SMT_DEFAULT_TARGET_LANGUAGE", langs[0] if langs else "hi").strip().lower()
        source_language = os.environ.get("SMT_SOURCE_LANGUAGE", "en").strip().lower()

        return AppConfig(
            data_dir=data_dir,
            target_languages=langs or ("hi",),
            default_target_language=default_lang,
            source_language=source_language,
            moses_path=os.environ.get("MOSES_BIN"),
            fast_align_path=os.environ.get("FAST_ALIGN_BIN"),
            atools_path=os.environ.get("ATOOLS_BIN"),
            giza_root=os.environ.get("GIZA_ROOT"),
        )

    def moses_ini_for(self, target_language: str) -> Path:
        candidate = self.data_dir / "models" / f"moses.{target_language}.ini"
        if candidate.exists():
            return candidate
        return self.data_dir / "models" / "moses.ini"
