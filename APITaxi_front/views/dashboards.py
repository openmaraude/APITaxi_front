# -*- coding: utf-8 -*-

from flask import Blueprint, redirect, render_template, url_for
from flask_security import login_required


blueprint = Blueprint('dashboards', __name__)


@blueprint.route('/dashboards', methods=['GET'])
@login_required
def index():
    return render_template('dashboards/index.html')


@blueprint.route('/dashboards/hails', methods=['GET'])
@login_required
def hails():
    return render_template('dashboards/hails.html')


@blueprint.route('/dashboards/taxis', methods=['GET'])
@login_required
def taxis():
    return render_template('dashboards/taxis.html')
