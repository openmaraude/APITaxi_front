"""Administrative views"""

import datetime
import dateutil
import json

from flask import Blueprint, flash, render_template, request
from flask_security import login_required, roles_accepted

from sqlalchemy import cast, func, Date, literal_column, String, text
from sqlalchemy.dialects.postgresql import aggregate_order_by

from APITaxi_models import db, Hail


# Hails with this status are considered successful
SUCCESS_STATUS = (
    'finished',
    'customer_on_board',
)


blueprint = Blueprint('admin', __name__)


def str_to_datetime(value):
    return dateutil.parser.parse(value)

blueprint.add_app_template_filter(str_to_datetime)


@blueprint.route('/admin/hails')
@login_required
@roles_accepted('admin')
def list_hails():
    start = datetime.date.today().replace(day=1)

    # Parse ?start
    start_arg = request.args.get('start')
    if start_arg:
        try:
            value = datetime.datetime.strptime(start_arg, '%Y-%m-%d')
            start = value
        # Ignore bad dates
        except ValueError:
            flash('Start date format is invalid. The format should be : %Y-%m-%d')

    end = start + dateutil.relativedelta.relativedelta(months=+1, day=1)

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

    customers_requests = []
    for row in query:
        success = any(hail for hail in row.hails if hail['status'] in SUCCESS_STATUS)
        customers_requests.append({
            'success': success,
            'data': row,
        })

    return render_template(
        'admin/hails.html',
        success_status=SUCCESS_STATUS,
        customers_requests=customers_requests,
        start=start
    )
