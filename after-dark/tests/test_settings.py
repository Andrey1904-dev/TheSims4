from after_dark.core.settings import DEFAULT_SETTINGS, is_module_enabled, load_settings


def test_defaults_when_no_input():
    settings, warnings = load_settings(None)
    assert settings == DEFAULT_SETTINGS
    assert warnings == []


def test_invalid_values_fall_back_with_warning():
    settings, warnings = load_settings({
        "event_frequency": "sometimes",
        "flirt_cooldown_hours": "4",
        "max_flirts_per_day": 1000,
        "modules": {"reputation": "yes", "nightlife": True},
    })
    assert settings["event_frequency"] == DEFAULT_SETTINGS["event_frequency"]
    assert settings["flirt_cooldown_hours"] == DEFAULT_SETTINGS["flirt_cooldown_hours"]
    assert settings["max_flirts_per_day"] == DEFAULT_SETTINGS["max_flirts_per_day"]
    assert settings["modules"]["reputation"] is True
    assert len(warnings) == 5


def test_bool_is_not_accepted_as_int():
    settings, warnings = load_settings({"flirt_cooldown_hours": True})
    assert settings["flirt_cooldown_hours"] == DEFAULT_SETTINGS["flirt_cooldown_hours"]
    assert warnings


def test_non_dict_input_is_reported():
    settings, warnings = load_settings(["not", "a", "dict"])
    assert settings == DEFAULT_SETTINGS
    assert warnings


def test_master_switch_disables_adult_modules_but_not_core():
    settings, _ = load_settings({"adult_mechanics_enabled": False})
    assert is_module_enabled(settings, "core") is True
    assert is_module_enabled(settings, "sexuality") is False
    assert is_module_enabled(settings, "reputation") is False


def test_single_module_can_be_disabled():
    settings, _ = load_settings({"modules": {"reputation": False}})
    assert is_module_enabled(settings, "reputation") is False
    assert is_module_enabled(settings, "relationships") is True
