# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal
from sql import Cast, Literal, Select, CombiningQuery, As

from ... import backend
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
    _sql_type = 'NUMERIC'

    def __init__(self, string='', digits=None, help='', required=False,
            readonly=False, domain=None, states=None, select=False,
            on_change=None, on_change_with=None, depends=None,
            context=None, loading='eager', currency_symbol=None,
            uom_symbol=None):
        '''
        :param currency_symbol: a valid PYSON object which resolves to str
        :param uom_symbol: a valid PYSON object which resolves to str
        '''
        super(Numeric, self).__init__(string=string, digits=digits, help=help,
            required=required, readonly=readonly, domain=domain, states=states,
            select=select, on_change=on_change, on_change_with=on_change_with,
            depends=depends, context=context, loading=loading)
        self.__currency_symbol = None
        self.currency_symbol = currency_symbol
        self.__uom_symbol = None
        self.uom_symbol = uom_symbol

    __init__.__doc__ += Float.__init__.__doc__

    def _get_currency_symbol(self):
        return self.__currency_symbol

    def _set_currency_symbol(self, value):
        currency_symbol_validate(value)
        self.__currency_symbol = value

    currency_symbol = property(_get_currency_symbol, _set_currency_symbol)

    def _get_uom_symbol(self):
        return self.__uom_symbol

    def _set_uom_symbol(self, value):
        if value:
            assert isinstance(value, PYSON), 'value must be a PYSON'
        self.__uom_symbol = value

    uom_symbol = property(_get_uom_symbol, _set_uom_symbol)

    def sql_format(self, value):
        if value is None:
            return None
        if isinstance(value, int):
            value = Decimal(str(value))
        value = Decimal(value)
        return value

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
