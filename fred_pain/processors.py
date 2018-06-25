"""FRED payment processors."""
from decimal import Decimal
from typing import Iterable

from django_pain.models import BankPayment
from django_pain.processors import AbstractPaymentProcessor
from fred_idl.Registry import Accounting

from fred_pain.corba import ACCOUNTING


class FredPaymentProcessor(AbstractPaymentProcessor):
    """FRED payment processor."""

    def process_payments(self, payments: Iterable[BankPayment]) -> Iterable[bool]:
        """Process payment through FRED."""
        for payment in payments:
            try:
                registrar, zone = ACCOUNTING.get_registrar_by_payment(payment)
                credit = ACCOUNTING.import_payment(payment)
                if Decimal(credit) > 0:
                    ACCOUNTING.increase_zone_credit_of_registrar(payment.uuid, registrar.handle, zone, credit)

            except (Accounting.INTERNAL_SERVER_ERROR, Accounting.REGISTRAR_NOT_FOUND, Accounting.INVALID_ZONE,
                    Accounting.INVALID_CREDIT_VALUE):
                yield False
            except Accounting.CREDIT_ALREADY_PROCESSED:
                # This can happen if connection error occurs after increasing credit in backend.
                # When we try to send the payment again, in another processing, backend recognizes
                # payment uuid and throws this exception.
                yield True
            else:
                yield True
