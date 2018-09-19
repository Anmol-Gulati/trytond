# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import unittest

from .test_tryton import ModuleTestCase, with_transaction
from trytond.pool import Pool
from trytond.exceptions import UserError


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
            "<tree string='All'>\n" +
            "<field name='name'/>\n" +
            "</tree>"
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
            "<tree string='Out of Sync'>\n" +
            "<field name='module'/>\n" +
            "</tree>"
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


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(IrTestCase)
