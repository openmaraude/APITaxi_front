from APITaxi_models2.unittest.factories import HailFactory, TaxiFactory, UserFactory


def test_users(admin):
    UserFactory.create_batch(30)
    # Create extra users to test search filters
    UserFactory(commercial_name='supertop')
    UserFactory(email='abcdefghi')

    resp = admin.client.get('/api/users?length=10&start=0&draw=1')
    assert resp.status_code == 200
    assert len(resp.json['data']) == 10

    # Filter on commercial_name
    resp = admin.client.get(
        '/api/users?'
        'length=10&start=0&draw=1'
        '&columns[0][name]=commercial_name'
        '&columns[0][search][value]=SUPERTOP'
    )
    assert resp.status_code == 200
    assert len(resp.json['data']) == 1

    # Filter on email
    resp = admin.client.get(
        '/api/users?'
        'length=10&start=0&draw=1'
        '&columns[0][name]=email'
        '&columns[0][search][value]=abc'
    )
    assert resp.status_code == 200
    assert len(resp.json['data']) == 1


def test_hails(app, moteur, operateur):
    integration_user = UserFactory(email=app.config['INTEGRATION_ACCOUNT_EMAIL'])

    # Hail created by moteur
    hail = HailFactory(added_by=moteur.user)
    # Hail of integration user
    HailFactory(added_by=integration_user, operateur=integration_user)

    # List hails where moteur is the owner
    resp = moteur.client.get('/api/hails?length=10&start=0&draw=1')
    assert resp.status_code == 200
    assert len(resp.json['data']) == 1

    # Operateur doesn't have any hail
    resp = operateur.client.get('/api/hails?length=10&start=0&draw=1')
    assert resp.status_code == 200
    assert len(resp.json['data']) == 0

    # Filter on taxi_id
    resp = moteur.client.get(
        '/api/hails?'
        'length=10&start=0&draw=1'
        '&columns[0][name]=taxi_id'
        '&columns[0][search][value]=%s' % hail.taxi_id
    )
    assert resp.status_code == 200
    assert len(resp.json['data']) == 1

    # Filter on taxi_id without match
    resp = moteur.client.get(
        '/api/hails?'
        'length=10&start=0&draw=1'
        '&columns[0][name]=taxi_id'
        '&columns[0][search][value]=xxx'
    )
    assert resp.status_code == 200
    assert len(resp.json['data']) == 0

    # If ?integration is given, we should return hails of integration user
    resp = moteur.client.get(
        '/api/hails?'
        'length=10&start=0&draw=1'
        '&integration'
    )
    assert resp.status_code == 200
    assert len(resp.json['data']) == 1


def test_taxis(app, operateur):
    integration_user = UserFactory(email=app.config['INTEGRATION_ACCOUNT_EMAIL'])

    # Create two taxis created by integration user
    TaxiFactory(added_by=integration_user)
    TaxiFactory(added_by=integration_user)

    # Three taxis, one with explicit licence_plate and taxi_id
    TaxiFactory(added_by=operateur.user)
    TaxiFactory(added_by=operateur.user)
    taxi = TaxiFactory(added_by=operateur.user)

    resp = operateur.client.get(
        '/api/taxis?'
        'length=10&start=0&draw=1'
    )
    assert resp.status_code == 200
    assert len(resp.json['data']) == 3

    # Filter on licence_plate and taxi_id
    resp = operateur.client.get(
        '/api/taxis?'
        'length=10&start=0&draw=1'
        '&columns[0][name]=taxi_id'
        '&columns[0][search][value]=%s'
        '&columns[1][name]=licence_plate'
        '&columns[1][search][value]=%s' % (taxi.id, taxi.vehicle.licence_plate)
    )
    assert resp.status_code == 200
    assert len(resp.json['data']) == 1

    # Search integration user taxis
    # Filter on licence_plate and taxi_id
    resp = operateur.client.get(
        '/api/taxis?'
        'length=10&start=0&draw=1'
        '&integration'
    )
    assert resp.status_code == 200
    assert len(resp.json['data']) == 2
