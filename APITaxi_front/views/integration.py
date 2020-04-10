from datetime import datetime
import json
import hashlib
import random
import socket
import time
from urllib.parse import urljoin

import requests

from sqlalchemy import or_
from sqlalchemy.orm.exc import NoResultFound

from flask import abort, Blueprint, current_app, redirect, render_template, url_for
from flask_security import current_user, login_required, roles_accepted
from flask_wtf import FlaskForm

from wtforms import SelectField, StringField, SubmitField, ValidationError, validators

from faker import Faker

from APITaxi_models import Hail, Taxi
from APITaxi_models.security import User

from .. import redis_client


blueprint = Blueprint('integration', __name__)


def blueprint_enabled(app):
    """This blueprint should only be enabled if TESTER_ENABLED is set, which is only True on
    https://dev.api.taxi and on local setup."""
    assert 'TESTER_ENABLED' in app.config
    return app.config['TESTER_ENABLED']


def get_integration_user(*fields):
    """Get the User object of the integration account as specified by the configuration."""
    try:
        return User.query.with_entities(*fields) \
                         .filter_by(email=current_app.config['TESTER_ACCOUNT_EMAIL']) \
                         .one()
    except NoResultFound:
        raise RuntimeError('%s account does not exist' % current_app.config['TESTER_ACCOUNT_EMAIL'])


class APITaxiIntegrationClient:
    """Wrapper to call APITaxi using credentials from settings."""
    def __init__(self, user=None):
        self.api_url = current_app.config['API_TAXI_URL']
        if user:
            self.api_key = user.apikey
        else:
            self.api_key = get_integration_user(User.apikey).apikey
        self.headers = {
            'X-Api-Key': self.api_key,
            'X-Version': '3',
            'Accept': 'application/json'
        }
        self.post_headers = dict(
            list(self.headers.items()) + list({
                'Content-Type': 'application/json'
            }.items())
        )

    def _modify_request(self, verb, endpoint, data):
        """Helper for POST, PUT, PATCH requests."""
        url = urljoin(self.api_url, endpoint)
        resp = verb(
            url,
            data=json.dumps({
                'data': [
                    data
                ]
            }),
            headers=self.post_headers
        )
        resp.raise_for_status()
        return resp.json()['data'][0]

    def post(self, endpoint, data):
        return self._modify_request(requests.post, endpoint, data)

    def put(self, endpoint, data):
        return self._modify_request(requests.put, endpoint, data)

    def get(self, endpoint, **kwargs):
        url = urljoin(self.api_url, endpoint)
        resp = requests.get(url, params=kwargs, headers=self.headers)
        resp.raise_for_status()
        return resp.json()['data']


@blueprint.route('/integration')
@login_required
@roles_accepted('admin', 'moteur', 'operateur')
def index():
    return render_template('integration/index.html')


class TaxiCreateForm(FlaskForm):
    """Form without any fields, just used for CSRF validation."""
    pass


@blueprint.route('/integration/operator/', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'moteur', 'operateur')
def operator():
    taxi_create_form = TaxiCreateForm()

    if not taxi_create_form.validate_on_submit():
        return render_template('integration/operator.html', taxi_create_form=taxi_create_form)

    faker = Faker('fr_FR')
    firstname, lastname = faker.first_name(), faker.last_name()

    api = APITaxiIntegrationClient()

    driver = api.post('/drivers', {
        'first_name': faker.first_name(),
        'last_name': faker.last_name(),
        'birth_date': faker.date(end_datetime=datetime(2000, 1, 1)),
        'professional_licence': 'fake-' + str(int(random.random() * 10**9)),
        'departement': {
            'nom': 'Paris'
        }
    })

    vehicle = api.post('/vehicles', {
        'color': faker.safe_color_name(),
        'licence_plate': faker.license_plate()
    })

    ads = api.post('/ads', {
        'vehicle_id': vehicle['id'],
        'category': '',
        'insee': '75101',
        'numero': str(random.randrange(1, 10**6)),
        'owner_type': 'company',
        'owner_name': 'le.taxi',
        'doublage': False
    })

    taxi = api.post('/taxis', {
        'ads': {
            'insee': '75101',
            'numero': ads['numero']
        },
        'driver': {
            'departement': '75',
            'professional_licence': driver['professional_licence'],
        },
        'vehicle': {
            'licence_plate': vehicle['licence_plate']
        }
    })
    return redirect(url_for('integration.operator'))


