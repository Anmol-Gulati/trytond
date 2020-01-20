# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from sql import Null
from sql.operators import Concat

from ..model import ModelView, ModelSQL, fields
from ..transaction import Transaction
from ..pyson import Eval
from .resource import ResourceMixin
from ..config import config

__all__ = [
    'Attachment',
    ]


def firstline(description):
    try:
        return next((x for x in description.splitlines() if x.strip()))
    except StopIteration:
        return ''

if config.getboolean('attachment', 'filestore', default=True):
    file_id = 'file_id'
    store_prefix = config.get('attachment', 'store_prefix', default=None)
else:
    file_id = None
    store_prefix = None


class Attachment(ResourceMixin, ModelSQL, ModelView):
    "Attachment"
    __name__ = 'ir.attachment'
    name = fields.Char('Name', required=True)
    kind = fields.Selection([
        ('data', 'Data'),
        ('link', 'Link'),
        ], 'Kind', required=True)
    description = fields.Text('Description')
    summary = fields.Function(fields.Char('Summary'), 'on_change_with_summary')
    link = fields.Char('Link', states={
            'invisible': Eval('kind') != 'link',
            }, depends=['kind'])
    data = fields.Binary('Data', filename='name',
        file_id=file_id, store_prefix=store_prefix,
        states={
            'invisible': Eval('kind') != 'data',
            }, depends=['kind'])
    file_id = fields.Char('File ID', readonly=True)
    data_size = fields.Function(fields.Integer('Data size', states={
                'invisible': Eval('kind') != 'data',
                }, depends=['kind']), 'get_size')


    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._order.insert(0, ('create_date', 'DESC'))

    @classmethod
    def __register__(cls, module_name):
        cursor = Transaction().connection.cursor()
        table = cls.__table_handler__(module_name)
        if not table.column_exist('kind'):
            table.column_rename('type', 'kind')

        super(Attachment, cls).__register__(module_name)

        attachment = cls.__table__()

        # Migration from 4.0: merge digest and collision into file_id
        if table.column_exist('digest') and table.column_exist('collision'):
            cursor.execute(*attachment.update(
                    [attachment.file_id],
                    [attachment.digest],
                    where=(attachment.collision == 0)
                    | (attachment.collision == Null)))
            cursor.execute(*attachment.update(
                    [attachment.file_id],
                    [Concat(Concat(attachment.digest, '-'),
                            attachment.collision)],
                    where=(attachment.collision != 0)
                    & (attachment.collision != Null)))
            table.drop_column('digest')
            table.drop_column('collision')

        # Migration from 4.8: remove unique constraint
        table.drop_constraint('resource_name')

    @staticmethod
    def default_kind():
        return 'data'

    def get_size(self, name):
        with Transaction().set_context({
                    '%s.%s' % (self.__name__, name): 'size',
                    }):
            record = self.__class__(self.id)
            return record.data

    @fields.depends('description')
    def on_change_with_summary(self, name=None):
        return firstline(self.description or '')
