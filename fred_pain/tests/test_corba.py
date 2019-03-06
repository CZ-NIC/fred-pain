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

"""Test fred_pain corba interface."""
import uuid
from datetime import date, datetime
from unittest.mock import sentinel

from django.test import SimpleTestCase
from django_pain.models import BankAccount, BankPayment
from djmoney.money import Money
from fred_idl.Registry import Accounting, IsoDate, IsoDateTime
from pytz import utc

from fred_pain.corba import AccountingCorbaRecoder


class TestFredPainCorbaRecoder(SimpleTestCase):
    """Test FredPainCorbaRecoder."""

    def test_encode_bankpayment(self):
        """Test encoding of BankPayment."""
        values = [
            ('identifier', 'account_payment_ident', sentinel.identifier),
            ('counter_account_number', 'counter_account_number', sentinel.counter_account_number),
            ('counter_account_name', 'counter_account_name', sentinel.counter_account_name),
            ('constant_symbol', 'constant_symbol', sentinel.constant_symbol),
            ('variable_symbol', 'variable_symbol', sentinel.variable_symbol),
            ('specific_symbol', 'specific_symbol', sentinel.specific_symbol),
            ('description', 'memo', sentinel.description),
        ]

        account = BankAccount(account_number='123', currency='USD')
        payment = BankPayment(account=account, amount=Money('999.00', 'USD'), transaction_date=date(2018, 2, 1),
                              create_time=datetime(2018, 2, 1, 15, 0, 0, tzinfo=utc),
                              uuid=uuid.UUID('6dfcab4c-fe4d-4b85-a659-6000d38d0672'),
                              **dict((val[0], val[2]) for val in values))

        recoder = AccountingCorbaRecoder()
        struct = recoder._encode_bankpayment(payment)

        self.assertIsInstance(struct, Accounting.PaymentData)
        self.assertIsInstance(struct.price, Accounting.Money)
        self.assertEqual(struct.price.value, '999.00')
        self.assertIsInstance(struct.date, IsoDate)
        self.assertEqual(struct.date.value, '2018-02-01')
        self.assertIsInstance(struct.creation_time, IsoDateTime)
        self.assertEqual(struct.creation_time.value, '2018-02-01T15:00:00+00:00')
        self.assertEqual(struct.uuid, '6dfcab4cfe4d4b85a6596000d38d0672')
        for _, key, val in values:
            self.assertEqual(getattr(struct, key), val)
