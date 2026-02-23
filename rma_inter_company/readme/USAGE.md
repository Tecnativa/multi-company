#. Create an RMA in Company A.
#. Confirm the RMA from Company A.
#. The RMA from Company B will be confirmed automatically.
#. Reception picking for RMA A will have Transit Location defined as the destination location.
#. Reception picking for RMA B will have Transit Location defined as the origin location.
#. When validating the reception picking for RMA B, the reception picking for RMA A will be auto-done first.
#. When creating a delivery picking (return or replace) in RMA B, it will also be created in RMA A.
#. The RMA B delivery picking will have Transit Location as its destination location.
#. The RMA A delivery picking will have Transit Location as its origin location.
#. When validating the RMA B delivery picking, the RMA A delivery picking will be automatically done.

#. If RMA B is canceled, RMA A is automatically canceled.
#. If RMA B is confirmed, RMA A is automatically confirmed.
#. If RMA B is returned (using the return or replace button), RMA A is automatically returned.