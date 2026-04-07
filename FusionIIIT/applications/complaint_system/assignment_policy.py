"""Assignment policy lookup for complaint auto-assignment.

This module keeps assignment policy decisions isolated from API views.
"""

# Explicit policy overrides for high-signal routes.
# Key: (complaint_type, location)
ASSIGNMENT_POLICIES = {
    ("internet", "hall-3"): {
        "team": "hall-3-caretaker-team",
        "strict_area": True,
        "fallback_chain": ("area_and_category", "category_only", "any_worker"),
    },
    ("Electricity", "Admin building"): {
        "team": "admin-maintenance-team",
        "strict_area": True,
        "fallback_chain": ("area_and_category", "category_only", "any_worker"),
    },
}

# Per-location defaults used when no explicit (category, location) policy is found.
LOCATION_DEFAULT_POLICY = {
    "hall-1": {
        "team": "hall-1-caretaker-team",
        "strict_area": True,
        "fallback_chain": ("area_and_category", "category_only", "any_worker"),
    },
    "hall-3": {
        "team": "hall-3-caretaker-team",
        "strict_area": True,
        "fallback_chain": ("area_and_category", "category_only", "any_worker"),
    },
    "hall-4": {
        "team": "hall-4-caretaker-team",
        "strict_area": True,
        "fallback_chain": ("area_and_category", "category_only", "any_worker"),
    },
}


def lookup_assignment_policy(complaint_type, location):
    """Return assignment policy and source marker.

    Source values:
    - explicit: exact category + location rule found
    - location-default: location-wide default found
    - global-default: safe catch-all fallback
    """
    explicit = ASSIGNMENT_POLICIES.get((complaint_type, location))
    if explicit:
        return {**explicit, "source": "explicit"}

    location_policy = LOCATION_DEFAULT_POLICY.get(location)
    if location_policy:
        return {**location_policy, "source": "location-default"}

    return {
        "team": "general-maintenance-team",
        "strict_area": False,
        "fallback_chain": ("category_only", "any_worker"),
        "source": "global-default",
    }
