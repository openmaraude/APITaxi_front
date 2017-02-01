# -*- coding: utf-8 -*-
from APITaxi_utils.model_form import ModelForm
from APITaxi_models import models
from wtforms import HiddenField, SubmitField, StringField, FormField
from wtforms.ext.sqlalchemy.fields import QuerySelectField


class modelsDescriptionForm(ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(ModelForm, self).__init__(*args, **kwargs)
    class Meta:
        model = models.modelsDescription
        exclude = ['added_at', 'added_via', 'source', 'last_update_at']
    model = StringField(label=models.Model.name.info['label'],
                        description=models.Model.name.description)
    constructor = StringField(label=models.Constructor.name.info['label'],
                              description=models.Constructor.name.description)


class modelsForm(ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(ModelForm, self).__init__(*args, **kwargs)
    class Meta:
        model = models.models


class ADSForm(ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(ModelForm, self).__init__(*args, **kwargs)
    class Meta:
        model = models.ADS
        exclude = ['added_at', 'added_via', 'source', 'last_update_at']

class ADSFormmodels(ModelForm):
    models = FormField(modelsForm)
    models_description = FormField(modelsDescriptionForm)
    ads = FormField(ADSForm)

class ADSCreateForm(ADSFormmodels):
    submit = SubmitField(u'Créer')


class ADSUpdateForm(ADSFormmodels):
    id = HiddenField()
    submit = SubmitField("Modifier")


def departements():
    return models.Departement.query.all()

class DriverForm(ModelForm):
    class Meta:
        model = models.Driver
        exclude = ['added_at', 'added_via', 'source', 'last_update_at']

    departement = QuerySelectField(query_factory=departements, get_label='nom')


class DriverCreateForm(DriverForm):
    submit = SubmitField(u'Créer')


class DriverUpdateForm(DriverForm):
    id = HiddenField()
    submit = SubmitField(u'Modifier')
