def test_list_models(client):
    r = client.get("/v1/models")
    assert r.status_code == 200
    d = r.json()
    assert d["object"] == "list"
    ids = [m["id"] for m in d["data"]]
    assert "gpt-3.5-turbo" in ids


def test_get_model(client):
    r = client.get("/v1/models/gpt-3.5-turbo")
    assert r.status_code == 200
    assert r.json()["id"] == "gpt-3.5-turbo"


def test_get_model_not_found(client):
    r = client.get("/v1/models/nonexistent-model")
    assert r.status_code == 404
