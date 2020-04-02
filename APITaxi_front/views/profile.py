# -*- coding: utf-8 -*-

import re

from flask import (
    Blueprint,
    redirect,
    render_template,
    url_for,
)
from flask_security import login_required, current_user

from flask_wtf import FlaskForm
from wtforms import StringField, ValidationError, validators

from APITaxi_models import db



blueprint = Blueprint('profile', __name__)


class ValidatePhoneNumber:
    def __call__(self, form, field):
        if not re.match(r'^[0-9+\.]+$', field.data):
            raise ValidationError('Numéro de téléphone invalide.')


class ProfileForm(FlaskForm):
    commercial_name = StringField(validators=[
        validators.Optional()
    ])

    phone_number_technical = StringField(validators=[
        validators.Optional(),
        ValidatePhoneNumber()
    ])

    email_technical = StringField(validators=[
        validators.Optional(),
        validators.Email('Email invalide.')
    ])

    phone_number_customer = StringField(validators=[
        validators.Optional(),
        ValidatePhoneNumber()
    ])

    email_customer = StringField(validators=[
        validators.Optional(),
        validators.Email('Email invalide.')
    ])


class ProfileOperatorForm(ProfileForm):
    """Similar to ProfileForm, but with fields to store API endpoints.
    """
    hail_endpoint_production = StringField(validators=[
        validators.Optional(),
        validators.URL('URL invalide.')
    ])

    hail_endpoint_testing = StringField(validators=[
        validators.Optional(),
        validators.URL('URL invalide.')
    ])

    operator_header_name = StringField(validators=[
        validators.Optional(),
    ])

    operator_api_key = StringField(validators=[
        validators.Optional(),
    ])


@blueprint.route('/profile', methods=['GET', 'POST'])
@login_required
def edit():
    if current_user.has_role('operateur'):
        form = ProfileOperatorForm(obj=current_user)
    else:
        form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        form.populate_obj(current_user)
        db.session.commit()
        return redirect(url_for('profile.edit'))

    return render_template('profile.html', user=current_user, form=form)
