# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import itertools
import json

import dateutil

from flask import abort, Blueprint, flash, redirect, render_template, request, url_for
from flask_security import current_user, login_required, roles_accepted

from sqlalchemy import cast, Date, func, literal_column, or_
from sqlalchemy.dialects.postgresql import aggregate_order_by

import redis

from APITaxi_models import db, Hail
from APITaxi_models.security import User

from .. import redis_client


blueprint = Blueprint('dashboards', __name__)


@blueprint.route('/dashboards', methods=['GET'])
@login_required
def index():
    return render_template('dashboards/index.html')


@blueprint.route('/dashboards/hails', methods=['GET'])
@login_required
@roles_accepted('admin', 'moteur', 'operateur')
def hails():
    """View is calling the endpoint /api/hails to display data."""
    # All the dates for which we generate counters
    dates = db.session.query(
        func.generate_series(
            func.NOW() - timedelta(days=15),
            func.NOW(),
            timedelta(days=1)
        ).label('date')
    ).subquery()

    # For each date, count the number of different Hail status.
    # Result: one row per date/status
    query = db.session.query(
        cast(dates.c.date, Date).label('date'),
        Hail._status,
        func.COUNT(Hail.id).label('count')
    ).outerjoin(
        Hail, cast(Hail.added_at, Date) == cast(dates.c.date, Date)
    ).filter(
        or_(Hail.id.is_(None),
            Hail.operateur_id == current_user.id,
            Hail.added_by == current_user.id)
    ).group_by(
        cast(dates.c.date, Date),
        Hail._status
    ).order_by(
        cast(dates.c.date, Date)
    )

    # Use itertools.groupby to build a dictionary such as:
    #
    #  {
    #     '<date>': {
    #       '<status_name>': <count>,
    #       ...
    #     },
    #     ...
    #  }
    stats = {
        date.strftime('%d-%m-%Y'): {
            row._status: row.count
            for row in groups if row._status
        }
        for date, groups in itertools.groupby(query.all(), lambda row: row.date)
    }

    # All unique different status found in stats
    all_status = set(itertools.chain(*[list(group.keys()) for group in stats.values()]))

    return render_template('dashboards/hails.html', status_stats=stats, all_status=all_status)


@blueprint.route('/dashboards/hails/<string:hail_id>')
@login_required
@roles_accepted('admin', 'moteur', 'operateur')
def hails_details(hail_id):
    hail = Hail.query.get(hail_id)

    if not (current_user.has_role('admin') or current_user.id in (hail.operateur_id, hail.added_by)):
        abort(403)

    try:
        resp = redis_client.zrangebyscore('hail:%s' % hail_id, '-inf', '+inf', withscores=True)
    except redis.exceptions.ConnectionError:
        redis_error = True
        logs = []
    else:
        redis_error = False
        logs = [
            (datetime.fromtimestamp(date), json.loads(value.decode('utf8')))
            for value, date in resp
        ]

    return render_template('dashboards/hails_details.html', hail=hail, logs=logs, redis_error=redis_error)


@blueprint.route('/dashboards/hails_by_user')
@login_required
@roles_accepted('admin')
def hails_by_user():
    date = datetime.now()
    if request.args.get('date'):
        try:
            date = datetime.strptime(request.args.get('date'), '%Y-%m-%d')
        except ValueError:
            flash("Argument date invalide. Affichage des courses d'aujourd'hui.")

    start = date.date()
    end = start + dateutil.relativedelta.relativedelta(days=+1)

    # For each client (== phone number) and day, get all the hails
    query = Hail.query.with_entities(
        cast(Hail.added_at, Date).label('date'),
        Hail.customer_phone_number.label('phone'),
        func.JSON_AGG(
            aggregate_order_by(
                literal_column('"' + Hail.__tablename__ + '"'),
                Hail.added_at
            )
        ).label('hails')
    ).filter(
        cast(Hail.added_at, Date) >= start,
        cast(Hail.added_at, Date) < end,
    ).group_by(
        Hail.customer_phone_number,
        cast(Hail.added_at, Date)
    ).order_by(
        cast(Hail.added_at, Date).desc()
    )

    # Hails with this status are considered successful
    SUCCESS_STATUS = (
        'finished',
        'customer_on_board',
    )

    customers_requests = []
    for row in query:
        success = any(hail for hail in row.hails if hail['status'] in SUCCESS_STATUS)

        # For each hail, fetch operator details.
        #
        # SQL query is only run on database of the operator is not already in
        # the SQLAlchemy session's identity map, so this loop is not as
        # expensive as it could appear.
        for idx, hail in enumerate(row.hails):
            hail['operator'] = User.query.get(hail['operateur_id'])
            hail['added'] = User.query.get(hail['added_by'])

        customers_requests.append({
            'success': success,
            'data': row,
        })

    return render_template(
        'dashboards/hails_by_user.html',
        success_status=SUCCESS_STATUS,
        customers_requests=customers_requests,
        start=start, end=end
    )


@blueprint.route('/dashboards/taxis', methods=['GET'])
@login_required
@roles_accepted('admin', 'moteur', 'operateur')
def taxis():
    """View is calling the endpoint /api/taxis to display data."""
    return render_template('dashboards/taxis.html')
