# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import os
from collections import defaultdict
from functools import partial
from lxml import etree

from sql import Null

from ..model.modelview import _inherit_apply
from ..model import ModelView, ModelStorage, ModelSQL, DeactivableMixin, fields
from ..tools import file_open
from ..pyson import PYSONDecoder, PYSON, Eval
from ..transaction import Transaction
from ..pool import Pool
from ..cache import Cache
from ..rpc import RPC

__all__ = [
    'Action', 'ActionKeyword', 'ActionReport',
    'ActionActWindow', 'ActionActWindowView', 'ActionActWindowDomain',
    'ActionWizard', 'ActionURL',
    ]

EMAIL_REFKEYS = set(('cc', 'to', 'subject'))


class Action(DeactivableMixin, ModelSQL, ModelView):
    "Action"
    __name__ = 'ir.action'
    name = fields.Char('Name', required=True, translate=True)
    type = fields.Char('Type', required=True, readonly=True)
    usage = fields.Char('Usage')
    keywords = fields.One2Many('ir.action.keyword', 'action',
            'Keywords')
    groups = fields.Many2Many('ir.action-res.group', 'action', 'group',
            'Groups')
    icon = fields.Many2One('ir.ui.icon', 'Icon')

    @classmethod
    def __setup__(cls):
        super(Action, cls).__setup__()
        cls.__rpc__.update({
                'get_action_id': RPC(),
                })

    @staticmethod
    def default_usage():
        return None

    @classmethod
    def write(cls, actions, values, *args):
        pool = Pool()
        super(Action, cls).write(actions, values, *args)
        pool.get('ir.action.keyword')._get_keyword_cache.clear()

    @classmethod
    def get_action_id(cls, action_id):
        pool = Pool()
        with Transaction().set_context(active_test=False):
            if cls.search([
                        ('id', '=', action_id),
                        ]):
                return action_id
            for action_type in (
                    'ir.action.report',
                    'ir.action.act_window',
                    'ir.action.wizard',
                    'ir.action.url',
                    ):
                Action = pool.get(action_type)
                actions = Action.search([
                    ('id', '=', action_id),
                    ])
                if actions:
                    action, = actions
                    return action.action.id

    @classmethod
    def get_action_values(cls, type_, action_ids):
        Action = Pool().get(type_)
        columns = set(Action._fields.keys())
        columns.add('icon.rec_name')
        to_remove = ()
        if type_ == 'ir.action.report':
            to_remove = ('report_content_custom', 'report_content')
        elif type_ == 'ir.action.act_window':
            to_remove = ('domain', 'context', 'search_value')
        columns.difference_update(to_remove)
        return Action.read(action_ids, list(columns))


