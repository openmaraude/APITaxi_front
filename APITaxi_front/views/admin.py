from flask import Blueprint, redirect, url_for
from flask_security import login_required, roles_accepted

from APITaxi_models2 import User

from .generic.logas import LogAsView


blueprint = Blueprint('admin', __name__)


@blueprint.route('/admin', methods=['GET'])
@login_required
@roles_accepted('admin')
def index():
    return redirect(url_for('admin.logas'))


class AdminLogAs(LogAsView):
    """Logas view for administrators. We allow to login as any user, so there
    is no filter on the users_model.
    """
    decorators = [
        login_required,
        roles_accepted('admin')
    ]

    template_name = 'admin/logas.html'
    user_model = User
    redirect_on_success = 'home.home'


blueprint.add_url_rule(
    '/admin/logas',
    view_func=AdminLogAs.as_view('logas'),
    methods=['GET', 'POST']
)
