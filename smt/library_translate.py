from __future__ import annotations


class LibraryTranslationError(RuntimeError):
    pass


class LibrarySentenceTranslator:
    def __init__(self, source_language: str) -> None:
        self.source_language = source_language
        self.backend = "unknown"

    def _polyglot_translate(self, sentence: str, target_language: str) -> str:
        from polyglot.text import Text  # type: ignore

        text = Text(sentence)
        # Polyglot versions differ in translate() signature.
        for call in (
            lambda: text.translate(target_language),
            lambda: text.translate(to_lang=target_language),
            lambda: text.translate(to_language=target_language),
        ):
            try:
                translated = call()
                return str(translated).strip()
            except TypeError:
                continue
        raise LibraryTranslationError("Polyglot is installed but translation method is unavailable.")

    def _deep_translator_translate(self, sentence: str, target_language: str) -> str:
        from deep_translator import GoogleTranslator  # type: ignore

        translator = GoogleTranslator(source=self.source_language, target=target_language)
        return translator.translate(sentence).strip()

    def translate(self, sentence: str, target_language: str) -> str:
        # Try Polyglot first as requested.
        try:
            translated = self._polyglot_translate(sentence, target_language)
            if translated:
                self.backend = "polyglot"
                return translated
        except Exception:
            pass

        # Fallback to another Python MT library when Polyglot is unavailable.
        try:
            translated = self._deep_translator_translate(sentence, target_language)
            if translated:
                self.backend = "deep-translator"
                return translated
        except Exception as exc:
            raise LibraryTranslationError(
                "Library translation failed. Install translation dependencies and ensure internet access "
                "for online translation backends."
            ) from exc

        raise LibraryTranslationError("Translation backend returned empty output.")
