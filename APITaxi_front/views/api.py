# -*- coding: utf-8 -*-
"""This module gathers JSON endpoints, used by AJAX calls.
"""

import functools
import math
import re

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, url_for
from flask_security import current_user, login_required, roles_accepted

from sqlalchemy import func, or_
from sqlalchemy.orm import aliased

from marshmallow import fields, EXCLUDE, pre_load, Schema, ValidationError
from marshmallow.validate import Range

from geopy.distance import vincenty

from APITaxi_models import db, Hail, Taxi, Vehicle
from APITaxi_models.security import User

from .integration import get_integration_user


blueprint = Blueprint('api', __name__)


class DataTablesSchema(Schema):
    """Validate parameters for /api/users."""

    class Meta:
        """Do not raise an error nor return extra fields when calling schema.load().
        """
        unknown = EXCLUDE

    @pre_load
    def preprocess(self, data, **kwargs):
        """Datatables queries views with the following querystring arguments:

            "draw": "1",
            "columns[0][data]": "id",
            "columns[0][name]": "taxi_id",
            "columns[0][searchable]": "true",
            "columns[0][orderable]": "false",
            "columns[0][search][value]": "oaakaafaiakkaaaawaa",
            "columns[0][search][regex]": "false",
            "columns[1][data]": ...
            ...
            "start": "0",
            "length": "50",
            "search[value]": "",
            "search[regex]": "false",

        This function returns a dictionary, like:

            {
                'draw': '1',
                'columns': {
                    '0': {
                        'data': 'id',
                        'name': 'taxi_id',
                        'searchable': 'true',
                        'orderable': 'false',
                        'search': {
                            'value': ...
                            'regex': ...
                        ...
                    }
                    ...
                }
            }

        Validators are run against the output of this function.
        """
        ret = {}

        for key, value in data.items():
            # The regex below matches: columns[field][field2][field3]
            res = re.match(r'^(?P<root_key>[^\[]+)(\[[^\[]+\])+', key)
            if not res:
                ret[key] = value
            else:
                root_key = res.groupdict()['root_key']
                # Match each subkey. For example for columns[field1][field2][field3], returns ['field1', 'fiel2', 'field3']
                subkeys = re.findall(r'\[([^\[]*)\]', key)

                if root_key not in ret:
                    ret[root_key] = {}

                tmp = ret[root_key]
                for subkey in subkeys[:-1]:
                    if subkey not in tmp:
                        tmp[subkey] = {}
                    tmp = tmp[subkey]
                tmp[subkeys[-1]] = value
        return dict(ret)

    length = fields.Int(required=True, validate=Range(min=1, max=100))
    start = fields.Int(required=True)
    # Javascript module datatables provides a draw id in the request that needs
    # to be sent back in the response.
    draw = fields.Int(required=True)

    columns = fields.Dict(required=False)


def get_datatables_filter(filter_name, columns):
    """Given the columns dictionary returned by Datatables.preprocess(), return the value of the search field
    `filter_name`.
    """
    if not columns:
        return

    for column in columns.values():
        if column.get('name') == filter_name:
            return column.get('search', {}).get('value')


def check_datatables_arguments(func):
    """Decorator to validate Datatables parameters.

    APIs endpoints below are expected to be called by the javascript frontend, but if a user attempts to make a cURL
    query, we want to display an explicit error message to ask to provide the parameters as the front does.
    """
    @functools.wraps(func)
    def _decorator(*args, **kwargs):
        try:
            params = DataTablesSchema().load(dict(request.args))
        except ValidationError as err:
            return jsonify({'errors': err.messages})
        return func(**params)
    return _decorator


@blueprint.route('/api/users', methods=['GET'])
@login_required
@roles_accepted('admin')
@check_datatables_arguments
def users(length, start, draw, columns=None):
    """Administration endpoint to list users."""
    query = User.query.order_by(User.id)
    records_total = query.count()

    commercial_name_filter = get_datatables_filter('commercial_name', columns)
    if commercial_name_filter:
        query = query.filter(func.lower(User.commercial_name).startswith(commercial_name_filter.lower()))

    email_filter = get_datatables_filter('email', columns)
    if email_filter:
        query = query.filter(func.lower(User.email).startswith(email_filter.lower()))

    records_filtered = query.count()
    users = query.offset(start).limit(length).all()

    # The format below is expected by datatables.
    return jsonify({
        'draw': draw,
        'recordsTotal': records_total,
        'recordsFiltered': records_filtered,
        'data': [{
            'id': user.id,
            'email': user.email,
            'commercial_name': user.commercial_name,
        } for user in users]
    })


