# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import datetime
from sql.functions import Function

from ... import backend
from .field import Field
from trytond.exceptions import UserValueError


class SQLite_Date(Function):
    __slots__ = ()
    _function = 'DATE'


class SQLite_DateTime(Function):
    __slots__ = ()
    _function = 'DATETIME'


class SQLite_Time(Function):
    __slots__ = ()
    _function = 'TIME'


class Date(Field):
    '''
    Define a date field (``date``).
    '''
    _type = 'date'
    _sql_type = 'DATE'

    def sql_format(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                year, month, day = list(map(int, value.split("-", 2)))
            except ValueError:
                raise UserValueError(
                    'Invalid date formatting. Expected yyyy-mm-dd.'
                )
            try:
                return datetime.date(year, month, day)
            except ValueError as error:
                raise UserValueError(error)

        if (not isinstance(value, datetime.date)
                # Allow datetime with min time for XML-RPC
                # datetime must be tested separately because datetime is a
                # subclass of date
                or (isinstance(value, datetime.datetime)
                    and value.time() != datetime.time())):
            raise UserValueError(
                'Invalid value for datetime. It should use fulfil encoding.'
            )
        return value

    def sql_cast(self, expression):
        if backend.name() == 'sqlite':
            return SQLite_Date(expression)
        return super(Date, self).sql_cast(expression)


class DateTime(Field):
    '''
    Define a datetime field (``datetime``).
    '''
    _type = 'datetime'
    _sql_type = 'DATETIME'

    def __init__(self, string='', format='%H:%M:%S', help='', required=False,
            readonly=False, domain=None, states=None, select=False,
            on_change=None, on_change_with=None, depends=None,
            context=None, loading='eager'):
        '''
        :param format: The validation format as used by strftime.
        '''
        super(DateTime, self).__init__(string=string, help=help,
            required=required, readonly=readonly, domain=domain, states=states,
            select=select, on_change=on_change, on_change_with=on_change_with,
            depends=depends, context=context, loading=loading)
        self.format = format

    __init__.__doc__ += Field.__init__.__doc__

    def sql_format(self, value):
        if not value:
            return None
        if isinstance(value, str):
            try:
                if 'T' in value:
                    datepart, timepart = value.split("T")
                else:
                    datepart, timepart = value.split(" ")
                year, month, day = list(map(int, datepart.split("-", 2)))
                hours, minutes, seconds = list(map(int, timepart.split(":")))
                return datetime.datetime(year, month, day, hours, minutes, seconds)
            except ValueError as error:
                message = 'Invalid value for datetime: {}'.format(str(error))
                raise UserValueError(message)
        if not isinstance(value, datetime.datetime):
            raise UserValueError(
                'Invalid value for datetime. It should use fulfil encoding.'
            )
        return value.replace(microsecond=0)

    def sql_cast(self, expression):
        if backend.name() == 'sqlite':
            return SQLite_DateTime(expression)
        return super(DateTime, self).sql_cast(expression)


class Timestamp(Field):
    '''
    Define a timestamp field (``datetime``).
    '''
    _type = 'timestamp'
    _sql_type = 'TIMESTAMP'
    format = '%H:%M:%S.%f'

    def sql_format(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            datepart, timepart = value.split(" ")
            year, month, day = list(map(int, datepart.split("-", 2)))
            timepart_full = timepart.split(".", 1)
            hours, minutes, seconds = list(map(int, timepart_full[0].split(":")))
            if len(timepart_full) == 2:
                microseconds = int(timepart_full[1])
            else:
                microseconds = 0
            try:
                return datetime.datetime(
                    year, month, day, hours, minutes, seconds, microseconds
                )
            except ValueError as error:
                message = 'Invalid value for timestamp: {}'.format(str(error))
                raise UserValueError(message)
        if not isinstance(value, datetime.datetime):
            raise UserValueError(
                'Invalid value for timestamp. It should use fulfil encoding.'
            )
        return value


class Time(DateTime):
    '''
    Define a time field (``time``).
    '''
    _type = 'time'
    _sql_type = 'TIME'

    def sql_format(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                hours, minutes, seconds = list(map(int, value.split(":")))
                return datetime.time(hours, minutes, seconds)
            except ValueError as error:
                message = 'Invalid value for time: {}'.format(str(error))
                raise UserValueError(message)
        if not isinstance(value, datetime.time):
            raise UserValueError(
                'Invalid value for time. It should use fulfil encoding.'
            )
        return value.replace(microsecond=0)

    def sql_cast(self, expression):
        if backend.name() == 'sqlite':
            return SQLite_Time(expression)
        return super(Time, self).sql_cast(expression)


class TimeDelta(Field):
    '''
    Define a timedelta field (``timedelta``).
    '''
    _type = 'timedelta'
    _sql_type = 'INTERVAL'

    def __init__(self, string='', converter=None, help='', required=False,
            readonly=False, domain=None, states=None, select=False,
            on_change=None, on_change_with=None, depends=None,
            context=None, loading='eager'):
        '''
        :param converter: The name of the context key containing
            the time converter.
        '''
        super(TimeDelta, self).__init__(string=string, help=help,
            required=required, readonly=readonly, domain=domain, states=states,
            select=select, on_change=on_change, on_change_with=on_change_with,
            depends=depends, context=context, loading=loading)
        self.converter = converter

    def sql_format(self, value):
        if value is None:
            return None
        if not isinstance(value, datetime.timedelta):
            raise UserValueError(
                'Invalid value for timedelta. It should use fulfil encoding.'
            )
        return super(TimeDelta, self).sql_format(value)

    @classmethod
    def get(cls, ids, model, name, values=None):
        result = {}
        for row in values:
            value = row[name]
            if (value is not None
                    and not isinstance(value, datetime.timedelta)):
                if value >= datetime.timedelta.max.total_seconds():
                    value = datetime.timedelta.max
                elif value <= datetime.timedelta.min.total_seconds():
                    value = datetime.timedelta.min
                else:
                    value = datetime.timedelta(seconds=value)
                result[row['id']] = value
            else:
                result[row['id']] = value
        return result
