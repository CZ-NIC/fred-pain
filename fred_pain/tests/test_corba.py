"""Test fred_pain corba interface."""
from datetime import date
from unittest.mock import sentinel

from django.test import SimpleTestCase
from django_pain.models import BankAccount, BankPayment
from djmoney.money import Money
from fred_idl.Registry import Accounting

from fred_pain.corba import AccountingCorbaRecoder


class TestFredPainCorbaRecoder(SimpleTestCase):
    """Test FredPainCorbaRecoder."""

    def test_encode_bankpayment(self):
        """Test encoding of BankPayment."""
        values = [
            ('identifier', 'bank_payment', sentinel.identifier),
            ('uuid', 'uuid', sentinel.uuid),
            ('counter_account_number', 'counter_account_number', sentinel.counter_account_number),
            ('counter_account_name', 'counter_account_name', sentinel.counter_account_name),
            ('constant_symbol', 'constant_symbol', sentinel.constant_symbol),
            ('variable_symbol', 'variable_symbol', sentinel.variable_symbol),
            ('specific_symbol', 'specific_symbol', sentinel.specific_symbol),
            ('description', 'memo', sentinel.description),
        ]

        account = BankAccount(account_number='123', currency='USD')
        payment = BankPayment(account=account, amount=Money('999.00', 'USD'), transaction_date=date(2018, 2, 1),
                              **dict((val[0], val[2]) for val in values))

        recoder = AccountingCorbaRecoder()
        struct = recoder._encode_bankpayment(payment)

        self.assertIsInstance(struct, Accounting.PaymentData)
        self.assertEqual(struct.price, '999.00')
        self.assertEqual(struct.date, '2018-02-01')
        for _, key, val in values:
            self.assertEqual(getattr(struct, key), val)