class ValidateFloat:
    def __call__(self, form, field):
        try:
            float(field.data)
        except ValueError:
            raise ValidationError('Valeur invalide.')


class TaxiLocationForm(FlaskForm):
    lon = StringField(validators=[validators.Required('Champ requis.'), ValidateFloat()])
    lat = StringField(validators=[validators.Required('Champ requis.'), ValidateFloat()])
    submit_taxi_location = SubmitField()


def update_taxi_position(integration_user, taxi_id, lon, lat):
    """Query geotaxi to update the position of taxi_id."""
    payload = {
        'timestamp': int(time.time()),
        'operator': integration_user.email,
        'taxi': taxi_id,
        'lon': lon,
        'lat': lat,
        'device': 'phone',
        'status': 'free',
        'version':'2',
    }
    # Build hash to identify the request
    h = ''.join(str(payload[key]) for key in [
        'timestamp',
        'operator',
        'taxi',
        'lat',
        'lon',
        'device',
        'status',
        'version'
    ])
    h += integration_user.apikey
    payload['hash'] = hashlib.sha1(h.encode('utf8')).hexdigest()
    # Send udpate request to geotaxi
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(
        json.dumps(payload).encode('utf8'),
        (current_app.config['GEOTAXI_HOST'], current_app.config['GEOTAXI_PORT'])
    )


class TaxiStatusForm(FlaskForm):
    status = SelectField(choices=[
        ('free', 'free'),
        ('occupied', 'occupied'),
        ('oncoming', 'oncoming'),
        ('off', 'off'),
    ])
    submit_taxi_status = SubmitField()


def _get_taxi_details(taxi_id):
    """Helper function used in operator_taxi_details and search_taxi_details.

    Return the integration user, the taxi object and its last location, and
    operator names of the taxi.
    """
    integration_user = get_integration_user(User.id, User.email, User.apikey)

    try:
        taxi = Taxi.query.filter(
            Taxi.id == taxi_id,
            or_(Taxi.added_by == integration_user.id, Taxi.added_by == current_user.id)
        ).one()
    except NoResultFound:
        abort(404, 'Unknown taxi id')

    # Retrieve last known taxi location
    redis_data = redis_client.hget('taxi:%s' % taxi.id, integration_user.email)
    last_location = None
    if redis_data:
        try:
            timestamp, lat, lon, status, device, version = redis_data.decode('utf8').split()
            last_location = {
                'date': datetime.fromtimestamp(int(timestamp)),
                'lat': float(lat),
                'lon': float(lon),
                'status': status,
            }
        except ValueError:  # Bad redis format
            pass

    # Taxis can be registered with several operators. In the case has a taxi
    # uses, let's say, three applications, the database objects created will
    # be:
    # - one taxi object (linked to one ADS, one driver, one vehicle)
    # - one vehicle object
    # - one vehicle_description object per operator.
    #
    # The VehicleDescription.added_by SQLAlchemy field from APITaxi_models doesn't
    # have a relationship to a User object, so we can't easily get the name of
    # the operator from a VehicleDescription.
    #
    # Below, we build a dictionary where keys are user ids from the fields
    # added_by of the VehicleDescription objects, and the values are the names
    # of the operators.
    #
    # Note: integration taxis are created with only one operator, we could also
    # remote this part and only display the first VehicleDescription in the
    # UI. I prefer not to and display all operators as it could make debug
    # easier if we attempt to make integration tests with more complex cases
    # someday.
    operators_names = {
        description.added_by: User.query.with_entities(User.email).filter_by(
            id=description.added_by
        ).one().email
        for description in taxi.vehicle.descriptions
    }

    return integration_user, taxi, last_location, operators_names


