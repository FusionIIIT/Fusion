from django.db import IntegrityError, transaction
from django.db.models import F

from .models import Budget, Club, ClubMember, GalleryItem, PollOption, PollVote


def update_club_status(club, status):
    club.status = status
    club.save()
    return club


def upload_club_calendar(club, file_url):
    club.activity_calendar = file_url
    club.save()
    return club


def create_membership_request(*, user, club, description=""):
    return ClubMember.objects.create(student=user, club=club, description=description, status="open")


def update_membership(member, *, status, remarks=""):
    member.status = status
    member.remarks = remarks or member.remarks
    member.save()
    return member


def create_event(*, serializer, created_by):
    return serializer.save(status="open", created_by=created_by)


def update_event_status(event, status):
    event.status = status
    event.save()
    return event


def create_budget(*, serializer, requested_by):
    return serializer.save(status="open", requested_by=requested_by)


def approve_budget(budget_id, *, remarks="Approved"):
    with transaction.atomic():
        budget = Budget.objects.select_for_update().select_related("club").get(pk=budget_id)
        club = Club.objects.select_for_update().get(pk=budget.club_id)
        avail = club.alloted_budget - club.spent_budget
        if budget.status == "confirmed":
            return budget, club, avail
        budget.status = "confirmed"
        budget.remarks = remarks
        budget.save()
        club.spent_budget += budget.amount
        club.save()
        return budget, club, avail


def reject_budget(budget, *, remarks="Rejected"):
    budget.status = "rejected"
    budget.remarks = remarks
    budget.save()
    return budget


def create_poll(*, serializer, created_by):
    return serializer.save(created_by=created_by)


def delete_poll(poll):
    poll.delete()


def cast_vote(*, poll, option, voter):
    try:
        PollVote.objects.create(poll=poll, option=option, voter=voter)
    except IntegrityError as exc:
        raise exc
    PollOption.objects.filter(pk=option.pk).update(votes=F("votes") + 1)
    option.refresh_from_db()
    return poll


def create_gallery_item(*, serializer, uploaded_by):
    return serializer.save(uploaded_by=uploaded_by)


def delete_gallery_item(item):
    item.delete()
