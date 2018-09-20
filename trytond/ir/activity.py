# -*- coding: utf-8 -*-
"""
    Activity

    :license: see LICENSE for details.
"""
from trytond.pool import PoolMeta, Pool
from trytond.model import ModelSQL, ModelView, fields

__metaclass__ = PoolMeta
__all__ = ['Activity']


class Activity(ModelSQL, ModelView):
    "Activity"
    __name__ = 'ir.activity'

    type = fields.Char('Type', select=True)
    object_record = fields.Reference(
        'Object Record', selection='get_models', select=True)
    target_record = fields.Reference(
        'Target Record', selection='get_models', select=True)

    @classmethod
    def get_models(cls):
        """
        Return all models
        """
        Model = Pool().get('ir.model')

        return map(lambda m: (m.model, m.name), Model.search([]))
