from flask_security import current_user

from APITaxi_models2 import db
from APITaxi_models2.unittest.factories import UserFactory


def test_logas_feature(operateur):
    # Not a manager
    resp = operateur.client.get('/manager/logas')
    assert resp.status_code == 302

    non_managed_user = UserFactory()

    managed_user = UserFactory(manager=operateur.user)
    db.session.refresh(operateur.user)

    # It is now possible to list user
    resp = operateur.client.get('/manager/logas')
    assert resp.status_code == 200

    # Try to log-as a non-existing user
    resp = operateur.client.post('/manager/logas', data={'user_id': 9999999})
    assert current_user.id == operateur.user.id
    assert resp.status_code == 404

    # Try to log-as a non-managed user
    resp = operateur.client.post('/manager/logas', data={'user_id': non_managed_user.id})
    assert current_user.id == operateur.user.id
    assert resp.status_code == 404

    # Try to log-as the new user
    resp = operateur.client.post('/manager/logas', data={'user_id': managed_user.id})
    assert current_user.id == managed_user.id
    assert resp.status_code == 302

    # Try to logout
    resp = operateur.client.post('/logas/logout')
    assert resp.status_code == 302
    assert current_user.id == operateur.user.id

    # Try to logout again from the origin account
    resp = operateur.client.post('/logas/logout')
    assert resp.status_code == 302
    assert current_user.is_anonymous
