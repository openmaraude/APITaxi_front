# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, url_for, jsonify
from flask_restplus import reqparse, abort
from flask_security import login_required, current_user
from APITaxi_utils import request_wants_json
from APITaxi_models.security import User, db
from APITaxi_models.hail import Hail
from APITaxi_models.taxis import Taxi
from datetime import datetime, timedelta
from itertools import groupby
import json
from geopy.distance import vincenty
from math import trunc
from sqlalchemy import func

class HailEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Hail):
            return [obj.id, obj.status,
                    '{:d} mètres'.format(trunc(
                        vincenty((obj.customer_lat, obj.customer_lon),
                       (obj.initial_taxi_lat, obj.initial_taxi_lon)).meters))]
        elif isinstance(obj, Taxi):
            return obj.vehicle.licence_plate
        return json.JSONEncoder.default(self, obj)


mod = Blueprint('home_bo', __name__)

@mod.route('/')
@login_required
def home():
    if current_user.has_role('admin'):
        user_list = [u for u in User.query.all() if u.has_role('operateur')]
    elif current_user.has_role('operateur'):
        user_list = [current_user]
    else:
        user_list = []
    return render_template('index.html',
                          user_name_list=[u.email for u in user_list],
                          is_admin=current_user.has_role('admin'),
                          apikey=current_user.apikey)

@mod.route('/table')
@login_required
def table():
    user = None
    if current_user.has_role('admin'):
        parser = reqparse.RequestParser()
        parser.add_argument('user')
        args = parser.parse_args()
        if not 'user' in args:
            abort(400)
        user = User.query.filter(User.email==args['user']).first()
    elif current_user.has_role('operateur'):
        user = current_user
    if not user:
        abort(400)
    hails = Hail.query.filter(
                        Hail.operateur_id == user.id,
                        Hail.added_at >= datetime.now() - timedelta(weeks=1),
                        Hail._status.in_(['timeout_taxi', 'declined_by_taxi',
                                         'incident_taxi'])
    ).all()
    hails_sorted = sorted(hails, key=lambda h: h.taxi_id)
    hails_grouped = [(v[0], list(v[1]), Taxi.query.get(v[0]))
                     for v in groupby(hails_sorted, key=lambda h: h.taxi_id)
                    ]
    return jsonify({"data":
        json.loads(json.dumps(
            sorted(hails_grouped, key=lambda l: len(l[1]), reverse=True)[:20],
            cls=HailEncoder))})


@mod.route('/stats_hails')
@login_required
def stats():
    statuses = {"declined_by_taxi": ["timeout_taxi", "declined_by_taxi", "incident_taxi"],
                "declined_by_customer": ["timeout_customer", "declined_by_customer",
                                        "incident_customer"],
                "ok": ["accepted_by_customer", "customer_on_board", "finished"],
                "total": []}
    user = None
    if current_user.has_role('admin'):
        parser = reqparse.RequestParser()
        parser.add_argument('user')
        args = parser.parse_args()
        if not 'user' in args:
            abort(400)
        user_list = [User.query.filter(User.email==args['user']).first(), None]
        status_keys = statuses.keys()
    elif current_user.has_role('operateur'):
        user_list = [current_user]
        status_keys = ["total", "declined_by_taxi", "ok"]
    elif current_user.has_role('moteur'):
        user_list = [current_user]
        status_keys = ["total", "declined_by_customer", "ok"]
    else:
        abort(400)

    res = []
    for user in user_list:
        email = user.email if user else 'total'
        filters = [Hail.added_at >= datetime.now() - timedelta(weeks=2)]
        if user and user.has_role('moteur'):
            filters += [Hail.added_by == user.id]
        if user and user.has_role('operateur'):
            filters += [Hail.operateur_id == user.id]
        res.append({"email": email})
        for key in status_keys:
            status_filters = [Hail._status != 'customer_banned']
            if statuses[key]:
                status_filters += [Hail._status.in_(statuses[key])]
            q = db.session.query(
                    func.date(Hail.added_at),
                    func.count('id')
                ).select_from(Hail).filter(
                    *status_filters + filters
                ).group_by(
                    func.date(Hail.added_at)
                ).order_by(
                    func.date(Hail.added_at)
            )
            res[-1][key] = {k_v[0].isoformat(): k_v[1] for k_v in q.all()}
    return jsonify({"data": res})


