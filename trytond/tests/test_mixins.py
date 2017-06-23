# -*- coding: utf-8 -*-
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

import unittest

from trytond.tests.test_tryton import install_module, with_transaction
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.url import HOSTNAME


class UrlTestCase(unittest.TestCase):
    "Test URL generation"

    @classmethod
    def setUpClass(cls):
        install_module('tests')

    @with_transaction()
    def testModelURL(self):
        "Test model URLs"
        pool = Pool()
        UrlObject = pool.get('test.urlobject')

        self.assertEqual(UrlObject.__url__,
            'https://%s/client/#/model/test.urlobject' % (
                HOSTNAME, ))

        self.assertEqual(UrlObject(1).__url__,
            'https://%s/client/#/model/test.urlobject/1' % (
                HOSTNAME, ))

    @with_transaction()
    def testWizardURL(self):
        "Test wizard URLs"
        pool = Pool()
        UrlWizard = pool.get('test.test_wizard', type='wizard')
        db_name = Transaction().database.name

        self.assertEqual(UrlWizard.__url__,
            'https://%s/client/#/wizard/test.test_wizard' % (
                HOSTNAME, ))


def suite():
    func = unittest.TestLoader().loadTestsFromTestCase
    suite = unittest.TestSuite()
    for testcase in (UrlTestCase,):
        suite.addTests(func(testcase))
    return suite
