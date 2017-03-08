# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, url_for, jsonify
from flask_restplus import reqparse, abort
from flask_security import login_required, current_user
from APITaxi_utils import request_wants_json
import APITaxi_models as models
from datetime import datetime, timedelta, date
from itertools import groupby
import json
from geopy.distance import vincenty
from math import trunc
from sqlalchemy import func, or_


mod = Blueprint('home_bo', __name__)

@mod.route('/')
@login_required
def home():
    if current_user.has_role('admin'):
        user_list = [u for u in models.security.User.query.all() if u.has_role('operateur')]
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
    parser = reqparse.RequestParser()
    parser.add_argument('user')
    parser.add_argument('q')
    args = parser.parse_args()
    if current_user.has_role('admin'):
        if not 'user' in args and not 'q' in args:
            print  args
            abort(400)
        user = models.security.User.query.filter(models.security.User.email==args['user']).first()
    elif current_user.has_role('operateur'):
        user = current_user
    else:
        abort(400)
    filters = [models.Hail.added_at >= datetime.now() - timedelta(weeks=100),
               models.Hail._status != 'customer_banned']
    taxis = []
    if user:
        filters.append(models.Hail.operateur_id == user.id)
    if 'q' in args and args['q']:
        q = args['q']
        filters_taxi = [models.Taxi.id.like("%{}%".format(q)),]
        vehicle_descs = models.VehicleDescription.query.filter(
           models.VehicleDescription.internal_id.like("%{}%".format(q))).all()
        if vehicle_descs:
            filters_taxi.append(
                models.Taxi.vehicle_id.in_([v.vehicle_id for v in vehicle_descs])
            )
        vehicles = models.Vehicle.query.filter(
            models.Vehicle.licence_plate.like("%{}%".format(q))).all()
        if vehicles:
            filters_taxi.append(
                models.Taxi.vehicle_id.in_([v.id for v in vehicles])
            )

        taxis = filter(
            lambda t: current_user.has_role('admin') or
                      any(map(lambda vd: vd.added_by == current_user.id,
                          t.vehicle.descriptions)),
            models.Taxi.query.filter(or_(*filters_taxi)).all()
        )
        if taxis:
            filters.append(models.Hail.taxi_id.in_([t.id for t in taxis]))
        else:
            filters = None
    if filters:
        hails = models.Hail.query.filter(
            models.Hail._status.in_(['timeout_taxi', 'declined_by_taxi', 'incident_taxi']),
            *filters
        ).all()
    else:
        hails = []

    class HailEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, models.Hail):
                return {"id": obj.id,
                        "status": obj.status,
                        "date": obj.added_at.isoformat(),
                        "distance": trunc(
                            vincenty((obj.customer_lat, obj.customer_lon),
                                     (obj.initial_taxi_lat, obj.initial_taxi_lon)).meters)
                }
            elif isinstance(obj, models.Taxi):
                q = models.db.session.query(func.count('id')).filter(models.Hail.taxi_id == obj.id,
                                                              *filters)
                return {"licence": obj.vehicle.licence_plate,
                        "received": q.first()[0],
                        "accepted": q.filter(models.Hail.change_to_accepted_by_taxi != None).first()[0],
                        "accepted_customer": q.filter(
                            models.Hail.change_to_accepted_by_customer != None).first()[0],
                        "internal_id": obj.vehicle.internal_id if obj.vehicle.description else None
                       }
            return json.JSONEncoder.default(self, obj)
    hails_sorted = sorted(hails, key=lambda h: h.taxi_id)
    hails_grouped = [
        {"id": v[0], "hails": list(v[1]), "taxi": models.Taxi.query.get(v[0])}
                     for v in groupby(hails_sorted, key=lambda h: h.taxi_id)
    ]
    for taxi in taxis:
        if taxi.id not in [g["taxi"].id for g in hails_grouped]:
            hails_grouped.append({"id": taxi.id, "hails": [], "taxi": taxi})
    return jsonify({"data":
        json.loads(json.dumps(
            sorted(hails_grouped, key=lambda l: len(l["hails"]), reverse=True)[:20],
            cls=HailEncoder))})


@mod.route('/stats_hails')
@login_required
def stats():
    statuses = {
        "declined_by_taxi": {
            "timeout": ["timeout_taxi"],
            "declined": ["declined_by_taxi", "incident_taxi"]
        },
        "declined_by_customer": {
            "timeout": ["timeout_customer"],
            "declined": ["declined_by_customer", "incident_customer"]
        },
        "ok": {"ok": ["accepted_by_customer", "customer_on_board", "finished"]},
        "total": {"total": []}
    }
    user = None
    if current_user.has_role('admin'):
        parser = reqparse.RequestParser()
        parser.add_argument('user')
        args = parser.parse_args()
        if not 'user' in args:
            abort(400)
        user_list = [models.security.User.query.filter(models.security.User.email==args['user']).first(), None]
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
    begin_date = date.today() - timedelta(weeks=2)
    range_date = [(begin_date + timedelta(days=d)).isoformat() for d in
                  range(0, (date.today() - begin_date).days)]
    for user in user_list:
        email = user.email if user else 'total'
        filters = [models.Hail.added_at >= begin_date]
        if user and user.has_role('moteur'):
            filters += [models.Hail.added_by == user.id]
        if user and user.has_role('operateur'):
            filters += [models.Hail.operateur_id == user.id]
        res.append({"email": email})
        for key in status_keys:
            res[-1][key] = {}
            for substatus, status_list in statuses[key].iteritems():
                status_filters = [models.Hail._status != 'customer_banned']
                if status_list:
                    status_filters += [models.Hail._status.in_(status_list)]
                q = models.db.session.query(
                        func.date(models.Hail.added_at),
                        func.count('id')
                    ).select_from(models.Hail).filter(
                        *status_filters + filters
                    ).group_by(
                        func.date(models.Hail.added_at)
                    ).order_by(
                        func.date(models.Hail.added_at)
                )
		tmp = {k_v[0].isoformat(): k_v[1] for k_v in q.all()}
                res[-1][key][substatus] = {d: tmp.get(d, 0) for d in range_date}

            if len(res[-1][key].keys()) > 1:
                res[-1][key]['total'] = {
                    v[0]: sum(v[1:])
                        for v in zip(res[-1][key].values()[0].keys(),
                                 *map(lambda d: d.values(), res[-1][key].values()))
                }

    return jsonify({"data": res})
