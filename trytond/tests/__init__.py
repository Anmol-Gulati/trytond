# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

try:
    import pkg_resources
except ImportError:
    pkg_resources = None


from ..pool import Pool
from .modelview import *
from .rpc import *
from .mptt import *
from .import_data import *
from .export_data import *
from .trigger import *
from .access import *
from .wizard import *
from .workflow import *
from .history import *
from .field_context import *
from . import model
from . import modelstorage
from . import modelsql
from . import field_boolean
from . import field_integer
from . import field_float
from . import field_numeric
from . import field_char
from . import field_text
from . import field_date
from . import field_datetime
from . import field_time
from . import field_timedelta
from . import field_selection
from . import field_dict
from . import field_binary
from . import field_many2one
from . import field_reference
from . import field_one2many
from . import field_many2many
from . import field_one2one
from . import multivalue
from . import mixin
from . import tree
from . import rule
from . import copy_


def register():
    Pool.register(
        Boolean,
        BooleanDefault,
        Integer,
        IntegerDefault,
        IntegerRequired,
        IntegerDomain,
        Float,
        FloatDefault,
        FloatRequired,
        FloatDigits,
        Numeric,
        NumericDefault,
        NumericRequired,
        NumericDigits,
        Char,
        CharDefault,
        CharRequired,
        CharSize,
        CharTranslate,
        Text,
        TextDefault,
        TextRequired,
        TextSize,
        TextTranslate,
        Date,
        DateDefault,
        DateRequired,
        DateTime,
        DateTimeDefault,
        DateTimeRequired,
        DateTimeFormat,
        Time,
        TimeDefault,
        TimeRequired,
        TimeFormat,
        TimeDelta,
        TimeDeltaDefault,
        TimeDeltaRequired,
        One2One,
        One2OneTarget,
        One2OneRelation,
        One2OneRequired,
        One2OneRequiredRelation,
        One2OneDomain,
        One2OneDomainRelation,
        One2Many,
        One2ManyTarget,
        One2ManyRequired,
        One2ManyRequiredTarget,
        One2ManyReference,
        One2ManyReferenceTarget,
        One2ManySize,
        One2ManySizeTarget,
        One2ManySizePYSON,
        One2ManySizePYSONTarget,
        Many2Many,
        Many2ManyTarget,
        Many2ManyRelation,
        Many2ManyRequired,
        Many2ManyRequiredTarget,
        Many2ManyRequiredRelation,
        Many2ManyReference,
        Many2ManyReferenceTarget,
        Many2ManyReferenceRelation,
        Many2ManySize,
        Many2ManySizeTarget,
        Many2ManySizeRelation,
        Many2ManyTree,
        Many2ManyTreeRelation,
        Reference,
        ReferenceTarget,
        ReferenceRequired,
        Property,
        Selection,
        SelectionRequired,
        DictSchema,
        Dict,
        DictDefault,
        DictRequired,
        Binary,
        BinaryDefault,
        BinaryRequired,
        Singleton,
        URLObject,
        ModelStorage,
        ModelStoragePYSONDomain,
        ModelSQLRequiredField,
        ModelSQLTimestamp,
        ModelSQLFieldSet,
        Model4Union1,
        Model4Union2,
        Model4Union3,
        Model4Union4,
        Union,
        UnionUnion,
        Model4UnionTree1,
        Model4UnionTree2,
        UnionTree,
        ModelViewChangedValues,
        ModelViewChangedValuesTarget,
        ModelRPC,
        ModelViewChangedValues,
        ModelViewChangedValuesTarget,
        ModelViewButton,
        ModelViewButtonDepends,
        ModelViewRPC,
        ModelViewEmptyPage,
        ModelViewCircularDepends,
        MPTT,
        ImportDataBoolean,
        ImportDataInteger,
        ImportDataIntegerRequired,
        ImportDataFloat,
        ImportDataFloatRequired,
        ImportDataNumeric,
        ImportDataNumericRequired,
        ImportDataChar,
        ImportDataText,
        ImportDataDate,
        ImportDataDateTime,
        ImportDataSelection,
        ImportDataMany2OneTarget,
        ImportDataMany2One,
        ImportDataMany2ManyTarget,
        ImportDataMany2Many,
        ImportDataMany2ManyRelation,
        ImportDataOne2Many,
        ImportDataOne2ManyTarget,
        ImportDataReferenceSelection,
        ImportDataReference,
        ExportDataTarget,
        ExportData,
        ExportDataTarget2,
        ExportDataRelation,
        Triggered,
        TriggerAction,
        TestAccess,
        TestWizardStart,
        WorkflowedModel,
        TestHistory,
        TestHistoryLine,
        FieldContextChild,
        FieldContextParent,
        module='tests', type_='model')
    Pool.register(
        TestWizard,
        module='tests', type_='wizard')

    model.register('tests')
    modelstorage.register('tests')
    modelsql.register('tests')
    field_boolean.register('tests')
    field_integer.register('tests')
    field_float.register('tests')
    field_numeric.register('tests')
    field_char.register('tests')
    field_text.register('tests')
    field_date.register('tests')
    field_datetime.register('tests')
    field_time.register('tests')
    field_timedelta.register('tests')
    field_selection.register('tests')
    field_dict.register('tests')
    field_binary.register('tests')
    field_many2one.register('tests')
    field_reference.register('tests')
    field_one2many.register('tests')
    field_many2many.register('tests')
    field_one2one.register('tests')
    multivalue.register('tests')
    mixin.register('tests')
    tree.register('tests')
    rule.register('tests')
    copy_.register('tests')

    if pkg_resources is not None:
        entry_points = pkg_resources.iter_entry_points('trytond.tests')
        for test_ep in entry_points:
            test_module = test_ep.load()
            if hasattr(test_module, 'register'):
                test_module.register('tests')


def suite():
    from .test_tryton import all_suite
    return all_suite()
