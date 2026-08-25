from app.services.access_control import allowed, best_role


def test_best_role_picks_highest():
    assert best_role(None, "viewer", "admin") == "admin"
    assert best_role("operator", "viewer") == "operator"
    assert best_role(None, None) is None


def test_allowed_rank():
    assert allowed("admin", "viewer")
    assert allowed("operator", "operator")
    assert not allowed("viewer", "operator")
    assert not allowed(None, "viewer")
