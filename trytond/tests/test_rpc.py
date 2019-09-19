import unittest

from trytond.rpc import RPC


class RPCTestCase(unittest.TestCase):
    'Test RPC'

    def test_simple(self):
        "Test simple"
        rpc = RPC(check_access=False)
        self.assertEqual(
            rpc.convert(None, 'foo', {}),
            (['foo'], {}, {}, None))

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


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(RPCTestCase)
