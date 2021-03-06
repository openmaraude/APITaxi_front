from flask_security.utils import verify_password

from APITaxi_models2 import db


def test_profile(operateur, moteur):
    resp = operateur.client.get('/profile')
    assert resp.status_code == 200

    # Passwords and confirmation don't match
    resp = operateur.client.post('/profile', data={
        'password': 'xxxxxxxxxxxx',
        'password_confirm': 'yyyyyyy'
    })
    assert 'Formulaire invalide' in resp.data.decode('utf8')

    # Make sure password is changed
    resp = operateur.client.post('/profile', data={
        'password': 'eqwiofnpqiwof',
        'password_confirm': 'eqwiofnpqiwof',
        'commercial_name': 'New NAME',
        'phone_number_technical': '+3368908323',
        'email_technical': 'tek@email.com',
        'phone_number_customer': '+338234822342',
        'email_customer': 'cust@email.com',
        'hail_endpoint_production': 'http://xxx',
        'operator_header_name': 'X-Header',
        'operator_api_key': 'MyApiKey'
    })
    assert resp.status_code == 302

    assert verify_password('eqwiofnpqiwof', operateur.user.password) is True
    assert operateur.user.commercial_name == 'New NAME'
    assert operateur.user.phone_number_technical == '+3368908323'
    assert operateur.user.email_technical == 'tek@email.com'
    assert operateur.user.phone_number_customer == '+338234822342'
    assert operateur.user.email_customer == 'cust@email.com'

    assert operateur.user.hail_endpoint_production == 'http://xxx'
    assert operateur.user.operator_header_name == 'X-Header'
    assert operateur.user.operator_api_key == 'MyApiKey'

    # Operateur doesn't have an account manager.
    assert 'Gestionnaire de compte' not in resp.data.decode('utf8')

    # If we set an account manager, it should be displayed on the profile page.
    operateur.user.manager_id = moteur.user.id
    db.session.commit()
    resp = operateur.client.get('/profile')
    assert 'Gestionnaire de compte' in resp.data.decode('utf8')
