from urllib.parse import urljoin

from flask import Blueprint, current_app, redirect, render_template


blueprint = Blueprint('documentation', __name__)


@blueprint.route('/documentation')
def index():
    return render_template('documentation/index.html')


@blueprint.route('/documentation/search')
def search():
    return render_template('documentation/search.html')


@blueprint.route('/documentation/operator')
def operator():
    return render_template('documentation/operator.html')


@blueprint.route('/documentation/reference')
def reference():
    # In production, swagger is available https://api.taxi/doc or
    # https://dev.api.taxi/doc.
    # When developing locally, SWAGGER_URL should be set in settings.py.
    api_url = current_app.config.get(
        'SWAGGER_URL',
        current_app.config.get('API_TAXI_URL', '')
    )
    redirect_url = urljoin(api_url, 'doc/')
    return redirect(redirect_url)


@blueprint.route('/documentation/examples')
def examples():
    return render_template('documentation/examples.html')