@blueprint.route('/integration/operator/taxis/<string:taxi_id>', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'moteur', 'operateur')
def operator_taxi_details(taxi_id):
    integration_user, taxi, last_location, operators_names = _get_taxi_details(taxi_id)

    status_form = TaxiStatusForm()
    if status_form.submit_taxi_status.data and status_form.validate_on_submit():
        api = APITaxiIntegrationClient()
        api.put('/taxis/%s' % taxi.id, {'status': status_form.status.data})
        return redirect(url_for('integration.operator_taxi_details', taxi_id=taxi_id))

    location_form = TaxiLocationForm()
    if location_form.submit_taxi_location.data and location_form.validate_on_submit():
        update_taxi_position(
            integration_user,
            taxi_id,
            location_form.lon.data,
            location_form.lat.data
        )

        api = APITaxiIntegrationClient()
        api.put('/taxis/%s' % taxi.id, {'status': 'free'})

        return redirect(url_for('integration.operator_taxi_details', taxi_id=taxi_id))

    return render_template(
        'integration/operator_taxi_details.html',
        taxi=taxi,
        status_form=status_form,
        location_form=location_form,
        last_location=last_location,
        operators_names=operators_names
    )


@blueprint.route('/integration/search', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'moteur', 'operateur')
def search():
    location_form = TaxiLocationForm()

    taxis = None

    if location_form.validate_on_submit():
        api = APITaxiIntegrationClient()
        taxis = api.get('/taxis', lon=location_form.lon.data, lat=location_form.lat.data)

    return render_template('integration/search.html', location_form=location_form, taxis=taxis)


class CreateHailForm(FlaskForm):
    customer_lon = StringField(validators=[validators.Required('Champ requis.'), ValidateFloat()])
    customer_lat = StringField(validators=[validators.Required('Champ requis.'), ValidateFloat()])
    customer_address = StringField(validators=[validators.Required('Champ requis.')])
    customer_phone_number = StringField(validators=[validators.Required('Champ requis.')])
    taxi_operator = SelectField()
    customer_internal_id = StringField(validators=[validators.Required('Champ requis.')])

    submit_create_hail = SubmitField()


@blueprint.route('/integration/search/taxis/<string:taxi_id>', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'moteur', 'operateur')
def search_taxi_details(taxi_id):
    integration_user, taxi, last_location, operators_names = _get_taxi_details(taxi_id)

    create_hail_form = CreateHailForm()
    create_hail_form.taxi_operator.choices = [
        (name, name) for name in operators_names.values()
    ]

    api_error_msg = None

    if create_hail_form.validate_on_submit():
        api = APITaxiIntegrationClient(user=integration_user)
        try:
            resp = api.post('/hails', {
                'customer_lon': create_hail_form.customer_lon.data,
                'customer_lat': create_hail_form.customer_lat.data,
                'customer_address': create_hail_form.customer_address.data,
                'taxi_id': taxi_id,
                'customer_phone_number': create_hail_form.customer_phone_number.data,
                'operateur': create_hail_form.taxi_operator.data,
                'customer_id': create_hail_form.customer_internal_id.data
            })
            return redirect(url_for('integration.search_hail_details', hail_id=resp['id']))
        except requests.exceptions.HTTPError as exc:
            api_error_msg = "Erreur lors de la demande de course. L'API a retourné le message " \
                            "suivant : %s" % exc.response.json()['message']

    return render_template(
        'integration/search_taxi_details.html',
        taxi=taxi,
        last_location=last_location,
        operators_names=operators_names,
        create_hail_form=create_hail_form,
        api_error_msg=api_error_msg
    )


class HailStatusForm(FlaskForm):
    status = SelectField(choices=[
        ('accepted_by_customer', 'accepted_by_customer'),
        ('declined_by_customer', 'declined_by_customer'),
        ('incident_customer', 'incident_customer'),
    ])


@blueprint.route('/integration/search/hails/<string:hail_id>', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'moteur', 'operateur')
def search_hail_details(hail_id):
    integration_user = get_integration_user(User.id, User.apikey)
    try:
        hail = Hail.query.filter(
            Hail.id == hail_id,
            or_(Hail.added_by == integration_user.id, Hail.added_by == current_user.id)
        ).one()
    except NoResultFound:
        abort(404, 'Unknown taxi id')

    status_form = HailStatusForm()
    if status_form.validate_on_submit():
        api = APITaxiIntegrationClient(user=integration_user)
        api.put('/hails/%s' % hail_id, {'status': status_form.status.data})
        return redirect(url_for('integration.search_hail_details', hail_id=hail_id))

    return render_template('integration/search_hail_details.html', hail=hail, status_form=status_form)
