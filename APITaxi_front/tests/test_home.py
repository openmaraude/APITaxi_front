def test_home(moteur):
    resp = moteur.client.get('/')
    assert resp.status_code == 302
