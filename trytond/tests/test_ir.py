# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from dateutil.relativedelta import relativedelta
import datetime
import unittest

from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.exceptions import UserError
from .test_tryton import ModuleTestCase, with_transaction


class IrTestCase(ModuleTestCase):
    'Test ir module'
    module = 'ir'

    @with_transaction()
    def test_domain_window_create_view(self):
        pool = Pool()
        ActWindowDomain = pool.get('ir.action.act_window.domain')
        ActWindow = pool.get('ir.action.act_window')

        act_window, = ActWindow.search([
            ('res_model', '=', 'ir.action.act_window')
        ])
        domain_window_id = ActWindowDomain.create_view(
            act_window.id,
            "All",
            "[]",
            ["name"],
            True,
        )
        domain_window = ActWindowDomain(domain_window_id)
        self.assertEqual(domain_window.name, "All")
        self.assertEqual(domain_window.domain, "[]")
        self.assertIsNone(domain_window.view)
        self.assertTrue(domain_window.custom_view)
        self.assertTrue(domain_window.public)
        self.assertEqual(
            domain_window.custom_view.arch,
            '<tree string="All">\n' +
            '<field name="name"/>\n' +
            '</tree>'
        )
        self.assertTrue(act_window.domains)

    @with_transaction()
    def test_domain_window_update_view(self):
        pool = Pool()
        ActWindowDomain = pool.get('ir.action.act_window.domain')

        domain_window, = ActWindowDomain.search([('name', '=', 'Out of Sync')])

        # Try updating domain or name for system defind act window, it
        # should raise exception.
        self.assertTrue(domain_window.system_defined)
        with self.assertRaises(UserError):
            ActWindowDomain.update_view(
                domain_window.id,
                "All",
                "[]",
                ["name"],
            )

        ActWindowDomain.update_view(
            domain_window.id,
            None,
            None,
            ["module"],
        )
        self.assertTrue(domain_window.custom_view)
        self.assertTrue(domain_window.public)
        self.assertEqual(
            domain_window.custom_view.arch,
            '<tree string="Out of Sync">\n' +
            '<field name="module"/>\n' +
            '</tree>'
        )

    @with_transaction()
    def test_domain_window_delete_view(self):
        pool = Pool()
        ActWindowDomain = pool.get('ir.action.act_window.domain')
        ActWindow = pool.get('ir.action.act_window')

        domain_window, = ActWindowDomain.search([('name', '=', 'Out of Sync')])

        # Try deleting domain window for system defind act window, it
        # should raise exception.
        self.assertTrue(domain_window.system_defined)
        with self.assertRaises(UserError):
            ActWindowDomain.delete_view(domain_window.id)

        # Create a custom view and try deleting
        act_window, = ActWindow.search([
            ('res_model', '=', 'ir.action.act_window')
        ])
        domain_window_id = ActWindowDomain.create_view(
            act_window.id,
            "All",
            "[]",
            ["name"],
            True,
        )
        ActWindowDomain.delete_view(domain_window_id)
        self.assertFalse(ActWindowDomain.search_count([
            ('id', '=', domain_window_id)
        ]))

    @with_transaction()
    def test_sequence_substitutions(self):
        'Test Sequence Substitutions'
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        SequenceType = pool.get('ir.sequence.type')
        Date = pool.get('ir.date')
        try:
            Group = pool.get('res.group')
            groups = Group.search([])
        except KeyError:
            groups = []

        sequence_type = SequenceType(name='Test', code='test', groups=groups)
        sequence_type.save()
        sequence = Sequence(name='Test Sequence', code='test')
        sequence.save()
        self.assertEqual(Sequence.get_id(sequence.id), '1')
        today = Date.today()
        sequence.prefix = '${year}'
        sequence.save()
        self.assertEqual(Sequence.get_id(sequence.id),
            '%s2' % str(today.year))
        next_year = today + relativedelta(years=1)
        with Transaction().set_context(date=next_year):
            self.assertEqual(Sequence.get_id(sequence.id),
                '%s3' % str(next_year.year))

    @with_transaction()
    def test_global_search(self):
        'Test Global Search'
        pool = Pool()
        Model = pool.get('ir.model')
        Model.global_search('User', 10)

    @with_transaction()
    def test_lang_strftime(self):
        "Test Lang.strftime"
        pool = Pool()
        Lang = pool.get('ir.lang')
        test_data = [
            ((2016, 8, 3), 'en', '%d %B %Y', "03 August 2016"),
            ((2016, 8, 3), 'fr', '%d %B %Y', "03 ao\xfbt 2016"),
            ((2016, 8, 3), 'fr', '%d %B %Y', "03 ao\xfbt 2016"),
            ]
        for date, code, format_, result in test_data:
            lang = Lang.get(code)
            self.assertEqual(
                lang.strftime(datetime.date(*date), format_),
                result)


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(IrTestCase)
