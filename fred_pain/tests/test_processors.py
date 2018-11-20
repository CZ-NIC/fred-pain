"""Test fred_pain paypemnt processor."""
from datetime import date
from unittest.mock import call, patch
from uuid import UUID

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django_pain.constants import InvoiceType
from django_pain.models import BankAccount, BankPayment, Client, Invoice
from django_pain.processors import ProcessPaymentResult
from djmoney.money import Money
from fred_idl.Registry import Accounting
from pyfco.utils import CorbaAssertMixin
from testfixtures import LogCapture

from fred_pain.corba import ACCOUNTING
from fred_pain.processors import FredDaphnePaymentProcessor, FredPaymentProcessor


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
        'id': 1,
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
class TestFredPaymentProcessor(CorbaAssertMixin, TestCase):
    """Test FredPaymentProcessor."""

    def setUp(self):
        """Set up common variables."""
        self.processor = FredPaymentProcessor()
        self.account = BankAccount(account_number='123', currency='USD')
        self.account.save()
        self.payment = BankPayment(identifier='PAYMENT', uuid=UUID('00000000-0000-0000-0000-000000000000'),
                                   account=self.account, amount=Money('999.00', 'USD'),
                                   transaction_date=date(2018, 1, 1))
        self.payment.save()
        self.log_handler = LogCapture('fred_pain.processors', propagate=False)

    def tearDown(self):
        self.log_handler.uninstall()

    def test_process_payments_success(self, corba_mock):
        """Test process_payments with successful credit increase."""
        ACCOUNTING.get_registrar_by_payment.return_value = (get_registrar(handle='REG-BBT', id=1), 'CZ')
        ACCOUNTING.import_payment.return_value = ([], Accounting.Credit(value='42'))

        self.assertEqual(
            list(self.processor.process_payments([self.payment])),
            [ProcessPaymentResult(True)]
        )
        self.assertQuerysetEqual(Client.objects.all().values_list('handle', 'remote_id', 'payment'), [
            ('REG-BBT', 1, self.payment.pk)
        ], transform=tuple)
        self.assertCorbaCallsEqual(corba_mock.mock_calls, [
            call.get_registrar_by_payment(self.payment),
            call.import_payment(self.payment),
        ])
        self.log_handler.check(
            ('fred_pain.processors', 'DEBUG',
             'Payment 00000000-0000-0000-0000-000000000000 accepted. 0 invoices attached.'),
        )

    def test_process_payments_credit_already_processed(self, corba_mock):
        """Test process_payments with CREDIT_ALREADY_PROCESSED exception."""
        ACCOUNTING.get_registrar_by_payment.return_value = (get_registrar(handle='REG-BBT'), 'CZ')
        ACCOUNTING.import_payment.side_effect = Accounting.CREDIT_ALREADY_PROCESSED

        self.assertEqual(
            list(self.processor.process_payments([self.payment])),
            [ProcessPaymentResult(True)]
        )
        self.assertCorbaCallsEqual(corba_mock.mock_calls, [
            call.get_registrar_by_payment(self.payment),
            call.import_payment(self.payment),
        ])
        self.log_handler.check(
            ('fred_pain.processors', 'DEBUG', 'Payment 00000000-0000-0000-0000-000000000000 was already processed.'),
        )

    def test_process_payments_registrar_not_found(self, corba_mock):
        """Test process_payments with REGISTRAR_NOT_FOUND exception."""
        ACCOUNTING.get_registrar_by_payment.side_effect = Accounting.REGISTRAR_NOT_FOUND

        self.assertEqual(
            list(self.processor.process_payments([self.payment])),
            [ProcessPaymentResult(False)]
        )
        self.assertCorbaCallsEqual(corba_mock.mock_calls, [
            call.get_registrar_by_payment(self.payment),
        ])
        self.log_handler.check(
            ('fred_pain.processors', 'DEBUG', 'Payment 00000000-0000-0000-0000-000000000000 rejected.'),
        )

    def test_assign_payment(self, corba_mock):
        """Test assign_payment method."""
        ACCOUNTING.get_registrar_by_handle_and_payment.return_value = (get_registrar(handle='REG-BBT'), 'CZ')
        ACCOUNTING.import_payment_by_registrar_handle.return_value = (
            [Accounting.InvoiceReference(id=42, number='INV42', type=Accounting.InvoiceType.advance)],
            Accounting.Credit(value='42')
        )

        self.assertEqual(
            self.processor.assign_payment(self.payment, 'REG-BBT'),
            ProcessPaymentResult(True)
        )
        self.assertQuerysetEqual(Invoice.objects.all().values_list('number', 'remote_id', 'invoice_type', 'payments'), [
            ('INV42', 42, InvoiceType.ADVANCE, self.payment.pk)
        ], transform=tuple)
        self.assertCorbaCallsEqual(corba_mock.mock_calls, [
            call.get_registrar_by_handle_and_payment('REG-BBT', self.payment),
            call.import_payment_by_registrar_handle(self.payment, 'REG-BBT'),
        ])
        self.log_handler.check(
            ('fred_pain.processors', 'DEBUG',
             'Manually assigning payment 00000000-0000-0000-0000-000000000000 to registrar REG-BBT.'),
            ('fred_pain.processors', 'DEBUG',
             'Payment 00000000-0000-0000-0000-000000000000 accepted. 1 invoices attached.'),
        )

    def test_assign_payment_invoice_exists(self, corba_mock):
        """Test assign_payment method when invoice already exists."""
        ACCOUNTING.get_registrar_by_handle_and_payment.return_value = (get_registrar(handle='REG-BBT'), 'CZ')
        ACCOUNTING.import_payment_by_registrar_handle.return_value = (
            [Accounting.InvoiceReference(id=42, number='INV42', type=Accounting.InvoiceType.advance)],
            Accounting.Credit(value='42')
        )
        invoice = Invoice(remote_id=42, number='INV42', invoice_type=InvoiceType.ADVANCE)
        invoice.save()
        self.processor.assign_payment(self.payment, 'REG-BBT'),

        self.assertQuerysetEqual(invoice.payments.all().values_list('pk'), [(self.payment.pk,)], transform=tuple)

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


