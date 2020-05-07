# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import unittest
from unittest.mock import Mock, DEFAULT, call

from trytond.rpc import RPC
from trytond.pool import Pool
from trytond.exceptions import UserError
from trytond.transaction import Transaction
from trytond.tests.test_tryton import with_transaction, activate_module


class RPCTestCase(unittest.TestCase):
    "Test RPC"

    @classmethod
    def setUpClass(cls):
        activate_module('ir')

    @with_transaction()
    def test_simple(self):
        "Test simple"
        rpc = RPC(check_access=False)
        self.assertEqual(
            rpc.convert(None, None, 'foo', {}),
            (['foo'], {}, {}, None))

    @with_transaction()
    def test_atomic_validation(self):
        "Test atomic rpc validation"
        rpc = RPC()
        assert rpc.atomic is True

        rpc = RPC(instantiate=0, atomic=True)
        assert rpc.instantiate is not None
        assert rpc.atomic is True

        rpc = RPC(atomic=False)
        assert rpc.instantiate is None
        assert rpc.atomic is False

        with self.assertRaises(AssertionError) as context:
            RPC(instantiate=0, atomic=False)

        assert "Non atomic RPC doesn't support instantiation" == \
            str(context.exception)

    @with_transaction()
    def test_keyword_argument(self):
        "Test keyword argument"
        rpc = RPC(check_access=False)
        self.assertEqual(
            rpc.convert(None, None, 'foo', bar=True, context={}),
            (['foo'], {'bar': True}, {}, None))

    @with_transaction()
    def test_clean_context(self):
        "Test clean context"
        rpc = RPC(check_access=False)
        self.assertEqual(
            rpc.convert(None, None, {'_foo': True, '_datetime': None}),
            ([], {}, {'_datetime': None}, None))

    @with_transaction()
    def test_timestamp(self):
        "Test context timestamp"
        rpc = RPC(check_access=False)
        self.assertEqual(
            rpc.convert(None, None, {'_timestamp': 'test'}),
            ([], {}, {}, 'test'))

    @with_transaction()
    def test_instantiate(self):
        "Test instantiate"

        def side_effect(*args, **kwargs):
            self.assertEqual(Transaction().context, {'test': True})
            return DEFAULT

        rpc = RPC(instantiate=0, check_access=True)
        obj = Mock(__name__="test.model_rpc")
        obj.return_value = instance = Mock(__name__="test.model_rpc")
        obj.side_effect = side_effect

        # Integer
        self.assertEqual(
            rpc.convert(obj, 'echo_atomic_rpc', 1, {'test': True}),
            ([instance], {}, {'test': True, '_check_access': True}, None))
        obj.assert_called_once_with(1)

        obj.reset_mock()
        obj.__name__ = "test.model_rpc"

        # Dictionary
        self.assertEqual(
            rpc.convert(
                obj, 'echo_atomic_rpc', {'foo': 'bar'}, {'test': True}),
            ([instance], {}, {'test': True, '_check_access': True}, None))
        obj.assert_called_once_with(foo='bar')

        obj.reset_mock()
        obj.__name__ = "test.model_rpc"

        obj.browse.return_value = instances = Mock(__name__="test.model_rpc")

        # List
        self.assertEqual(
            rpc.convert(obj, 'echo_atomic_rpc', [1, 2, 3], {'test': True}),
            ([instances], {}, {'test': True, '_check_access': True}, None))
        obj.browse.assert_called_once_with([1, 2, 3])

    @with_transaction()
    def test_instantiate_unique(self):
        "Test instantiate unique"
        rpc = RPC(instantiate=0, unique=True)
        obj = Mock(__name__="test.model_rpc")

        rpc.convert(obj, 'echo_atomic_rpc', [1, 2], {})
        obj.browse.assert_called_once_with([1, 2])

        obj.reset_mock()
        obj.__name__ = "test.model_rpc"

        with self.assertRaises(ValueError):
            rpc.convert(obj, 'echo_atomic_rpc', [1, 1], {})

    @with_transaction()
    def test_instantiate_slice(self):
        "Test instantiate with slice"
        rpc = RPC(instantiate=slice(0, 2), check_access=False)
        obj = Mock(__name__="test.model_rpc")
        obj.return_value = instance = Mock(__name__="test.model_rpc")

        self.assertEqual(
            rpc.convert(obj, 'echo_atomic_rpc', 1, 2, {}),
            ([instance, instance], {}, {}, None))
        obj.assert_has_calls([call(1), call(2)])

    @with_transaction()
    def test_check_access(self):
        "Test check_access"
        pool = Pool()
        TestRPC = pool.get("test.model_rpc")

        rpc_no_access = RPC(check_access=False)
        self.assertEqual(
            rpc_no_access.convert(TestRPC, "echo_atomic_rpc", 'foo', {}),
            (['foo'], {}, {}, None))

        rpc_with_access = RPC(check_access=True)
        self.assertEqual(
            rpc_with_access.convert(TestRPC, "echo_atomic_rpc", 'foo', {}),
            (['foo'], {}, {'_check_access': True}, None))

    @with_transaction()
    def test_rpc_perm(self):
        pool = Pool()
        Model = pool.get('ir.model')
        ModelData = pool.get('ir.model.data')
        ModelRPC = pool.get('ir.model.rpc')
        TestRPC = pool.get("test.model_rpc")
        User = pool.get('res.user')

        rpc_model, = Model.search([("model", "=", "test.model_rpc")])
        group_id = ModelData.get_id("res", "group_admin")

        ModelRPC.create([{
            "method": "echo_atomic_rpc",
            "model": rpc_model,
            "groups": [('add', [group_id])]
        }])

        user, = User.create([{
            'name': 'dummy user',
            'login': 'dummy@user.com',
        }])

        with Transaction().set_user(user.id):
            with self.assertRaises(UserError) as exception:
                rpc = RPC(check_access=True)
                rpc.convert(TestRPC, "echo_atomic_rpc", 'foo', {})

        assert "Calling rpc echo_atomic_rpc on test.model_rpc is not allowed!" \
            in exception.exception.message


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(RPCTestCase)
