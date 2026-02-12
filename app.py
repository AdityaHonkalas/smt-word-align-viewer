import os
from io import BytesIO
from flask import Flask, render_template, request, send_file

from smt.config import AppConfig
from smt.engine import SMTTranslator


LANGUAGE_LABELS = {
    "hi": "Hindi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
}


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev"))

    cfg = AppConfig.from_env()
    translator = SMTTranslator(cfg)
    target_languages = list(cfg.target_languages)
    if cfg.default_target_language not in target_languages:
        target_languages.insert(0, cfg.default_target_language)

    language_options = [
        {"code": code, "label": LANGUAGE_LABELS.get(code, code.upper())}
        for code in target_languages
    ]
    label_by_code = {item["code"]: item["label"] for item in language_options}

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            source_text="",
            selected_target_language=cfg.default_target_language,
            selected_target_language_label=label_by_code.get(
                cfg.default_target_language, cfg.default_target_language.upper()
            ),
            target_languages=language_options,
            result=None,
            error=None,
        )

    @app.post("/translate")
    def translate():
        source_text = request.form.get("source_text", "").strip()
        target_language = request.form.get("target_language", cfg.default_target_language).strip().lower()

        if target_language not in {l["code"] for l in language_options}:
            target_language = cfg.default_target_language

        if not source_text:
            return render_template(
                "index.html",
                source_text="",
                selected_target_language=target_language,
                selected_target_language_label=label_by_code.get(
                    target_language, target_language.upper()
                ),
                target_languages=language_options,
                result=None,
                error="Enter a sentence to translate.",
            )

        try:
            result = translator.translate_with_alignment(source_text, target_language)
            return render_template(
                "index.html",
                source_text=source_text,
                selected_target_language=target_language,
                selected_target_language_label=label_by_code.get(
                    target_language, target_language.upper()
                ),
                target_languages=language_options,
                result=result,
                error=None,
            )
        except Exception as exc:
            return render_template(
                "index.html",
                source_text=source_text,
                selected_target_language=target_language,
                selected_target_language_label=label_by_code.get(
                    target_language, target_language.upper()
                ),
                target_languages=language_options,
                result=None,
                error=f"Translation failed: {exc}",
            )

    @app.post("/download")
    def download_translation():
        translated_text = request.form.get("translated_text", "").strip()
        target_language = request.form.get("target_language", cfg.default_target_language).strip().lower()
        if not translated_text:
            translated_text = "No translated text available."
        payload = translated_text.encode("utf-8")
        filename = f"translation_{target_language}.txt"
        return send_file(
            BytesIO(payload),
            as_attachment=True,
            download_name=filename,
            mimetype="text/plain; charset=utf-8",
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
