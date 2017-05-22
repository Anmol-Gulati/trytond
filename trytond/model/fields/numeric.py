# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal
from sql import Query, Expression, Cast, Literal, Select, CombiningQuery, As

from ... import backend
from .field import SQLType
from .float import Float
from ...pyson import PYSON


class SQLite_Cast(Cast):

    def as_(self, output_name):
        # Use PARSE_COLNAMES instead of CAST for final column
        return As(self.expression, '%s [NUMERIC]' % output_name)

def currency_symbol_validate(value):
    if value:
        assert isinstance(value, PYSON), 'value must be a PYSON'

class Numeric(Float):
    '''
    Define a numeric field (``decimal``).
    '''
    _type = 'numeric'

    def __init__(self, string='', digits=None, help='', required=False,
            readonly=False, domain=None, states=None, select=False,
            on_change=None, on_change_with=None, depends=None,
            context=None, loading='eager', currency_symbol=None):
        '''
        :param currency_symbol: a list of two integers defining the total
            of digits and the number of decimals of the float.
        '''
        super(Numeric, self).__init__(string=string, digits=digits, help=help,
            required=required, readonly=readonly, domain=domain, states=states,
            select=select, on_change=on_change, on_change_with=on_change_with,
            depends=depends, context=context, loading=loading)
        self.__currency_symbol = None
        self.currency_symbol = currency_symbol

    __init__.__doc__ += Float.__init__.__doc__

    def _get_currency_symbol(self):
        return self.__currency_symbol

    def _set_currency_symbol(self, value):
        currency_symbol_validate(value)
        self.__currency_symbol = value

    currency_symbol = property(_get_currency_symbol, _set_currency_symbol)

    @staticmethod
    def sql_format(value):
        if isinstance(value, (Query, Expression)):
            return value
        if value is None:
            return None
        if isinstance(value, (int, long)):
            value = Decimal(str(value))
        assert isinstance(value, Decimal)
        return value

    def sql_type(self):
        db_type = backend.name()
        if db_type == 'mysql':
            return SQLType('DECIMAL', 'DECIMAL(65, 30)')
        return SQLType('NUMERIC', 'NUMERIC')

    def sql_column(self, table):
        column = super(Numeric, self).sql_column(table)
        db_type = backend.name()
        if db_type == 'sqlite':
            # Must be casted as Decimal is stored as bytes
            column = SQLite_Cast(column, self.sql_type().base)
        return column

    def _domain_value(self, operator, value):
        value = super(Numeric, self)._domain_value(operator, value)
        db_type = backend.name()
        if db_type == 'sqlite':
            if isinstance(value, (Select, CombiningQuery)):
                return value
            # Must be casted as Decimal is adapted to bytes
            type_ = self.sql_type().base
            if operator in ('in', 'not in'):
                return [Cast(Literal(v), type_) for v in value]
            elif value is not None:
                return Cast(Literal(value), type_)
        return value
