from urllib.parse import urljoin

from flask import Blueprint, current_app, redirect, render_template
from flask_security import login_required


blueprint = Blueprint('documentation', __name__)


@blueprint.route('/documentation')
@login_required
def index():
    return render_template('documentation/index.html')


@blueprint.route('/documentation/interactive')
@login_required
def interactive():
    api_url = current_app.config.get('API_TAXI_URL', '')
    redirect_url = urljoin(api_url, 'doc/')
    return redirect('/doc/')


@blueprint.route('/documentation/search')
@login_required
def search():
    return render_template('documentation/search.html')


@blueprint.route('/documentation/operator')
@login_required
def operator():
    return render_template('documentation/operator.html')


@blueprint.route('/documentation/reference')
@login_required
def reference():
    return render_template('documentation/reference.html')


@blueprint.route('/documentation/examples')
@login_required
def examples():
    return render_template('documentation/examples.html')
