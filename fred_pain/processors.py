"""FRED payment processors."""
import logging
from typing import Iterable, Optional

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
from django_pain.constants import InvoiceType
from django_pain.models import BankPayment, Client, Invoice
from django_pain.processors import AbstractPaymentProcessor, ProcessPaymentResult
from fred_idl.Registry import Accounting

from fred_pain.corba import ACCOUNTING
from fred_pain.settings import SETTINGS

INVOICE_TYPE_MAP = {
    Accounting.InvoiceType.advance: InvoiceType.ADVANCE,
    Accounting.InvoiceType.account: InvoiceType.ACCOUNT,
}

LOGGER = logging.getLogger(__name__)


class FredPaymentProcessor(AbstractPaymentProcessor):
    """FRED payment processor."""

    default_objective = _('Registrar payment')

    def process_payments(self, payments: Iterable[BankPayment]) -> Iterable[ProcessPaymentResult]:
        """Process payment through FRED."""
        for payment in payments:
            yield self.process_payment(payment)

    def assign_payment(self, payment: BankPayment, client_id: str) -> ProcessPaymentResult:
        """Force assign payment to FRED."""
        LOGGER.debug('Manually assigning payment %s to registrar %s.', str(payment.uuid), client_id)
        return self.process_payment(payment, client_id)

    def process_payment(self, payment: BankPayment, client_id: Optional[str] = None):
        """Process one payment."""
        try:
            if client_id is None:
                registrar, zone = ACCOUNTING.get_registrar_by_payment(payment)
                invoices, credit = ACCOUNTING.import_payment(payment)
            else:
                registrar, zone = ACCOUNTING.get_registrar_by_handle_and_payment(client_id, payment)
                invoices, credit = ACCOUNTING.import_payment_by_registrar_handle(payment, registrar.handle)

        except (Accounting.INTERNAL_SERVER_ERROR, Accounting.REGISTRAR_NOT_FOUND, Accounting.INVALID_PAYMENT_DATA):
            LOGGER.debug('Payment %s rejected.', str(payment.uuid))
            return ProcessPaymentResult(result=False)
        except Accounting.CREDIT_ALREADY_PROCESSED:
            # This can happen if connection error occurs after increasing credit in backend.
            # When we try to send the payment again, in another processing, backend recognizes
            # payment uuid and throws this exception.
            LOGGER.debug('Payment %s was already processed.', str(payment.uuid))
            return ProcessPaymentResult(result=True)
        else:
            LOGGER.debug('Payment %s accepted. %s invoices attached.', str(payment.uuid), len(invoices))
            client = Client(handle=registrar.handle, remote_id=registrar.id, payment=payment)
            client.save()

            for invoice in invoices:
                inv, created = Invoice.objects.get_or_create(number=invoice.number, defaults={
                    'remote_id': invoice.id, 'invoice_type': INVOICE_TYPE_MAP[invoice.type]})
                if not created:
                    if inv.remote_id != invoice.id:
                        LOGGER.error('Invoice number %s already exists with id=%s (received id=%s)',
                                     invoice.number, inv.remote_id, invoice.id)
                    if inv.invoice_type == InvoiceType.ADVANCE:
                        LOGGER.error('Advance invoice number %s is already associated with different payment.',
                                     invoice.number)
                inv.payments.add(payment)

            return ProcessPaymentResult(result=True)

    @staticmethod
    def get_client_choices() -> dict:
        """
        Get registrar handles and names.

        Registrar handle is appended to registrar name.
        """
        registrars = {}
        for reg in ACCOUNTING.get_registrar_references():
            registrars[reg.handle] = '{} ({})'.format(reg.name, reg.handle)
        return registrars


class FredDaphnePaymentProcessor(FredPaymentProcessor):
    """FRED payment processor with links to Daphne webadmin tool."""

    def __init__(self, *args, **kwargs):
        """Check mandatory settings."""
        if not SETTINGS.daphne_url:
            raise ImproperlyConfigured('Setting FRED_PAIN_DAPHNE_URL is mandatory '
                                       'when using FredDaphnePaymentProcessor')
        super().__init__(*args, **kwargs)

    @staticmethod
    def get_invoice_url(invoice: Invoice) -> str:
        """Get invoice url in Daphne."""
        return '{}/invoice/detail/?id={}'.format(SETTINGS.daphne_url, invoice.remote_id)

    @staticmethod
    def get_client_url(client: Client) -> str:
        """Get registrar url in Daphne."""
        return '{}/registrar/detail/?id={}'.format(SETTINGS.daphne_url, client.remote_id)
