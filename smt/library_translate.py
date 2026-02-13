from __future__ import annotations


class LibraryTranslationError(RuntimeError):
    pass


class LibrarySentenceTranslator:
    def __init__(self, source_language: str) -> None:
        self.source_language = source_language
        self.backend = "google-translator"

    def translate(self, sentence: str, target_language: str) -> str:
        try:
            from deep_translator import GoogleTranslator  # type: ignore
        except Exception as exc:
            raise LibraryTranslationError(
                "deep-translator is not available. Install dependencies from requirements.txt."
            ) from exc

        try:
            translated = GoogleTranslator(source=self.source_language, target=target_language).translate(sentence)
            translated = (translated or "").strip()
            if translated:
                self.backend = "google-translator"
                return translated
        except Exception as exc:
            raise LibraryTranslationError(
                "Google translation failed. Verify language codes and internet connectivity."
            ) from exc

        raise LibraryTranslationError("Google translation returned empty output.")
