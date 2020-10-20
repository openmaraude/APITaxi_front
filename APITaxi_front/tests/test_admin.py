from flask_security import current_user

from APITaxi_models2.unittest.factories import UserFactory


def test_logas_feature(admin, moteur, operateur):
    # Not enough permissions
    for client in (moteur, operateur):
        resp = client.client.get('/admin/logas')
        assert resp.status_code == 302

    # List users
    resp = admin.client.get('/admin/logas')
    assert resp.status_code == 200

    new_user = UserFactory()

    assert current_user.id == admin.user.id

    # Try to log-as a non-existing user
    resp = admin.client.post('/admin/logas', data={'user_id': 9999999})
    assert current_user.id == admin.user.id
    assert resp.status_code == 404

    # Try to log-as the new user
    resp = admin.client.post('/admin/logas', data={'user_id': new_user.id})
    assert current_user.id == new_user.id
    assert resp.status_code == 302

    # Try to logout
    resp = admin.client.get('/logas/logout')
    assert resp.status_code == 302
    assert current_user.id == admin.user.id

    # Try to logout again from the origin account
    resp = admin.client.get('/logas/logout')
    assert resp.status_code == 302
    assert current_user.is_anonymous
