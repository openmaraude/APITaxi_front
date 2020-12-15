import json

from flask_security import current_user

from APITaxi_models2 import RolesUsers, User
from APITaxi_models2.unittest.factories import RoleFactory, RolesUsersFactory, UserFactory


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
    resp = admin.client.post('/logas/logout')
    assert resp.status_code == 302
    assert current_user.id == admin.user.id

    # Try to logout again from the origin account
    resp = admin.client.post('/logas/logout')
    assert resp.status_code == 302
    assert current_user.is_anonymous


def test_logout_deleted_user(admin):
    """Attempt to logout to a non-existing user."""
    other_admin = UserFactory()
    RolesUsersFactory(role=RoleFactory(name='admin'), user=other_admin)

    user = UserFactory()

    # Log as the manager
    resp = admin.client.post('/admin/logas', data={'user_id': other_admin.id})
    assert current_user.id == other_admin.id
    assert resp.status_code == 302

    # Log as the user
    resp = admin.client.post('/admin/logas', data={'user_id': user.id})
    assert current_user.id == user.id
    assert resp.status_code == 302

    RolesUsers.query.filter_by(user=other_admin).delete()
    User.query.filter_by(id=other_admin.id).delete()

    # Logout as the admin, which doesn't exist anymore.
    resp = admin.client.post('/logas/logout')
    assert resp.status_code == 302
    assert current_user.is_anonymous
    # logas_sessions is emptied, and user is logged out.
    for header in resp.headers.getlist('set-cookie'):
        assert 'logas_sessions=;' in header or 'session=;' in header


def test_security(admin):
    """Attempt to alter cookies to gain privileges."""
    new_user = UserFactory()

    # Log-as the new user
    resp = admin.client.post('/admin/logas', data={'user_id': new_user.id})
    assert current_user.id == new_user.id
    assert resp.status_code == 302

    admin.client.set_cookie('localhost', 'logas_sessions', json.dumps([
        'altered'
    ]))

    # Try to logout: 400 response, logas_sessions cookie is emptied, and user
    # is logged out.
    resp = admin.client.post('/logas/logout')
    assert resp.status_code == 400
    for header in resp.headers.getlist('set-cookie'):
        assert 'logas_sessions=;' in header or 'session=;' in header
