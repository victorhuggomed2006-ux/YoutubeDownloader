"""Language selection.

This is the one test that touches ``gui``. It imports QtCore only, so it needs
no display: nothing here creates a widget.
"""

from __future__ import annotations

from ytdownloader.gui.i18n import LANGUAGES, effective_language, match_language


def test_an_explicit_preference_wins_over_the_system() -> None:
    assert effective_language("es") == "es"
    assert effective_language("pt_BR") == "pt_BR"
    assert effective_language("en") == "en"


def test_auto_resolves_to_one_of_the_catalogues() -> None:
    assert effective_language("auto") in {"en", "pt_BR", "es"}


def test_an_unknown_preference_falls_back_instead_of_breaking() -> None:
    assert effective_language("klingon") in {"en", "pt_BR", "es"}


def test_windows_ranks_the_display_language_first() -> None:
    """The regional format setting can differ from the display language."""
    assert match_language(["pt-Latn-BR", "pt-BR", "en-US", "en"]) == "pt_BR"


def test_a_script_subtag_does_not_hide_the_language() -> None:
    assert match_language(["es-419"]) == "es"
    assert match_language(["pt_BR"]) == "pt_BR"


def test_a_language_without_a_catalogue_falls_through_to_the_next() -> None:
    assert match_language(["fr-FR", "es-ES"]) == "es"


def test_english_is_the_last_resort() -> None:
    assert match_language(["fr-FR", "de-DE"]) == "en"
    assert match_language([]) == "en"


def test_every_offered_language_resolves_to_itself() -> None:
    for code in LANGUAGES:
        if code == "auto":
            continue
        assert effective_language(code) == code
