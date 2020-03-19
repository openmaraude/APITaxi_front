# -*- coding: utf-8 -*-

from datetime import datetime
import json

from flask import abort, Blueprint, redirect, render_template, url_for
from flask_security import current_user, login_required, roles_accepted

from APITaxi_models import Hail

from .. import redis_client


blueprint = Blueprint('dashboards', __name__)


@blueprint.route('/dashboards', methods=['GET'])
@login_required
@roles_accepted('admin', 'moteur', 'operateur')
def index():
    return render_template('dashboards/index.html')


@blueprint.route('/dashboards/hails', methods=['GET'])
@login_required
@roles_accepted('admin', 'moteur', 'operateur')
def hails():
    return render_template('dashboards/hails.html')


@blueprint.route('/dashboards/hails/<string:hail_id>')
@login_required
def hails_details(hail_id):
    hail = Hail.query.get(hail_id)

    if not (current_user.has_role('admin') or current_user.id in (hail.operateur_id, hail.added_by)):
        abort(403)

    resp = redis_client.zrangebyscore('hail:%s' % hail_id, '-inf', '+inf', withscores=True)

    logs = [
        (datetime.fromtimestamp(date), json.loads(value.decode('utf8')))
        for value, date in resp
    ]

    return render_template('dashboards/hails_details.html', hail=hail, logs=logs)


@blueprint.route('/dashboards/taxis', methods=['GET'])
@login_required
@roles_accepted('admin', 'moteur', 'operateur')
def taxis():
    return render_template('dashboards/taxis.html')
