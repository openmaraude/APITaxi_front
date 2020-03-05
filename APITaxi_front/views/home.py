from flask import Blueprint, url_for, redirect
from flask_security import login_required


blueprint = Blueprint('home', __name__)


@blueprint.route('/')
@login_required
def home():
    return redirect(url_for('dashboards.index'))
