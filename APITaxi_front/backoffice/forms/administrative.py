# -*- coding: utf-8 -*-
from APITaxi_utils.model_form import ModelForm
import APITaxi_models import models
from wtforms import HiddenField, SubmitField
from wtforms.fields import FormField
from wtforms_alchemy import ModelFormField
from wtforms.widgets import ListWidget
from wtforms.ext.sqlalchemy.fields import QuerySelectField

def departements():
    return models.Departement.query.all()

class ZUPCSimpleForm(ModelForm):
    class Meta:
        skip_unknown_types = True
        model = models.ZUPC
    exclude = ['shape']

class ZUPCForm(ZUPCSimpleForm):
    departement = QuerySelectField(query_factory=departements, get_label='nom')


class ZUPCreateForm(ZUPCForm):
    submit = SubmitField(u'Créer')


class ZUPCUpdateForm(ZUPCForm):
    id = HiddenField()          
    submit = SubmitField(u'Modifier')


