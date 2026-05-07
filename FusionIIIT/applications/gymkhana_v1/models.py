from django.conf import settings
from django.db import models
from django.utils import timezone


VENUE_CHOICES = [
    ("CR101", "CR101"),
    ("CR102", "CR102"),
    ("L101", "L101"),
    ("L102", "L102"),
    ("Football Ground", "Football Ground"),
    ("Cricket Ground", "Cricket Ground"),
    ("Basketball Ground", "Basketball Ground"),
    ("Auditorium", "Auditorium"),
    ("OAT", "OAT"),
    ("Other", "Other"),
]

INDOOR_VENUES = ["CR101", "CR102", "L101", "L102", "Auditorium"]
OUTDOOR_VENUES = ["Football Ground", "Cricket Ground", "Basketball Ground", "OAT"]


class Club(models.Model):
    CATEGORY_CHOICES = [("Technical", "Technical"), ("Sports", "Sports"), ("Cultural", "Cultural")]
    STATUS_CHOICES = [("open", "Open"), ("confirmed", "Confirmed"), ("rejected", "Rejected")]

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="gymkhana_v1_coordinating_clubs",
    )
    co_coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="gymkhana_v1_co_coordinating_clubs",
    )
    faculty_incharge = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    alloted_budget = models.PositiveIntegerField(default=0)
    spent_budget = models.PositiveIntegerField(default=0)
    activity_calendar = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def avail_budget(self):
        return self.alloted_budget - self.spent_budget


class ClubMember(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("member", "Member"),
        ("coordinator", "Coordinator"),
        ("Co-cordinator", "Co-Coordinator"),
        ("rejected", "Rejected"),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="gymkhana_v1_memberships",
    )
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="members")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    description = models.TextField(blank=True)
    remarks = models.CharField(max_length=256, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "club")

    def __str__(self):
        return f"{self.student} -> {self.club} [{self.status}]"


class Event(models.Model):
    STATUS_CHOICES = [("open", "Open"), ("confirmed", "Confirmed"), ("rejected", "Rejected")]

    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="events")
    name = models.CharField(max_length=200)
    venue = models.CharField(max_length=50, choices=VENUE_CHOICES, default="Other")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    incharge = models.CharField(max_length=100)
    details = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.club})"


class Budget(models.Model):
    TYPE_CHOICES = [("club", "Club"), ("fest", "Fest")]
    STATUS_CHOICES = [("open", "Open"), ("confirmed", "Confirmed"), ("rejected", "Rejected")]

    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="budgets")
    budget_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="club")
    budget_for = models.CharField(max_length=200)
    amount = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    remarks = models.CharField(max_length=256, blank=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.club} - {self.budget_for} (Rs.{self.amount})"


class Poll(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    pub_date = models.DateField(default=timezone.now)
    exp_date = models.DateField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        return self.exp_date >= timezone.localdate()


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=200)
    votes = models.PositiveIntegerField(default=0)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]


class PollVote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="votes")
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE)
    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("poll", "voter")


class GalleryItem(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="gallery", null=True, blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="gallery", null=True, blank=True)
    caption = models.CharField(max_length=300, blank=True)
    image_url = models.CharField(max_length=500)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
