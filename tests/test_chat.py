import json

PAYLOAD = {
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello"}],
}


def test_non_streaming_shape(client):
    r = client.post("/v1/chat/completions", json={**PAYLOAD, "stream": False})
    assert r.status_code == 200
    d = r.json()
    assert d["object"] == "chat.completion"
    assert len(d["choices"]) == 1
    assert d["choices"][0]["message"]["role"] == "assistant"
    assert isinstance(d["choices"][0]["message"]["content"], str)
    assert "usage" in d


def test_non_streaming_invalid_body(client):
    r = client.post("/v1/chat/completions", json={"model": "x"})
    assert r.status_code == 422


def test_streaming_sse_format(client):
    r = client.post(
        "/v1/chat/completions",
        json={**PAYLOAD, "stream": True},
        headers={"Accept": "text/event-stream"},
    )
    assert r.status_code == 200
    assert "text/event-stream" in r.headers["content-type"]

    lines = [l for l in r.text.splitlines() if l.startswith("data: ")]
    assert lines[-1] == "data: [DONE]"

    chunks = [json.loads(l[len("data: "):]) for l in lines[:-1]]
    assert all(c["object"] == "chat.completion.chunk" for c in chunks)

    # first chunk must carry the role
    assert chunks[0]["choices"][0]["delta"].get("role") == "assistant"

    # last content chunk must have finish_reason="stop"
    last = chunks[-1]
    assert last["choices"][0]["finish_reason"] == "stop"
