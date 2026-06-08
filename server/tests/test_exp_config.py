from services.exp_config import exp_progress, level_for_exp


def test_level_for_exp_starts_at_apprentice():
    level, title = level_for_exp(0)
    assert level == 1
    assert title == "见习炼金师"


def test_level_for_exp_reaches_level_two():
    level, title = level_for_exp(30)
    assert level == 2
    assert title == "初级炼金师"


def test_exp_progress_for_new_user():
    current, required, _ = exp_progress(0)
    assert current == 0
    assert required == 30
