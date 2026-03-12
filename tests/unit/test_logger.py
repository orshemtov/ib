from ib_client.logger import should_use_colors


def test_auto_color_uses_ci_signal() -> None:
    assert should_use_colors("auto", ci=False) is True
    assert should_use_colors("auto", ci=True) is False


def test_explicit_color_modes_override_ci() -> None:
    assert should_use_colors("true", ci=True) is True
    assert should_use_colors("false", ci=False) is False
