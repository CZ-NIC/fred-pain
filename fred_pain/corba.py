"""FRED CORBA interface."""
from django.utils.functional import SimpleLazyObject
from django_pain.models import BankPayment
from fred_idl.Registry import Accounting, IsoDate, IsoDateTime
from pyfco import CorbaClient, CorbaClientProxy, CorbaNameServiceClient, CorbaRecoder
from pyfco.recoder import decode_iso_date, decode_iso_datetime, encode_iso_date, encode_iso_datetime

from fred_pain.settings import SETTINGS


class AccountingCorbaRecoder(CorbaRecoder):
    """Recoder for Accounting interface."""

    def __init__(self, coding='ascii'):
        """Add specific recode functions."""
        super().__init__(coding)
        self.add_recode_function(BankPayment, self._identity, self._encode_bankpayment)

        self.add_recode_function(IsoDate, decode_iso_date, self._identity)
        self.add_recode_function(IsoDateTime, decode_iso_datetime, self._identity)
        self.add_recode_function(Accounting.Money, self._identity, self._identity)
        self.add_recode_function(Accounting.Credit, self._identity, self._identity)

    def _encode_bankpayment(self, payment: BankPayment) -> Accounting.PaymentData:
        """Encode bank payment to struct."""
        return Accounting.PaymentData(
            bank_payment_ident=payment.identifier,
            uuid=payment.uuid,
            account_number=payment.account.account_number,
            counter_account_number=payment.counter_account_number,
            counter_account_name=payment.counter_account_name,
            constant_symbol=payment.constant_symbol,
            variable_symbol=payment.variable_symbol,
            specific_symbol=payment.specific_symbol,
            price=Accounting.Money(value=str(payment.amount.amount)),
            date=encode_iso_date(payment.transaction_date),
            memo=payment.description,
            creation_time=encode_iso_datetime(payment.create_time),
        )


_CORBA = CorbaNameServiceClient(host_port=SETTINGS.corba_netloc, context_name=SETTINGS.corba_context)

_ACCOUNTING = SimpleLazyObject(lambda: _CORBA.get_object('Accounting', Accounting.AccountingIntf))  # pragma: no cover
ACCOUNTING = CorbaClientProxy(
    CorbaClient(_ACCOUNTING, AccountingCorbaRecoder('utf-8'), Accounting.INTERNAL_SERVER_ERROR))
