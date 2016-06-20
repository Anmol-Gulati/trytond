# This file is part of Tryton.  The COPYRIGHT file at the toplevel of this
# repository contains the full copyright notices and license terms.
from .field import Field, SQLType


class JSON(Field):
    'Define json field.'
    _type = 'text'

    def sql_type(self):
        return SQLType('JSON', 'JSON')
