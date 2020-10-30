def test_documentation(anonymous):
    """Documentation is available to anonymous users."""
    for endpoint in (
        '/documentation',
        '/documentation/search',
        '/documentation/operator',
        '/documentation/examples',
    ):
        resp = anonymous.client.get(endpoint)
        assert resp.status_code == 200

    resp = anonymous.client.get('/documentation/reference')
    assert resp.status_code == 302
