from flask import Blueprint

from .generic.logas import LogoutAsView

from APITaxi_models2 import User


blueprint = Blueprint('logout', __name__)


class Logout(LogoutAsView):
    user_model = User
    redirect_on_success = 'home.home'


blueprint.add_url_rule(
    '/logas/logout',
    view_func=Logout.as_view('logout'),
    methods=['POST']
)