@blueprint.route('/api/hails', methods=['GET'])
@login_required
@roles_accepted('admin', 'moteur', 'operateur')
@check_datatables_arguments
def hails(length, start, draw, columns=None):
    """List taxis of operateur."""
    owner = current_user

    if 'integration' in request.args and current_app.config.get('TESTER_ENABLED', False):
        owner = get_integration_user(User.id)

    UserOperateur = aliased(User)
    UserMoteur = aliased(User)

    query = Hail.query.with_entities(
        Hail, UserOperateur, UserMoteur
    ).filter(
        or_(Hail.operateur_id == owner.id,
            Hail.added_by == owner.id)
    ).join(
        UserOperateur, Hail.operateur_id == UserOperateur.id
    ).join(
        UserMoteur, Hail.added_by == UserMoteur.id
    ).order_by(
        Hail.added_at.desc()
    )
    records_total = query.count()

    taxi_id_filter = get_datatables_filter('taxi_id', columns)
    if taxi_id_filter:
        query = query.filter(func.lower(Hail.taxi_id).startswith(taxi_id_filter.lower()))

    records_filtered = query.count()

    hails = query.offset(start).limit(length).all()

    # The format below is expected by datatables.
    return jsonify({
        'draw': draw,
        'recordsTotal': records_total,
        'recordsFiltered': records_filtered,
        'data': [{
            'id': hail.id,
            'status': hail.status,
            'taxi': {
                'id': hail.taxi_id,
            },
            'operateur': {
                'id': operateur.id,
                'commercial_name': operateur.commercial_name,
            },
            'moteur': {
                'id': moteur.id,
                'commercial_name': moteur.commercial_name,
            },
            'added_at': hail.added_at.isoformat(),
            'distance': math.trunc(vincenty(
                (hail.customer_lat, hail.customer_lon),
                (hail.initial_taxi_lat, hail.initial_taxi_lon)
            ).meters)
        } for hail, operateur, moteur in hails]
    })


@blueprint.route('/api/taxis', methods=['GET'])
@login_required
@roles_accepted('admin', 'operateur', 'moteur')
@check_datatables_arguments
def taxis(length, start, draw, columns=None):
    """List taxis of operateur.

    This API endpoint is used by the taxis dashboard and by the integration
    feature.
    """
    owner = current_user
    # There is no relationship between a Taxi and User. We don't want to modify
    # too much APITaxi_models for now, so let's store the operator name in a
    # dictionary.
    operator_names = {
        current_user.id: current_user.commercial_name
    }

    # This view is called by the integration feature to list taxis of the test
    # account. If integration is set, list taxis from the integration account
    # instead of taxis from the current account.
    if 'integration' in request.args and current_app.config.get('TESTER_ENABLED', False):
        owner = get_integration_user(User.id)
        integration_user = get_integration_user(User.id, User.commercial_name)
        operator_names[integration_user.id] = integration_user.commercial_name

    query = Taxi.query.join(Vehicle).filter(
        Taxi.added_by == owner.id
    ).order_by(
        Taxi.added_at.desc()
    )

    records_total = query.count()

    taxi_id_filter = get_datatables_filter('taxi_id', columns)
    if taxi_id_filter:
        query = query.filter(func.lower(Taxi.id).startswith(taxi_id_filter.lower()))

    licence_plate_filter = get_datatables_filter('licence_plate', columns)
    if licence_plate_filter:
        query = query.filter(func.lower(Vehicle.licence_plate).startswith(licence_plate_filter.lower()))

    records_filtered = query.count()

    taxis = query.offset(start).limit(length).all()

    # The format below is expected by datatables.
    return jsonify({
        'draw': draw,
        'recordsTotal': records_total,
        'recordsFiltered': records_filtered,
        'data': [{
            'id': taxi.id,
            'added_at': taxi.added_at,
            'vehicle': {
                'licence_plate': taxi.vehicle.licence_plate,
            },
            'driver': {
                'fullname': '%s %s' % (taxi.driver.first_name, taxi.driver.last_name)
            },
            'ads': {
                'zupc': {
                    'name': taxi.ads.zupc.nom,
                }
            },
            'operator': {
                'id': taxi.added_by,
                'commercial_name': operator_names.get(taxi.added_by)
            }
        } for taxi in taxis]
    })
