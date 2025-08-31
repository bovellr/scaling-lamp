from config.settings import AppSettings


def test_false_string_parsed_as_false():
    settings = AppSettings()
    settings.settings.setValue("matching/auto_match_high_confidence", "False")
    settings.load_settings()
    assert settings.auto_match_high_confidence is False