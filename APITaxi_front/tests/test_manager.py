from flask_security import current_user

from APITaxi_models2 import db
from APITaxi_models2.unittest.factories import UserFactory


def test_logas_feature(no_roles):
    # Not a manager
    resp = no_roles.client.get('/manager/logas')
    assert resp.status_code == 302

    non_managed_user = UserFactory()

    managed_user = UserFactory(manager=no_roles.user)
    db.session.refresh(no_roles.user)

    # It is now possible to list user
    resp = no_roles.client.get('/manager/logas')
    assert resp.status_code == 200

    # Try to log-as a non-existing user
    resp = no_roles.client.post('/manager/logas', data={'user_id': 9999999})
    assert current_user.id == no_roles.user.id
    assert resp.status_code == 404

    # Try to log-as a non-managed user
    resp = no_roles.client.post('/manager/logas', data={'user_id': non_managed_user.id})
    assert current_user.id == no_roles.user.id
    assert resp.status_code == 404

    # Try to log-as the new user
    resp = no_roles.client.post('/manager/logas', data={'user_id': managed_user.id})
    assert current_user.id == managed_user.id
    assert resp.status_code == 302

    # Try to logout
    resp = no_roles.client.post('/logas/logout')
    assert resp.status_code == 302
    assert current_user.id == no_roles.user.id

    # Try to logout again from the origin account
    resp = no_roles.client.post('/logas/logout')
    assert resp.status_code == 302
    assert current_user.is_anonymous