class ActionKeyword(ModelSQL, ModelView):
    "Action keyword"
    __name__ = 'ir.action.keyword'
    keyword = fields.Selection([
            ('tree_open', 'Open tree'),
            ('form_print', 'Print form'),
            ('form_action', 'Action form'),
            ('form_relate', 'Form relate'),
            ('graph_open', 'Open Graph'),
            ], string='Keyword', required=True)
    model = fields.Reference('Model', selection='models_get')
    sequence = fields.Integer('Sequence', select=True, required=True)
    action = fields.Many2One('ir.action', 'Action',
        ondelete='CASCADE', select=True)
    groups = fields.Function(fields.One2Many('res.group', None, 'Groups'),
        'get_groups', searcher='search_groups')
    _get_keyword_cache = Cache('ir_action_keyword.get_keyword')

    @staticmethod
    def default_sequence():
        return 10

    @classmethod
    def __setup__(cls):
        super(ActionKeyword, cls).__setup__()
        cls.__rpc__.update({'get_keyword': RPC()})
        cls._order.insert(0, ('sequence', 'ASC'))
        cls._error_messages.update({
                'wrong_wizard_model': ('Wrong wizard model in keyword action '
                    '"%s".'),
                })

    @classmethod
    def __register__(cls, module_name):
        super(ActionKeyword, cls).__register__(module_name)

        table = cls.__table_handler__(module_name)
        table.index_action(['keyword', 'model'], 'add')

    def get_groups(self, name):
        return [g.id for g in self.action.groups]

    @classmethod
    def search_groups(cls, name, clause):
        return [('action.' + clause[0],) + tuple(clause[1:])]

    @classmethod
    def validate(cls, actions):
        super(ActionKeyword, cls).validate(actions)
        for action in actions:
            action.check_wizard_model()

    def check_wizard_model(self):
        ActionWizard = Pool().get('ir.action.wizard')
        if self.action.type == 'ir.action.wizard':
            action_wizards = ActionWizard.search([
                ('action', '=', self.action.id),
                ], limit=1)
            # could be empty when copying an action
            if action_wizards:
                action_wizard, = action_wizards
                if action_wizard.model:
                    if not str(self.model).startswith(
                            '%s,' % action_wizard.model):
                        self.raise_user_error('wrong_wizard_model', (
                                action_wizard.rec_name,))

    @staticmethod
    def _convert_vals(vals):
        vals = vals.copy()
        pool = Pool()
        Action = pool.get('ir.action')
        if 'action' in vals:
            vals['action'] = Action.get_action_id(vals['action'])
        return vals

    @staticmethod
    def models_get():
        pool = Pool()
        Model = pool.get('ir.model')
        return [(m.model, m.name) for m in Model.search([])]

    @classmethod
    def delete(cls, keywords):
        ModelView._fields_view_get_cache.clear()
        ModelView._view_toolbar_get_cache.clear()
        cls._get_keyword_cache.clear()
        super(ActionKeyword, cls).delete(keywords)

    @classmethod
    def create(cls, vlist):
        ModelView._fields_view_get_cache.clear()
        ModelView._view_toolbar_get_cache.clear()
        cls._get_keyword_cache.clear()
        new_vlist = []
        for vals in vlist:
            new_vlist.append(cls._convert_vals(vals))
        return super(ActionKeyword, cls).create(new_vlist)

    @classmethod
    def write(cls, keywords, values, *args):
        actions = iter((keywords, values) + args)
        args = []
        for keywords, values in zip(actions, actions):
            args.extend((keywords, cls._convert_vals(values)))
        super(ActionKeyword, cls).write(*args)
        ModelView._fields_view_get_cache.clear()
        ModelView._view_toolbar_get_cache.clear()
        cls._get_keyword_cache.clear()

    @classmethod
    def get_keyword(cls, keyword, value):
        Action = Pool().get('ir.action')
        key = (keyword, tuple(value), Transaction().user)
        keywords = cls._get_keyword_cache.get(key)
        if keywords is not None:
            return keywords
        keywords = []
        model, model_id = value

        clause = [
            ('keyword', '=', keyword),
            ('model', '=', model + ',-1'),
            ]
        if model_id >= 0:
            clause = ['OR',
                clause,
                [
                    ('keyword', '=', keyword),
                    ('model', '=', model + ',' + str(model_id)),
                    ],
                ]
        clause = [clause, ('action.active', '=', True)]
        action_keywords = cls.search(clause)
        types = defaultdict(list)
        for action_keyword in action_keywords:
            type_ = action_keyword.action.type
            types[type_].append(action_keyword.action.id)
        for type_, action_ids in types.items():
            for value in Action.get_action_values(type_, action_ids):
                value['keyword'] = keyword
                keywords.append(value)
        keywords.sort(key=lambda k: [
            a.action.id for a in action_keywords
        ].index(k['id']))
        cls._get_keyword_cache.set(key, keywords)
        return keywords


class ActionMixin(ModelSQL):
    _order_name = 'action'
    _action_name = 'name'

    @classmethod
    def __setup__(cls):
        super(ActionMixin, cls).__setup__()
        for name in dir(Action):
            field = getattr(Action, name)
            if (isinstance(field, fields.Field)
                    and not getattr(cls, name, None)):
                setattr(cls, name, fields.Function(field, 'get_action',
                        setter='set_action', searcher='search_action'))
                default_func = 'default_' + name
                if getattr(Action, default_func, None):
                    setattr(cls, default_func,
                        partial(ActionMixin._default_action, name))

    @staticmethod
    def _default_action(name):
        pool = Pool()
        Action = pool.get('ir.action')
        return getattr(Action, 'default_' + name, None)()

    @classmethod
    def get_action(cls, ids, names):
        records = cls.browse(ids)
        result = {}
        for name in names:
            result[name] = values = {}
            for record in records:
                value = getattr(record, 'action')
                convert = lambda v: v
                if value is not None:
                    value = getattr(value, name)
                    if isinstance(value, ModelStorage):
                        if cls._fields[name]._type == 'reference':
                            convert = str
                        else:
                            convert = int
                    elif isinstance(value, (list, tuple)):
                        convert = lambda v: [r.id for r in v]
                values[record.id] = convert(value)
        return result

    @classmethod
    def set_action(cls, records, name, value):
        pool = Pool()
        Action = pool.get('ir.action')
        Action.write([r.action for r in records], {
                name: value,
                })

    @classmethod
    def search_action(cls, name, clause):
        return [('action.' + clause[0],) + tuple(clause[1:])]

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        ModelView._fields_view_get_cache.clear()
        ModelView._view_toolbar_get_cache.clear()
        Action = pool.get('ir.action')
        ir_action = cls.__table__()
        new_records = []
        to_write = []
        for values in vlist:
            later = {}
            action_values = {}
            values = values.copy()
            for field in values:
                if field in Action._fields:
                    action_values[field] = values[field]
                if hasattr(getattr(cls, field), 'set'):
                    later[field] = values[field]
            for field in later:
                del values[field]
            action_values['type'] = cls.default_type()
            transaction = Transaction()
            database = transaction.database
            cursor = transaction.connection.cursor()
            if database.nextid(transaction.connection, cls._table):
                database.setnextid(transaction.connection, cls._table,
                    database.currid(transaction.connection, Action._table))
            if 'action' not in values:
                action, = Action.create([action_values])
                values['action'] = action.id
            else:
                action = Action(values['action'])
            record, = super(ActionMixin, cls).create([values])
            cursor.execute(*ir_action.update(
                    [ir_action.id], [action.id],
                    where=ir_action.id == record.id))
            transaction.database.update_auto_increment(
                transaction.connection, cls._table, action.id)
            record = cls(action.id)
            new_records.append(record)
            to_write.extend(([record], later))
        if to_write:
            cls.write(*to_write)
        return new_records

    @classmethod
    def write(cls, records, values, *args):
        pool = Pool()
        ActionKeyword = pool.get('ir.action.keyword')
        super(ActionMixin, cls).write(records, values, *args)
        ModelView._fields_view_get_cache.clear()
        ModelView._view_toolbar_get_cache.clear()
        ActionKeyword._get_keyword_cache.clear()

    @classmethod
    def delete(cls, records):
        pool = Pool()
        ModelView._fields_view_get_cache.clear()
        ModelView._view_toolbar_get_cache.clear()
        Action = pool.get('ir.action')
        actions = [x.action for x in records]
        super(ActionMixin, cls).delete(records)
        Action.delete(actions)

    @classmethod
    def copy(cls, records, default=None):
        pool = Pool()
        Action = pool.get('ir.action')
        if default is None:
            default = {}
        default = default.copy()
        new_records = []
        for record in records:
            default['action'] = Action.copy([record.action])[0].id
            new_records.extend(super(ActionMixin, cls).copy([record],
                    default=default))
        return new_records

    @classmethod
    def get_groups(cls, name, action_id=None):
        # TODO add cache
        domain = [
            (cls._action_name, '=', name),
            ]
        if action_id:
            domain.append(('id', '=', action_id))
        actions = cls.search(domain)
        groups = {g.id for a in actions for g in a.groups}
        return groups


