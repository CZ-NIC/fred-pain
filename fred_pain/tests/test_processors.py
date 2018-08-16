"""Test fred_pain paypemnt processor."""
from unittest.mock import call, patch

from django.test import SimpleTestCase
from django_pain.models import BankAccount, BankPayment
from django_pain.processors import ProcessPaymentResult
from djmoney.money import Money
from fred_idl.Registry import Accounting
from pyfco.utils import CorbaAssertMixin

from fred_pain.corba import ACCOUNTING
from fred_pain.processors import FredPaymentProcessor


def get_address(**kwargs):
    """Return sample PlaceAddress."""
    defaults = {
        'street1': '2311 North Los Robles Avenue',
        'street2': None,
        'street3': None,
        'city': 'Pasadena',
        'stateorprovince': 'California',
        'postalcode': '91001',
        'country_code': 'USA',
    }
    defaults.update(kwargs)
    return Accounting.PlaceAddress(**defaults)


def get_registrar(**kwargs):
    """Return sample Registrar."""
    defaults = {
        'handle': 'REG-BBT',
        'name': 'Sheldon Cooper',
        'organization': 'Caltech',
        'cin': '',
        'tin': '',
        'url': 'http://sheldon.example.com',
        'phone': None,
        'fax': None,
        'address': get_address(),
    }
    defaults.update(kwargs)
    return Accounting.Registrar(**defaults)


@patch('fred_pain.corba.ACCOUNTING.client')
class TestFredPaymentProcessor(CorbaAssertMixin, SimpleTestCase):
    """Test FredPaymentProcessor."""

    def setUp(self):
        """Set up common variables."""
        self.processor = FredPaymentProcessor()
        self.account = BankAccount(account_number='123', currency='USD')
        self.payment = BankPayment(identifier='PAYMENT', uuid='UUID', account=self.account,
                                   amount=Money('999.00', 'USD'))

    def test_process_payments_success(self, corba_mock):
        """Test process_payments with successful credit increase."""
        ACCOUNTING.get_registrar_by_payment.return_value = (get_registrar(handle='REG-BBT'), 'CZ')
        ACCOUNTING.import_payment.return_value = Accounting.Credit(value='42')

        self.assertEqual(
            list(self.processor.process_payments([self.payment])),
            [ProcessPaymentResult(True, 'Registrar payment')]
        )
        self.assertCorbaCallsEqual(corba_mock.mock_calls, [
            call.get_registrar_by_payment(self.payment),
            call.import_payment(self.payment),
            # call.increase_zone_credit_of_registrar('UUID', 'REG-BBT', 'CZ', '42')
        ])

    def test_process_payments_no_credit(self, corba_mock):
        """Test process_payments with no credit increase (all the money went to decreasing debt)."""
        ACCOUNTING.get_registrar_by_payment.return_value = (get_registrar(handle='REG-BBT'), 'CZ')
        ACCOUNTING.import_payment.return_value = Accounting.Credit(value='0')

        self.assertEqual(
            list(self.processor.process_payments([self.payment])),
            [ProcessPaymentResult(True, 'Registrar payment')]
        )
        self.assertCorbaCallsEqual(corba_mock.mock_calls, [
            call.get_registrar_by_payment(self.payment),
            call.import_payment(self.payment),
        ])

    def test_process_payments_registrar_not_found(self, corba_mock):
        """Test process_payments with REGISTRAR_NOT_FOUND exception."""
        ACCOUNTING.get_registrar_by_payment.side_effect = Accounting.REGISTRAR_NOT_FOUND

        self.assertEqual(
            list(self.processor.process_payments([self.payment])),
            [ProcessPaymentResult(False, 'Registrar payment')]
        )
        self.assertCorbaCallsEqual(corba_mock.mock_calls, [
            call.get_registrar_by_payment(self.payment),
        ])

    def test_assign_payment(self, corba_mock):
        """Test assign_payment method."""
        ACCOUNTING.get_registrar_by_handle_and_payment.return_value = (get_registrar(handle='REG-BBT'), 'CZ')
        ACCOUNTING.import_payment_by_registrar_handle.return_value = Accounting.Credit(value='42')

        self.assertEqual(
            self.processor.assign_payment(self.payment, 'REG-BBT'),
            ProcessPaymentResult(True, 'Registrar payment')
        )
        self.assertCorbaCallsEqual(corba_mock.mock_calls, [
            call.get_registrar_by_handle_and_payment('REG-BBT', self.payment),
            call.import_payment_by_registrar_handle(self.payment, 'REG-BBT'),
        ])

    def test_get_client_choices(self, corba_mock):
        """Test get_client_choices method."""
        ACCOUNTING.get_registrar_references.return_value = (
            Accounting.RegistrarReference(handle='SW', name='Star Wars'),
            Accounting.RegistrarReference(handle='ST', name='Star Trek'),
        )
        self.assertEqual(self.processor.get_client_choices(), {
            'SW': 'Star Wars (SW)',
            'ST': 'Star Trek (ST)',
        })
