# -*- coding: utf-8 -*-
"""
All tests for queue
"""
import unittest

from trytond.pool import Pool
from trytond.tests.test_tryton import activate_module, with_transaction


class QueueTestCase(unittest.TestCase):
    'Test Queue'

    @classmethod
    def setUpClass(cls):
        activate_module('tests')

    @with_transaction()
    def test_queue_params(self):
        """
        Tests if queue parameters are saved to database
        """
        Queue = Pool().get('ir.queue')

        Model = Queue.caller(Queue)
        task_id = Model.default_enqueued_at()
        queued_task = Queue(task_id)

        assert queued_task.data['instances'] == []
        assert queued_task.data['args'] == []
        assert queued_task.finished_at is None
        assert queued_task.run() is None
        assert queued_task.finished_at is not None


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(QueueTestCase)