class ActionReport(ActionMixin, ModelSQL, ModelView):
    "Action report"
    __name__ = 'ir.action.report'
    _action_name = 'report_name'
    model = fields.Char('Model')
    report_name = fields.Char('Internal Name', required=True)
    report = fields.Char(
        "Path",
        states={
            'invisible': Eval('is_custom', False),
            },
        depends=['is_custom'])
    report_content_custom = fields.Binary('Content')
    is_custom = fields.Function(fields.Boolean("Is Custom"), 'get_is_custom')
    report_content = fields.Function(fields.Binary('Content',
            filename='report_content_name'),
        'get_report_content', setter='set_report_content')
    report_content_name = fields.Function(fields.Char('Content Name'),
        'on_change_with_report_content_name')
    action = fields.Many2One('ir.action', 'Action', required=True,
            ondelete='CASCADE')
    direct_print = fields.Boolean('Direct Print')
    single = fields.Boolean("Single",
        help="Check if the template works only for one record.")
    translatable = fields.Boolean("Translatable",
        help="Uncheck to disable translations for this report.")
    template_extension = fields.Selection([
            ('odt', 'OpenDocument Text'),
            ('odp', 'OpenDocument Presentation'),
            ('ods', 'OpenDocument Spreadsheet'),
            ('odg', 'OpenDocument Graphics'),
            ('txt', 'Plain Text'),
            ('xml', 'XML'),
            ('html', 'HTML'),
            ('xhtml', 'XHTML'),
            ], string='Template Extension', required=True,
        translate=False)
    extension = fields.Selection([
            ('', ''),
            ('bib', 'BibTex'),
            ('bmp', 'Windows Bitmap'),
            ('csv', 'Text CSV'),
            ('dbf', 'dBase'),
            ('dif', 'Data Interchange Format'),
            ('doc', 'Microsoft Word 97/2000/XP'),
            ('doc6', 'Microsoft Word 6.0'),
            ('doc95', 'Microsoft Word 95'),
            ('docbook', 'DocBook'),
            ('docx', 'Microsoft Office Open XML Text'),
            ('docx7', 'Microsoft Word 2007 XML'),
            ('emf', 'Enhanced Metafile'),
            ('eps', 'Encapsulated PostScript'),
            ('gif', 'Graphics Interchange Format'),
            ('html', 'HTML Document'),
            ('jpg', 'Joint Photographic Experts Group'),
            ('met', 'OS/2 Metafile'),
            ('ooxml', 'Microsoft Office Open XML'),
            ('pbm', 'Portable Bitmap'),
            ('pct', 'Mac Pict'),
            ('pdb', 'AportisDoc (Palm)'),
            ('pdf', 'Portable Document Format'),
            ('pgm', 'Portable Graymap'),
            ('png', 'Portable Network Graphic'),
            ('ppm', 'Portable Pixelmap'),
            ('ppt', 'Microsoft PowerPoint 97/2000/XP'),
            ('psw', 'Pocket Word'),
            ('pwp', 'PlaceWare'),
            ('pxl', 'Pocket Excel'),
            ('ras', 'Sun Raster Image'),
            ('rtf', 'Rich Text Format'),
            ('latex', 'LaTeX 2e'),
            ('sda', 'StarDraw 5.0 (OpenOffice.org Impress)'),
            ('sdc', 'StarCalc 5.0'),
            ('sdc4', 'StarCalc 4.0'),
            ('sdc3', 'StarCalc 3.0'),
            ('sdd', 'StarImpress 5.0'),
            ('sdd3', 'StarDraw 3.0 (OpenOffice.org Impress)'),
            ('sdd4', 'StarImpress 4.0'),
            ('sdw', 'StarWriter 5.0'),
            ('sdw4', 'StarWriter 4.0'),
            ('sdw3', 'StarWriter 3.0'),
            ('slk', 'SYLK'),
            ('svg', 'Scalable Vector Graphics'),
            ('svm', 'StarView Metafile'),
            ('swf', 'Macromedia Flash (SWF)'),
            ('sxc', 'OpenOffice.org 1.0 Spreadsheet'),
            ('sxi', 'OpenOffice.org 1.0 Presentation'),
            ('sxd', 'OpenOffice.org 1.0 Drawing'),
            ('sxd3', 'StarDraw 3.0'),
            ('sxd5', 'StarDraw 5.0'),
            ('sxw', 'Open Office.org 1.0 Text Document'),
            ('text', 'Text Encoded'),
            ('tiff', 'Tagged Image File Format'),
            ('txt', 'Plain Text'),
            ('wmf', 'Windows Metafile'),
            ('xhtml', 'XHTML Document'),
            ('xls', 'Microsoft Excel 97/2000/XP'),
            ('xls5', 'Microsoft Excel 5.0'),
            ('xls95', 'Microsoft Excel 95'),
            ('xlsx', 'Microsoft Excel 2007/2010 XML'),
            ('xpm', 'X PixMap'),
            ], translate=False,
        string='Extension', help='Leave empty for the same as template, '
        'see LibreOffice documentation for compatible format')
    module = fields.Char('Module', readonly=True, select=True)
    email = fields.Char('Email',
        help='Python dictonary where keys define "to" "cc" "subject"\n'
        "Example: {'to': 'test@example.com', 'cc': 'user@example.com'}")
    pyson_email = fields.Function(fields.Char('PySON Email'), 'get_pyson')

    @classmethod
    def __setup__(cls):
        super(ActionReport, cls).__setup__()
        cls._error_messages.update({
                'invalid_email': 'Invalid email definition on report "%s".',
                })

    @classmethod
    def __register__(cls, module_name):
        super(ActionReport, cls).__register__(module_name)

        transaction = Transaction()
        cursor = transaction.connection.cursor()
        table = cls.__table_handler__(module_name)
        action_report = cls.__table__()

        # Migration from 3.4 remove report_name_module_uniq constraint
        table.drop_constraint('report_name_module_uniq')

        # Migration from 4.4 replace plain extension by txt
        cursor.execute(*action_report.update(
                [action_report.extension],
                ['txt'],
                where=action_report.extension == 'plain'))

    @staticmethod
    def default_type():
        return 'ir.action.report'

    @staticmethod
    def default_report_content():
        return None

    @staticmethod
    def default_direct_print():
        return False

    @classmethod
    def default_single(cls):
        return False

    @classmethod
    def default_translatable(cls):
        return True

    @staticmethod
    def default_template_extension():
        return 'odt'

    @staticmethod
    def default_extension():
        return ''

    @staticmethod
    def default_module():
        return Transaction().context.get('module') or ''

    @classmethod
    def validate(cls, reports):
        super(ActionReport, cls).validate(reports)
        cls.check_email(reports)

    @classmethod
    def check_email(cls, reports):
        "Check email"
        for report in reports:
            if report.email:
                try:
                    value = PYSONDecoder().decode(report.email)
                except Exception:
                    value = None
                if isinstance(value, dict):
                    inkeys = set(value)
                    if not inkeys <= EMAIL_REFKEYS:
                        cls.raise_user_error('invalid_email', (
                                report.rec_name,))
                else:
                    cls.raise_user_error('invalid_email', (report.rec_name,))

    def get_is_custom(self, name):
        return bool(self.report_content_custom)

    @classmethod
    def get_report_content(cls, reports, name):
        contents = {}
        converter = fields.Binary.cast
        default = None
        format_ = Transaction().context.get(
            '%s.%s' % (cls.__name__, name), '')
        if format_ == 'size':
            converter = len
            default = 0
        for report in reports:
            data = getattr(report, name + '_custom')
            if not data and getattr(report, name[:-8]):
                try:
                    with file_open(
                            getattr(report, name[:-8]).replace('/', os.sep),
                            mode='rb') as fp:
                        data = fp.read()
                except Exception:
                    data = None
            contents[report.id] = converter(data) if data else default
        return contents

    @classmethod
    def set_report_content(cls, records, name, value):
        cls.write(records, {'%s_custom' % name: value})

    @fields.depends('name', 'template_extension')
    def on_change_with_report_content_name(self, name=None):
        return ''.join(
            filter(None, [self.name, os.extsep, self.template_extension]))

    @classmethod
    def get_pyson(cls, reports, name):
        pysons = {}
        field = name[6:]
        defaults = {
            'email': '{}',
            }
        for report in reports:
            pysons[report.id] = (getattr(report, field)
                or defaults.get(field, 'null'))
        return pysons

    @classmethod
    def copy(cls, reports, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default.setdefault('module', None)

        new_reports = []
        for report in reports:
            if report.report:
                default['report_content'] = None
            default['report_name'] = report.report_name
            new_reports.extend(super(ActionReport, cls).copy([report],
                    default=default))
        return new_reports

    @classmethod
    def write(cls, reports, values, *args):
        context = Transaction().context
        if 'module' in context:
            actions = iter((reports, values) + args)
            args = []
            for reports, values in zip(actions, actions):
                values = values.copy()
                values['module'] = context['module']
                args.extend((reports, values))
            reports, values = args[:2]
            args = args[2:]
        super(ActionReport, cls).write(reports, values, *args)


class ActionActWindow(ActionMixin, ModelSQL, ModelView):
    "Action act window"
    __name__ = 'ir.action.act_window'
    domain = fields.Char('Domain Value')
    context = fields.Char('Context Value')
    order = fields.Char('Order Value')
    res_model = fields.Char('Model')
    context_model = fields.Char('Context Model')
    context_domain = fields.Char(
        "Context Domain",
        help="Part of the domain that will be evaluated on each refresh")
    act_window_views = fields.One2Many('ir.action.act_window.view',
            'act_window', 'Views')
    views = fields.Function(fields.Binary('Views'), 'get_views')
    act_window_domains = fields.One2Many('ir.action.act_window.domain',
        'act_window', 'Domains')
    domains = fields.Function(fields.Binary('Domains'), 'get_domains')
    limit = fields.Integer('Limit', help='Default limit for the list view')
    action = fields.Many2One('ir.action', 'Action', required=True,
            ondelete='CASCADE')
    search_value = fields.Char('Search Criteria',
            help='Default search criteria for the list view')
    pyson_domain = fields.Function(fields.Char('PySON Domain'), 'get_pyson')
    pyson_context = fields.Function(fields.Char('PySON Context'),
            'get_pyson')
    pyson_order = fields.Function(fields.Char('PySON Order'), 'get_pyson')
    pyson_search_value = fields.Function(fields.Char(
        'PySON Search Criteria'), 'get_pyson')

    @classmethod
    def __setup__(cls):
        super(ActionActWindow, cls).__setup__()
        cls._error_messages.update({
                'invalid_views': ('Invalid view "%(view)s" for action '
                    '"%(action)s".'),
                'invalid_domain': ('Invalid domain or search criteria '
                    '"%(domain)s" on action "%(action)s".'),
                'invalid_context': ('Invalid context "%(context)s" on action '
                    '"%(action)s".'),
                })
        cls.__rpc__.update({
                'get': RPC(),
                })

    @classmethod
    def __register__(cls, module_name):
        cursor = Transaction().connection.cursor()
        act_window = cls.__table__()
        super(ActionActWindow, cls).__register__(module_name)

        table = cls.__table_handler__(module_name)

        # Migration from 3.0: auto_refresh removed
        table.drop_column('auto_refresh')

        # Migration from 4.0: window_name removed
        table.drop_column('window_name')

        # Migration from 4.2: remove required on limit
        table.not_null_action('limit', 'remove')
        cursor.execute(*act_window.update(
                [act_window.limit], [Null],
                where=act_window.limit == 0))

    @staticmethod
    def default_type():
        return 'ir.action.act_window'

    @staticmethod
    def default_context():
        return '{}'

    @staticmethod
    def default_search_value():
        return '[]'

    @classmethod
    def validate(cls, actions):
        super(ActionActWindow, cls).validate(actions)
        cls.check_views(actions)
        cls.check_domain(actions)
        cls.check_context(actions)

    @classmethod
    def check_views(cls, actions):
        "Check views"
        for action in actions:
            if action.res_model:
                for act_window_view in action.act_window_views:
                    view = act_window_view.view
                    if view.model != action.res_model:
                        cls.raise_user_error('invalid_views', {
                                'view': view.rec_name,
                                'action': action.rec_name,
                                })
                    if view.type == 'board':
                        cls.raise_user_error('invalid_views', {
                                'view': view.rec_name,
                                'action': action.rec_name,
                                })
            else:
                for act_window_view in action.act_window_views:
                    view = act_window_view.view
                    if view.model:
                        cls.raise_user_error('invalid_views', {
                                'view': view.rec_name,
                                'action': action.rec_name,
                                })
                    if view.type != 'board':
                        cls.raise_user_error('invalid_views', {
                                'view': view.rec_name,
                                'action': action.rec_name,
                                })

    @classmethod
    def check_domain(cls, actions):
        "Check domain and search_value"
        for action in actions:
            for domain in (action.domain, action.search_value):
                if not domain:
                    continue
                try:
                    value = PYSONDecoder().decode(domain)
                except Exception:
                    cls.raise_user_error('invalid_domain', {
                            'domain': domain,
                            'action': action.rec_name,
                            })
                if isinstance(value, PYSON):
                    if not value.types() == set([list]):
                        cls.raise_user_error('invalid_domain', {
                                'domain': domain,
                                'action': action.rec_name,
                                })
                elif not isinstance(value, list):
                    cls.raise_user_error('invalid_domain', {
                            'domain': domain,
                            'action': action.rec_name,
                            })
                else:
                    try:
                        fields.domain_validate(value)
                    except Exception:
                        cls.raise_user_error('invalid_domain', {
                                'domain': domain,
                                'action': action.rec_name,
                                })

    @classmethod
    def check_context(cls, actions):
        "Check context"
        for action in actions:
            if action.context:
                try:
                    value = PYSONDecoder().decode(action.context)
                except Exception:
                    cls.raise_user_error('invalid_context', {
                            'context': action.context,
                            'action': action.rec_name,
                            })
                if isinstance(value, PYSON):
                    if not value.types() == set([dict]):
                        cls.raise_user_error('invalid_context', {
                                'context': action.context,
                                'action': action.rec_name,
                                })
                elif not isinstance(value, dict):
                    cls.raise_user_error('invalid_context', {
                            'context': action.context,
                            'action': action.rec_name,
                            })
                else:
                    try:
                        fields.context_validate(value)
                    except Exception:
                        cls.raise_user_error('invalid_context', {
                                'context': action.context,
                                'action': action.rec_name,
                                })

    def get_views(self, name):
        return [(view.view.id, view.view.type)
            for view in self.act_window_views]

    def get_domains(self, name):
        pool = Pool()
        ActWindowDomain = pool.get('ir.action.act_window.domain')
        act_window_domains = ActWindowDomain.search([
            [('act_window', '=', self.id)], [
                "OR",
                [('public', '=', True)],
                [('create_uid', '=', Transaction().user)]
            ]
        ])
        return [{
            'id': domain.id,
            'name': domain.name,
            'domain': domain.domain or '[]',
            'display_record_count': domain.display_record_count,
            'order': domain.order,
            'context': domain.context,
            'view': (domain.custom_view and domain.custom_view.id) or
            (domain.view and domain.view.id),
            'system_defined': domain.system_defined,
            'create_uid': domain.create_uid.id,
            'public': domain.public,
        } for domain in act_window_domains]

    @classmethod
    def get_pyson(cls, windows, name):
        pysons = {}
        field = name[6:]
        defaults = {
            'domain': '[]',
            'context': '{}',
            'search_value': '[]',
            }
        for window in windows:
            pysons[window.id] = (getattr(window, field)
                or defaults.get(field, 'null'))
        return pysons

    @classmethod
    def get(cls, xml_id):
        'Get values from XML id or id'
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        Action = pool.get('ir.action')
        if '.' in xml_id:
            action_id = ModelData.get_id(*xml_id.split('.'))
        else:
            action_id = int(xml_id)
        return Action.get_action_values(cls.__name__, [action_id])[0]


class ActionActWindowView(DeactivableMixin, ModelSQL, ModelView):
    "Action act window view"
    __name__ = 'ir.action.act_window.view'
    sequence = fields.Integer('Sequence', required=True)
    view = fields.Many2One('ir.ui.view', 'View', required=True,
            ondelete='CASCADE')
    act_window = fields.Many2One('ir.action.act_window', 'Action',
            ondelete='CASCADE')

    @classmethod
    def __setup__(cls):
        super(ActionActWindowView, cls).__setup__()
        cls._order.insert(0, ('sequence', 'ASC'))

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        windows = super(ActionActWindowView, cls).create(vlist)
        pool.get('ir.action.keyword')._get_keyword_cache.clear()
        return windows

    @classmethod
    def write(cls, windows, values, *args):
        pool = Pool()
        super(ActionActWindowView, cls).write(windows, values, *args)
        pool.get('ir.action.keyword')._get_keyword_cache.clear()

    @classmethod
    def delete(cls, windows):
        pool = Pool()
        super(ActionActWindowView, cls).delete(windows)
        pool.get('ir.action.keyword')._get_keyword_cache.clear()


class ActionActWindowDomain(DeactivableMixin, ModelSQL, ModelView):
    "Action act window domain"
    __name__ = 'ir.action.act_window.domain'
    name = fields.Char('Name', translate=True)
    sequence = fields.Integer('Sequence', required=True)
    domain = fields.Char('Domain')
    count = fields.Boolean('Count')
    act_window = fields.Many2One('ir.action.act_window', 'Action',
        select=True, required=True, ondelete='CASCADE')
    display_record_count = fields.Boolean(
        'Display record counts', help="Impacts performance"
    )
    active = fields.Boolean('Active')
    order = fields.Char('Order Value')
    context = fields.Char('Context Value')
    view = fields.Many2One('ir.ui.view', 'View', ondelete='SET NULL')
    custom_view = fields.Many2One(
        'ir.ui.view', 'Custom View', ondelete='CASCADE'
    )
    public = fields.Boolean("Is Public?", readonly=True)
    system_defined = fields.Function(
        fields.Boolean("Is System Defined?"), "get_system_defined"
    )

    @classmethod
    def __setup__(cls):
        super(ActionActWindowDomain, cls).__setup__()
        cls._order.insert(0, ('sequence', 'ASC'))
        cls._error_messages.update({
                'invalid_domain': ('Invalid domain or search criteria '
                    '"%(domain)s" on action "%(action)s".'),
                })
        cls.__rpc__.update({
            "create_view": RPC(readonly=False),
            "update_view": RPC(readonly=False),
            "delete_view": RPC(readonly=False),
        })

    @classmethod
    def default_count(cls):
        return False

    @staticmethod
    def default_display_record_count():
        return True

    @staticmethod
    def default_public():
        if Transaction().user == 0:
            return True
        return False

    @classmethod
    def validate(cls, actions):
        super(ActionActWindowDomain, cls).validate(actions)
        cls.check_domain(actions)

    @classmethod
    def check_domain(cls, actions):
        for action in actions:
            if not action.domain:
                continue
            try:
                value = PYSONDecoder().decode(action.domain)
            except Exception:
                value = None
            if isinstance(value, PYSON):
                if not value.types() == set([list]):
                    value = None
            elif not isinstance(value, list):
                value = None
            else:
                try:
                    fields.domain_validate(value)
                except Exception:
                    value = None
            if value is None:
                cls.raise_user_error('invalid_domain', {
                        'domain': action.domain,
                        'action': action.rec_name,
                        })

    @classmethod
    def get_system_defined(cls, domains, name):
        res = {}
        for domain in domains:
            res[domain.id] = not bool(domain.create_uid.id)
        return res

    @classmethod
    def _get_tree_view_arch(cls, model, string, fields, view_id=None):
        """Validate and return tree view arch xml.
            model: model name
            string: String to be used on view
            fields: List of field names
            view_id: Existing view id in case trying to update system defined
                view columns.
        """
        if not len(fields):
            cls.raise_user_error("Really! atleast add one column")

        # Replace all double quots as they will conflict with xml arch
        string = string.replace('"', '')

        View = Pool().get('ir.ui.view')
        Model = Pool().get(model)
        if view_id:
            view = View(view_id)
            views = View.search([
                'OR', [
                    ('inherit', '=', view_id),
                    ('model', '=', model),
                ], [
                    ('id', '=', view_id),
                    ('inherit', '!=', None),
                ],
            ])
            views.sort(key=lambda x: cls._modules_list.index(x.module or None))
            parser = etree.XMLParser(remove_comments=True)
            root = etree.fromstring(view.arch, parser=parser)
            for view in views:
                if not view.arch or not view.arch.strip():
                    continue
                tree_inherit = etree.fromstring(view.arch, parser=parser)
                root = _inherit_apply(root, tree_inherit)
        else:
            root = etree.fromstring('<tree string="%s"></tree>' % (string, ))

        all_fields = Model.fields_get().keys()
        for field in fields:
            if field not in all_fields:
                cls.raise_user_error(
                    "Column %s doesn't exist in this model" % field
                )

        create_action = root.xpath('//tree')[0].get('create-action')
        arch = '<tree string="%s">\n' % string
        if create_action:
            arch = '<tree string="%s" create-action="%s">\n' % (
                string, create_action
            )

        for field in fields:
            arch += '<field name="%s"/>\n' % field

        # Adding bulk action button
        for element in root.findall('./bulk-action-button'):
            arch += etree.tostring(element)
        for button in root.findall('./button'):
            arch += etree.tostring(button)
        arch += "</tree>"

        return arch

    @classmethod
    def create_view(
            cls, act_window_id, name, domain, fields, public=False,
            view_id=None):
        """Creates a domain window view with given name and domain. It also
        creates a ir.ui.view and attach it to custom view field.
            action_window_id: instance of ir.action.act_window model
            name: domain window name
            domain: pyson domain
            fields: list of field names
            public: make view public
            view_id: Existing view id in case trying to update system defined
                view columns.
        """
        pool = Pool()
        ActionWindow = pool.get('ir.action.act_window')
        ActWindowDomain = pool.get('ir.action.act_window.domain')
        View = pool.get('ir.ui.view')

        try:
            action_window, = ActionWindow.search([('id', '=', act_window_id)])
        except ValueError:
            cls.raise_user_error("Action window id is invalid")

        # Create custom view and attach it to domain window.
        custom_view = View()
        custom_view.model = action_window.res_model
        custom_view.type = 'tree'
        custom_view.data = cls._get_tree_view_arch(
            model=action_window.res_model,
            string=name,
            fields=fields,
            view_id=view_id
        )
        action_domain = ActWindowDomain()
        action_domain.act_window = action_window
        action_domain.name = name
        action_domain.domain = domain
        action_domain.public = public
        action_domain.custom_view = custom_view
        action_domain.sequence = 10
        with Transaction().set_context(_check_access=False):
            action_domain.save()

        # Finally clear cache
        ModelView._fields_view_get_cache.clear()
        ActionKeyword._get_keyword_cache.clear()
        return action_domain.id

    @classmethod
    def update_view(
            cls, action_domain_id, name=None, domain=None, fields=None,
            public=None, view_id=None
    ):
        """Updates a domain window view with given name and domain. Requires
        domain window id always.
            action_domain_id: id of ir.action.act_window.domain model id
            name: name to update on domain window
            domain: domain to be updated
            fields: field names to be updated on view
            public: make view public
            view_id: Existing view id in case trying to update system defined
                view columns.
        """
        pool = Pool()
        ActWindowDomain = pool.get('ir.action.act_window.domain')
        View = pool.get('ir.ui.view')

        try:
            action_domain, = ActWindowDomain.search([
                ('id', '=', action_domain_id)
            ])
        except ValueError:
            cls.raise_user_error("Action domain id is invalid")

        if action_domain.system_defined and (
                name or domain or public is not None
        ):
            # You cannot update name and domain on system defined view.
            cls.raise_user_error("System defined views cannot be edited")
        if name:
            action_domain.name = name
        if domain:
            action_domain.domain = domain
        if public is not None:
            action_domain.public = public
        if fields:
            custom_view = action_domain.custom_view
            if custom_view is None:
                custom_view = View()
                custom_view.model = action_domain.act_window.res_model
                custom_view.type = 'tree'
                action_domain.custom_view = custom_view
            custom_view.arch = cls._get_tree_view_arch(
                model=action_domain.act_window.res_model,
                string=name or action_domain.name,
                fields=fields,
                view_id=action_domain.view and action_domain.view.id or view_id
            )
            with Transaction().set_context(_check_access=False):
                custom_view.save()
        with Transaction().set_context(_check_access=False):
            action_domain.save()

        # Finally clear cache
        ModelView._fields_view_get_cache.clear()
        ActionKeyword._get_keyword_cache.clear()

    @classmethod
    def delete_view(cls, action_domain_id):
        """Delete custom domain views.
            action_domain_id: id of ir.action.act_window.domain model id
        """
        pool = Pool()
        ActWindowDomain = pool.get('ir.action.act_window.domain')

        try:
            action_domain, = ActWindowDomain.search([
                ('id', '=', action_domain_id)
            ])
        except ValueError:
            cls.raise_user_error("Action domain id is invalid")
        if action_domain.system_defined:
            cls.raise_user_error("System defined views cannot be deleted")

        with Transaction().set_context(_check_access=False):
            ActWindowDomain.delete([action_domain])

        # Finally clear cache
        ModelView._fields_view_get_cache.clear()
        ActionKeyword._get_keyword_cache.clear()

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        domains = super(ActionActWindowDomain, cls).create(vlist)
        pool.get('ir.action.keyword')._get_keyword_cache.clear()
        return domains

    @classmethod
    def write(cls, domains, values, *args):
        pool = Pool()
        super(ActionActWindowDomain, cls).write(domains, values, *args)
        pool.get('ir.action.keyword')._get_keyword_cache.clear()

    @classmethod
    def delete(cls, domains):
        pool = Pool()
        super(ActionActWindowDomain, cls).delete(domains)
        pool.get('ir.action.keyword')._get_keyword_cache.clear()


class ActionWizard(ActionMixin, ModelSQL, ModelView):
    "Action wizard"
    __name__ = 'ir.action.wizard'
    _action_name = 'wiz_name'
    wiz_name = fields.Char('Wizard name', required=True)
    action = fields.Many2One('ir.action', 'Action', required=True,
            ondelete='CASCADE')
    model = fields.Char('Model')
    email = fields.Char('Email')
    window = fields.Boolean('Window', help='Run wizard in a new window')
    context = fields.Char('Context Value')

    @staticmethod
    def default_type():
        return 'ir.action.wizard'

    @classmethod
    def __setup__(cls):
        super(ActionWizard, cls).__setup__()
        cls._error_messages.update({
            'invalid_context': (
                'Invalid context "%(context)s" on wizards "%(wizard)s".'
            ),
        })

    @classmethod
    def validate(cls, wizards):
        super(ActionWizard, cls).validate(wizards)
        cls.check_context(wizards)

    @classmethod
    def check_context(cls, wizards):
        "Check context"
        for wizard in wizards:
            if wizard.context:
                try:
                    value = PYSONDecoder().decode(wizard.context)
                except Exception:
                    cls.raise_user_error('invalid_context', {
                        'context': wizard.context,
                        'wizard': wizard.name,
                    })
                if isinstance(value, PYSON):
                    if not value.types() == set([dict]):
                        cls.raise_user_error('invalid_context', {
                            'context': wizard.context,
                            'wizard': wizard.name,
                        })
                elif not isinstance(value, dict):
                    cls.raise_user_error('invalid_context', {
                        'context': wizard.context,
                        'wizard': wizard.name,
                    })
                else:
                    try:
                        fields.context_validate(value)
                    except Exception:
                        cls.raise_user_error('invalid_context', {
                            'context': wizard.context,
                            'wizard': wizard.name,
                        })


class ActionURL(ActionMixin, ModelSQL, ModelView):
    "Action URL"
    __name__ = 'ir.action.url'
    url = fields.Char('Action Url', required=True)
    action = fields.Many2One('ir.action', 'Action', required=True,
            ondelete='CASCADE')

    @staticmethod
    def default_type():
        return 'ir.action.url'
