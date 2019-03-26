# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from ..pool import Pool
from .activity import *
from .configuration import *
from .translation import *
from .sequence import *
from .ui.menu import *
from .ui.view import *
from .ui.icon import *
from .property import *
from .action import *
from .model import *
from .attachment import *
from .note import *
from .cron import *
from .lang import *
from .export import *
from .rule import *
from .module import *
from .cache import *
from .date import *
from .trigger import *
from .session import *
from . import queue
from .kvstore import *


def register():
    Pool.register(
        Configuration,
        Translation,
        TranslationSetStart,
        TranslationSetSucceed,
        TranslationCleanStart,
        TranslationCleanSucceed,
        TranslationUpdateStart,
        TranslationExportStart,
        TranslationExportResult,
        SequenceType,
        Sequence,
        SequenceStrict,
        UIMenu,
        UIMenuFavorite,
        View,
        ShowViewStart,
        ViewTreeWidth,
        ViewTreeState,
        ViewSearch,
        Icon,
        Property,
        Action,
        ActionKeyword,
        ActionReport,
        ActionActWindow,
        ActionActWindowView,
        ActionActWindowDomain,
        ActionWizard,
        ActionURL,
        Model,
        ModelField,
        ModelAccess,
        ModelFieldAccess,
        ModelButton,
        ModelData,
        PrintModelGraphStart,
        Activity,
        Attachment,
        Note,
        NoteRead,
        Cron,
        Lang,
        Export,
        ExportLine,
        RuleGroup,
        Rule,
        Module,
        ModuleDependency,
        ModuleConfigWizardItem,
        ModuleConfigWizardFirst,
        ModuleConfigWizardOther,
        ModuleConfigWizardDone,
        ModuleInstallUpgradeStart,
        ModuleInstallUpgradeDone,
        Cache,
        Date,
        Trigger,
        TriggerLog,
        Session,
        SessionWizard,
        queue.Queue,
        KeyValueStore,
        module='ir', type_='model')
    Pool.register(
        TranslationSet,
        TranslationClean,
        TranslationUpdate,
        TranslationExport,
        ShowView,
        PrintModelGraph,
        ModuleConfigWizard,
        ModuleInstallUpgrade,
        ModuleConfig,
        module='ir', type_='wizard')
    Pool.register(
        ModelGraph,
        ModelWorkflowGraph,
        module='ir', type_='report')
