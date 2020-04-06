from datetime import datetime
import json
import hashlib
import random
import socket
import time
from urllib.parse import urljoin

import requests

from sqlalchemy.orm.exc import NoResultFound

from flask import abort, Blueprint, current_app, redirect, render_template, url_for
from flask_security import login_required, roles_accepted
from flask_wtf import FlaskForm

from wtforms import StringField, ValidationError, validators

from faker import Faker

from APITaxi_models import Taxi
from APITaxi_models.security import User

from .. import redis_client


blueprint = Blueprint('tester', __name__)


def blueprint_enabled(app):
    """This blueprint should only be enabled if TESTER_ENABLED is set, which is only True on
    https://dev.api.taxi and on local setup."""
    assert 'TESTER_ENABLED' in app.config
    return app.config['TESTER_ENABLED']


def get_tester_user(*fields):
    """Get the User object of the tester account as specified by the configuration."""
    try:
        return User.query.with_entities(*fields) \
                         .filter_by(email=current_app.config['TESTER_ACCOUNT_EMAIL']) \
                         .one()
    except NoResultFound:
        raise RuntimeError('%s account does not exist' % current_app.config['TESTER_ACCOUNT_EMAIL'])


class APITaxiTesterClient:
    """Wrapper to call APITaxi using credentials from settings."""
    def __init__(self):
        self.api_url = current_app.config['API_TAXI_URL']
        self.api_key = get_tester_user(User.apikey).apikey

    def post(self, endpoint, data):
        url = urljoin(self.api_url, endpoint)
        resp = requests.post(
            url,
            data=json.dumps({
                'data': [
                    data
                ]
            }),
            headers={
                'X-Api-Key': self.api_key,
                'X-Version': '3',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        )
        resp.raise_for_status()
        return resp.json()['data'][0]


@blueprint.route('/tester')
@login_required
@roles_accepted('admin', 'moteur', 'operateur')
def index():
    return render_template('tester/index.html')


class TaxiCreateForm(FlaskForm):
    """Form without any fields, just used for CSRF validation."""
    pass


@blueprint.route('/tester/operator/', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'moteur', 'operateur')
def operator():
    taxi_create_form = TaxiCreateForm()

    if not taxi_create_form.validate_on_submit():
        return render_template('tester/operator.html', taxi_create_form=taxi_create_form)

    faker = Faker('fr_FR')
    firstname, lastname = faker.first_name(), faker.last_name()

    api = APITaxiTesterClient()

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
    return redirect(url_for('tester.operator'))


class ValidateFloat:
    def __call__(self, form, field):
        try:
            float(field.data)
        except ValueError:
            raise ValidationError('Valeur invalide.')


class TaxiUpdateLocationForm(FlaskForm):
    lon = StringField(validators=[validators.Required('Champ requis.'), ValidateFloat()])
    lat = StringField(validators=[validators.Required('Champ requis.'), ValidateFloat()])


def update_taxi_position(tester_user, taxi_id, lon, lat):
    """Query geotaxi to update the position of taxi_id."""
    payload = {
        'timestamp': int(time.time()),
        'operator': tester_user.email,
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
    h += tester_user.apikey
    payload['hash'] = hashlib.sha1(h.encode('utf8')).hexdigest()
    # Send udpate request to geotaxi
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(
        json.dumps(payload).encode('utf8'),
        (current_app.config['GEOTAXI_HOST'], current_app.config['GEOTAXI_PORT'])
    )


@blueprint.route('/tester/operator/taxis/<string:taxi_id>', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'moteur', 'operateur')
def operator_taxi_details(taxi_id):
    tester_user = get_tester_user(User.id, User.email, User.apikey)

    try:
        taxi = Taxi.query.filter(
            Taxi.id == taxi_id,
            Taxi.added_by == tester_user.id
        ).one()
    except NoResultFound:
        abort(404, 'Unknown taxi id')

    update_location_form = TaxiUpdateLocationForm()
    if update_location_form.validate_on_submit():
        update_taxi_position(
            tester_user,
            taxi_id,
            update_location_form.lon.data,
            update_location_form.lat.data
        )
        return redirect(url_for('tester.operator_taxi_details', taxi_id=taxi_id))

    # Retrieve last known taxi location
    redis_data = redis_client.hget('taxi:%s' % taxi.id, tester_user.email)
    last_location = None
    if redis_data:
        try:
            timestamp, lat, lon, status, device, version = redis_data.decode('utf8').split()
            last_location = {
                'date': datetime.fromtimestamp(int(timestamp)),
                'lat': float(lat),
                'lon': float(lon)
            }
        except ValueError:  # Bad redis format
            pass

    return render_template(
        'tester/operator_taxi_details.html',
        taxi=taxi,
        update_location_form=update_location_form,
        last_location=last_location
    )


@blueprint.route('/tester/search')
@login_required
@roles_accepted('admin', 'moteur', 'operateur')
def search():
    return render_template('tester/search.html')
