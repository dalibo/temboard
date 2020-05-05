def test_get_json(http):
    resp = http.get('/sample/')
    assert resp.json
    assert 'message' in resp.json
    assert resp.json['sample']
    assert "configured" == resp.json['option']
