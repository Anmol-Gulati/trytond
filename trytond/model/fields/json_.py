# This file is part of Tryton.  The COPYRIGHT file at the toplevel of this
# repository contains the full copyright notices and license terms.
from sql.operators import BinaryOperator

from .field import Field, SQLType, SQL_OPERATORS


class JSONText(BinaryOperator):
    __slots__ = ()
    _operator = '->>'


class JSON(Field):
    'Define json field.'
    _type = 'text'

    def sql_type(self):
        return SQLType('JSON', 'JSON')

    def convert_domain(self, domain, tables, Model):
        table, _ = tables[None]
        name, operator, value = domain[:3]
        column = self.sql_column(table)
        if '.' not in name:
            return super(JSON, self).convert_domain(domain, tables, Model)
        else:
            _, target_name = name.split('.', 1)
            return SQL_OPERATORS[operator](
                JSONText(column, target_name), value
            )
