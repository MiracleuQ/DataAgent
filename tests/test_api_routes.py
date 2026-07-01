from app.api import routes


def test_get_system_creates_fresh_instances(monkeypatch):
    created = []

    def fake_create_system():
        system = (object(), object())
        created.append(system)
        return system

    if hasattr(routes, "_system_cache"):
        routes._system_cache = None
    monkeypatch.setattr(routes, "create_system", fake_create_system)

    first = routes.get_system()
    second = routes.get_system()

    assert first is not second
    assert created == [first, second]
