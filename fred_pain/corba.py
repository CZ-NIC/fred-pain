#
# Copyright (C) 2018-2019  CZ.NIC, z. s. p. o.
#
# This file is part of FRED.
#
# FRED is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FRED is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FRED.  If not, see <https://www.gnu.org/licenses/>.

"""FRED CORBA interface."""
from datetime import date

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
        self.add_recode_function(date, self._identity, encode_iso_date)

        self.add_recode_function(IsoDate, decode_iso_date, self._identity)
        self.add_recode_function(IsoDateTime, decode_iso_datetime, self._identity)
        self.add_recode_function(Accounting.Money, self._identity, self._identity)
        self.add_recode_function(Accounting.Credit, self._identity, self._identity)

    def _encode_bankpayment(self, payment: BankPayment) -> Accounting.PaymentData:
        """Encode bank payment to struct."""
        return Accounting.PaymentData(
            account_payment_ident=payment.identifier,
            uuid=payment.uuid.hex,
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
