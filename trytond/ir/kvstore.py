# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from ..model import ModelView, ModelSQL, fields
from .resource import ResourceMixin

__all__ = ['KeyValueStore']


class KeyValueStore(ResourceMixin, ModelSQL, ModelView):
    "Key Value Store"
    __name__ = 'ir.kvstore'

    key = fields.Char("Key", required=True)
    value = fields.JSON("Value")
