"""
Version lifecycle rules for the timetable API.

Kept free of Django imports so the decisions can be unit-tested without a
database; the views do the locking and the writes.
"""

PUBLISHABLE_STATUSES = ('Draft', 'UnderReview', 'Approved')


def plan_publication(target_id, term_statuses, target_has_slots):
    """Decide a publish request for one version.

    ``term_statuses`` maps every version of the target's term (including the
    target) to its status, read while those rows are locked.  Returns
    (error_message, ids_to_archive); error_message is None when allowed.
    Every other Published version of the term is archived, so the term ends
    with exactly one published version even if earlier data had several.
    """
    status = term_statuses[target_id]
    if status not in PUBLISHABLE_STATUSES:
        return f'Cannot publish a version with status={status}.', []
    if not target_has_slots:
        return 'Cannot publish a version that has no scheduled slots.', []
    others = sorted(pk for pk, s in term_statuses.items()
                    if s == 'Published' and pk != target_id)
    return None, others
