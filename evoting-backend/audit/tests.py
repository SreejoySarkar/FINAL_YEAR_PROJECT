from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.db import close_old_connections, connections
from django.test import TransactionTestCase

from audit.models import AuditLog
from audit.services import compute_hash, log_event


class AuditLogConcurrencyTests(TransactionTestCase):

    reset_sequences = True

    def test_concurrent_events_form_a_valid_chain(self):
        number_of_events = 8
        barrier = Barrier(number_of_events)

        def create_event(worker_number):
            close_old_connections()

            try:
                barrier.wait(timeout=15)

                log_event(
                    action="AUDIT_CONCURRENCY_TEST",
                    details={"worker": worker_number},
                )
            finally:
                connections.close_all()

        with ThreadPoolExecutor(
            max_workers=number_of_events
        ) as executor:
            list(
                executor.map(
                    create_event,
                    range(number_of_events),
                )
            )

        records = list(AuditLog.objects.order_by("id"))

        self.assertEqual(len(records), number_of_events)

        previous_hash = "GENESIS"

        for record in records:
            self.assertEqual(record.prev_hash, previous_hash)

            expected_hash = compute_hash(
                previous_hash,
                record.action,
                record.actor_id,
                record.details,
                record.created_at,
            )

            self.assertEqual(record.event_hash, expected_hash)

            previous_hash = record.event_hash

    def test_failed_transaction_does_not_leave_audit_record(self):
        from django.db import transaction

        initial_count = AuditLog.objects.count()

        try:
            with transaction.atomic():
                log_event(
                    action="AUDIT_ROLLBACK_TEST",
                    details={"test": True},
                )

                raise RuntimeError("Simulated transaction failure")

        except RuntimeError:
            pass

        self.assertEqual(
            AuditLog.objects.count(),
            initial_count,
        )
        
