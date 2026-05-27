from .models import Registration


def promote_from_waitlist(event):
    waitlisted = event.registrations.filter(
        status=Registration.STATUS_WAITLISTED
    ).order_by("registered_at").first()

    if waitlisted and not event.is_full:
        waitlisted.status = Registration.STATUS_CONFIRMED
        waitlisted.save(update_fields=["status"])
        print(f"Promoted {waitlisted.user} from waitlist for {event}")
