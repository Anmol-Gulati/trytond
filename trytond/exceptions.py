# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.


class TrytonException(Exception):
    pass


class UserError(TrytonException):

    def __init__(self, message, description=''):
        super(UserError, self).__init__('UserError', (message, description))
        self.message = message
        self.description = description
        self.code = 1

    def __str__(self):
        return '%s - %s' % (self.message, self.description)


class UserValueError(UserError):
    '''
    Raised when there is a data error or a validation fails for api calls. 
    Makes handling easy over API dispatcher
    '''
    pass


class UserWarning(TrytonException):

    def __init__(self, name, message, description=''):
        super(UserWarning, self).__init__('UserWarning', (name, message,
                description))
        self.name = name
        self.message = message
        self.description = description
        self.code = 2

    def __str__(self):
        return '%s - %s' % (self.message, self.description)


class LoginException(TrytonException):
    """Request the named parameter for the login process.
    The type can be 'password' or 'char'.
    """

    def __init__(self, name, message, type='password'):
        super(LoginException, self).__init__(
            'LoginException', (name, message, type))
        self.name = name
        self.message = message
        self.type = type
        self.code = 3


class ConcurrencyException(TrytonException):

    def __init__(self, message, record=None, write_date=None, write_uid=None):
        super(ConcurrencyException, self).__init__('ConcurrencyException',
            (message, record, write_date, write_uid))
        self.message = message
        self.code = 4
        self.record = record
        self.write_date = write_date
        self.write_uid = write_uid

    def __str__(self):
        return self.message


class FieldNameError(UserError):
    def __init__(self, field_name):
        super(FieldNameError, self).__init__(
            field_name,
            "Field does not exist or you do not have permission to access."
        )

    def __str__(self):
        return self.message


class RateLimitException(TrytonException):
    """User has sent too many requests in a given amount of time."""


class MissingDependenciesException(TrytonException):

    def __init__(self, missings):
        self.missings = missings

    def __str__(self):
        return 'Missing dependencies: %s' % ' '.join(self.missings)
