from blinker import Namespace

_signals = Namespace()

#: This signal is emitted once a record has been created
#:
#: Arguments:
#:
#:  * sender: The name of the model (not the object)
#:  * ids: The id of the record created
#:
#: Caveats: Do remember that it is likely that the record
#: is immediately modified by overwriting the create method.
#: The signal is emitted when the ORM saves the record.
record_created = _signals.signal('record.created')


#: This signal is emitted once a record has been edited
#:
#: Arguments:
#:
#:  * sender: The name of the model (not the object)
#:  * ids: The id of the record created
record_updated = _signals.signal('record.updated')

#: This signal is emitted once a record has been deleted
#:
#: Arguments:
#:
#:  * sender: The name of the model (not the object)
#:  * ids: The id of the record created
#:
#: XXX: Not sure how this can be useful, since the ids
#: indicate deletion, but not necessarily find them again.
record_deleted = _signals.signal('record.deleted')