@override_settings(FRED_PAIN_DAPHNE_URL='http://example.com')
@patch('fred_pain.corba.ACCOUNTING.client')
class TestFredDaphnePaymentProcessor(CorbaAssertMixin, TestCase):
    """Test FredDaphnePaymentProcessor."""

    def setUp(self):
        """Set up common variables."""
        self.processor = FredDaphnePaymentProcessor()
        self.account = BankAccount(account_number='123', currency='USD')
        self.account.save()
        self.payment = BankPayment(identifier='PAYMENT', uuid=UUID('00000000-0000-0000-0000-000000000000'),
                                   account=self.account, amount=Money('999.00', 'USD'),
                                   transaction_date=date(2018, 1, 1))
        self.payment.save()

    def test_get_invoice_url(self, corba_mock):
        """Test get_invoice_url method."""
        self.assertEqual(self.processor.get_invoice_url(Invoice(remote_id=42)),
                         'http://example.com/invoice/detail/?id=42')

    def test_get_client_url(self, corba_mock):
        """Test get_client_url method."""
        self.assertEqual(self.processor.get_client_url(Client(remote_id=42)),
                         'http://example.com/registrar/detail/?id=42')

    def test_not_configured(self, corba_mock):
        """Test not configured properly."""
        with override_settings(FRED_PAIN_DAPHNE_URL=''):
            with self.assertRaisesRegex(
                    ImproperlyConfigured,
                    'Setting FRED_PAIN_DAPHNE_URL is mandatory when using FredDaphnePaymentProcessor'):
                FredDaphnePaymentProcessor()
