def test_stats_keys(client):
    r = client.get("/v1/stats")
    assert r.status_code == 200
    d = r.json()
    assert "total_requests" in d
    assert "active_requests" in d
    assert "latency_ms" in d
    assert "callers" in d
    assert "backend_health" in d


def test_stats_increment(client):
    before = client.get("/v1/stats").json()["total_requests"]
    client.post(
        "/v1/chat/completions",
        json={"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "hi"}]},
    )
    after = client.get("/v1/stats").json()["total_requests"]
    assert after == before + 1


def test_stats_callers(client):
    client.post(
        "/v1/chat/completions",
        json={"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "hi"}]},
    )
    d = client.get("/v1/stats").json()
    assert isinstance(d["callers"], dict)
    assert len(d["callers"]) > 0


def test_stats_active_requests_returns_to_zero(client):
    client.post(
        "/v1/chat/completions",
        json={"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "hi"}]},
    )
    d = client.get("/v1/stats").json()
    assert d["active_requests"] == 0


def test_stats_latency_null_initially():
    from gateway.stats import StatsStore
    store = StatsStore()
    pct = store.compute_percentiles()
    assert pct["p50"] is None
    assert pct["p95"] is None
    assert pct["p99"] is None
