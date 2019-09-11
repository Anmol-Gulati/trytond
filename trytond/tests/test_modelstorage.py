# This file is part of Tryton.  The COPYRIGHT file at the top level of this
# repository contains the full copyright notices and license terms.

import unittest

from trytond.error import UserError
from trytond.pool import Pool
from trytond.tests.test_tryton import install_module, with_transaction


class ModelStorageTestCase(unittest.TestCase):
    'Test ModelStorage'

    @classmethod
    def setUpClass(cls):
        install_module('tests')

    @with_transaction()
    def test_search_read_order(self):
        'Test search_read order'
        pool = Pool()
        ModelStorage = pool.get('test.modelstorage')

        ModelStorage.create([{'name': i} for i in ['foo', 'bar', 'test']])

        rows = ModelStorage.search_read([])
        self.assertTrue(
            all(x['id'] < y['id'] for x, y in zip(rows, rows[1:])))

        rows = ModelStorage.search_read([], order=[('name', 'ASC')])
        self.assertTrue(
            all(x['name'] <= y['name'] for x, y in zip(rows, rows[1:])))

        rows = ModelStorage.search_read([], order=[('name', 'DESC')])
        self.assertTrue(
            all(x['name'] >= y['name'] for x, y in zip(rows, rows[1:])))

    @with_transaction()
    def test_pyson_domain_same(self):
        "Test same pyson domain validation"
        pool = Pool()
        Model = pool.get('test.modelstorage.pyson_domain')

        Model.create([{'constraint': 'foo', 'value': 'foo'}] * 10)

        with self.assertRaises(UserError):
            Model.create([{'constraint': 'foo', 'value': 'bar'}] * 10)

    @with_transaction()
    def test_pyson_domain_unique(self):
        "Test unique pyson domain validation"
        pool = Pool()
        Model = pool.get('test.modelstorage.pyson_domain')

        Model.create(
            [{'constraint': str(i), 'value': str(i)} for i in range(10)])

        with self.assertRaises(UserError):
            Model.create(
                [{'constraint': str(i), 'value': str(i + 1)}
                    for i in range(10)])

    @with_transaction()
    def test_pyson_domain_single(self):
        "Test pyson domain validation for 1 record"
        pool = Pool()
        Model = pool.get('test.modelstorage.pyson_domain')

        Model.create([{'constraint': 'foo', 'value': 'foo'}])

        with self.assertRaises(UserError):
            Model.create([{'constraint': 'foo', 'value': 'bar'}])

    @with_transaction()
    def test_messages_field_returns_as_expected(self):
        """Test if the get messages returns messages properly after archival"""
        pool = Pool()
        Menu = pool.get('ir.ui.menu')
        menu_obj, = Menu.search([], limit=1)
        assert len(menu_obj.messages) == 0
        Menu.archive([menu_obj])
        assert menu_obj.messages[0]["title"] == "This record has been archived."
        assert menu_obj.messages[0]["type"] == "info"


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(ModelStorageTestCase)
