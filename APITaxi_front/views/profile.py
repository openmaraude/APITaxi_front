# -*- coding: utf-8 -*-

import re

from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_security import login_required, current_user
from flask_security.utils import hash_password

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, ValidationError, validators

from APITaxi_models2 import db



blueprint = Blueprint('profile', __name__)


class ValidatePhoneNumber:
    def __call__(self, form, field):
        if not re.match(r'^[0-9+\.]+$', field.data):
            raise ValidationError('Numéro de téléphone invalide.')


class ProfileForm(FlaskForm):

    password = PasswordField(validators=[
        validators.EqualTo(
            'password_confirm',
            message='Le mot de passe et la confirmation ne correspondent pas.'
        )
    ])

    password_confirm = PasswordField()

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


class ValidateURL:
    def __call__(self, form, field):
        """wtforms URL validator refuses underscores, which we use in
        production."""
        if field.data.startswith('http://') or field.data.startswith('https://'):
            return
        raise ValidationError('URL invalide.')


class ProfileOperatorForm(ProfileForm):
    """Similar to ProfileForm, but with fields to store API endpoints.
    """
    hail_endpoint_production = StringField(validators=[
        validators.Optional(),
        ValidateURL()
    ])

    hail_endpoint_testing = StringField(validators=[
        validators.Optional(),
        ValidateURL()
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

    # For POST requests, form.data is the password previously submitted.
    # For GET requests, do not fill with the current value, which is the hashed
    # password.
    if request.method != 'POST':
        form.password.data = ''
        form.password_confirm.data = ''

    if form.validate_on_submit():
        # If password is not provided, do not use the field to populate_obj.
        if not form.password.data:
            del form.password
            del form.password_confirm
        else:
            form.password.data = hash_password(form.password.data)

        form.populate_obj(current_user)

        db.session.commit()
        return redirect(url_for('profile.edit'))

    return render_template('profile.html', user=current_user, form=form)
