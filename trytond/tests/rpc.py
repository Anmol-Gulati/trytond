from trytond.model import ModelView
from trytond.transaction import Transaction
from trytond.rpc import RPC

__all__ = [
    'ModelRPC',
]


class ModelRPC(ModelView):
    "Model RPC"
    __name__ = 'test.model_rpc'

    @classmethod
    def __setup__(cls):
        super(ModelRPC, cls).__setup__()
        cls.__rpc__.update({
            'echo_atomic_rpc': RPC(atomic=True),
            'echo_non_atomic_rpc': RPC(atomic=False),
        })

    @classmethod
    def echo_atomic_rpc(cls, data):
        return {
            'data': data,
            'context': Transaction().context,
            'execution_user': Transaction().user,
        }

    @classmethod
    def echo_non_atomic_rpc(cls, data, user, context):
        return {
            'data': data,
            'user': user,
            'context': context,
            'execution_user': Transaction().user,
        }
