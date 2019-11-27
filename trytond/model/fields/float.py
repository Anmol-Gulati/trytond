# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from .field import Field
from ...pyson import PYSON


def digits_validate(value):
    if value:
        assert isinstance(value, tuple), 'digits must be a tuple'
        for i in value:
            assert isinstance(i, (int, PYSON)), \
                'digits must be tuple of integers or PYSON'
            if isinstance(i, PYSON):
                assert i.types().issubset(set([int, int])), \
                    'PYSON digits must return an integer'


class Float(Field):
    '''
    Define a float field (``float``).
    '''
    _type = 'float'
    _sql_type = 'FLOAT'

    def __init__(self, string='', digits=None, help='', required=False,
            readonly=False, domain=None, states=None, select=False,
            on_change=None, on_change_with=None, depends=None,
            context=None, loading='eager', uom_symbol=None):
        '''
        :param digits: a list of two integers defining the total
            of digits and the number of decimals of the float.
        :param uom_symbol: a valid PYSON object which resolves to str
        '''
        super(Float, self).__init__(string=string, help=help,
            required=required, readonly=readonly, domain=domain, states=states,
            select=select, on_change=on_change, on_change_with=on_change_with,
            depends=depends, context=context, loading=loading)
        self.__uom_symbol = None
        self.uom_symbol = uom_symbol
        self.__digits = None
        self.digits = digits

    __init__.__doc__ += Field.__init__.__doc__

    def _get_digits(self):
        return self.__digits

    def _set_digits(self, value):
        digits_validate(value)
        self.__digits = value

    digits = property(_get_digits, _set_digits)

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
        return float(value)
