# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, url_for, jsonify
from flask_security import login_required, current_user
from APITaxi_utils import request_wants_json
from APITaxi_models.security import User
from APITaxi_models.hail import Hail
from datetime import datetime, timedelta
from itertools import groupby
import json
from geopy.distance import vincenty

class HailEncoder(json.JSONEncoder):
    def default(self, obj):
        if not isinstance(obj, Hail):
            return json.JSONEncoder.default(self, obj)
        return [obj.id, obj.status,
               vincenty(obj.customer_lat, obj.customer_lon,
                       obj.initial_taxi_lat, obj.initial_taxi_lon).meters]


mod = Blueprint('home_bo', __name__)

@mod.route('/')
@login_required
def home():
    if current_user.has_role('admin'):
        user_list = [u for u in User.query.all() if "operateur" in u.roles]
    elif current_user.has_role('operateur'):
        user_list = [current_user]
    else:
        user_list = []
    users = {}
    for user in user_list:
        hails = Hail.query.filter(
                            Hail.added_by == user.id,
                            Hail.added_at >= datetime.now() - timedelta(weeks=21),
                            Hail._status.in_(['timeout_taxi', 'declined_by_taxi'])
        ).all()
        hails_sorted = sorted(hails, key=lambda h: h.taxi_id)
        hails_grouped = [(v[0], list(v[1])) for v in groupby(hails_sorted, key=lambda h: h.taxi_id)]
        users[user.email] = sorted(hails_grouped, key=lambda l: len(l[1]), reverse=True)
    return render_template('index.html',
                          user_name_list=[u.email for u in user_list],
                          user_json=json.dumps(users, cls=HailEncoder),
                          is_admin=current_user.has_role('admin'))
