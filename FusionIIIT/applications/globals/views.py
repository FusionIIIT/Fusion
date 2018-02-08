import json

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from PIL import Image

from applications.globals.forms import IssueForm, WebFeedbackForm
from applications.globals.models import Feedback, Issue, IssueImage
from Fusion.settings import LOGIN_URL


def index(request):
    context = {}
    return render(request, "globals/index1.html", context)


def login(request):
    context = {}
    return render(request, "globals/login.html", context)


@login_required(login_url=LOGIN_URL)
def dashboard(request):
    context = {}
    return render(request, "dashboard/dashboard.html", context)


@login_required(login_url=LOGIN_URL)
def logout_view(request):
    logout(request)
    return redirect("/")


""" Views for Feedback and Issue reports """


@login_required(login_url=LOGIN_URL)
def feedback(request):
    feeds = Feedback.objects.all().order_by("rating").exclude(user=request.user)
    if feeds.count() > 5:
        feeds = feeds[:5]
    rated = []
    for feed in feeds:
        rated.append(range(feed.rating))
    feeds = zip(feeds, rated)
    if request.method == "POST":
        try:
            feedback = Feedback.objects.get(user=request.user)
        except:
            feedback = None
        if feedback:
            form = WebFeedbackForm(request.POST or None, instance=feedback)
        else:
            form = WebFeedbackForm(request.POST or None)
        feedback = form.save(commit=False)
        user_rating = request.POST.get("rating")
        feedback.user = request.user
        if int(user_rating) > 0 and int(user_rating) < 6:
            feedback.rating = user_rating
            feedback.save()
        form = WebFeedbackForm(instance=feedback)
        stars = []
        for i in range(0, int(feedback.rating)):
            stars.append(1)
        rating = 0
        for feed in Feedback.objects.all():
            rating = rating + feed.rating
        if Feedback.objects.all().count() > 0:
            rating = rating/Feedback.objects.all().count()
        context = {
            'form': form,
            "feedback": feedback,
            'rating': rating,
            "stars": stars,
            "reviewed": True,
            "feeds": feeds
        }
        return render(request, "globals/feedback.html", context)
    rating = 0
    for feed in Feedback.objects.all():
        rating = rating + feed.rating
    if Feedback.objects.all().count() > 0:
        rating = rating/Feedback.objects.all().count()
    try:
        feedback = Feedback.objects.get(user=request.user)
        form = WebFeedbackForm(instance=feedback)
    except:
        form = WebFeedbackForm()
        context = {"form": form, "rating": rating, "feeds": feeds}
        return render(request, "globals/feedback.html", context)
    stars = []
    for i in range(0, int(feedback.rating)):
        stars.append(1)
    context = {
        "rating": rating,
        "feedback": feedback,
        "stars": stars,
        "form": form,
        "reviewed": True,
        "feeds": feeds
    }
    return render(request, "globals/feedback.html", context)


@login_required(login_url=LOGIN_URL)
def issue(request):
    if request.method == "POST":
        form = IssueForm(request.POST or None)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.user = request.user
            issue.save()
            for image in request.FILES.getlist('images'):
                try:
                    Image.open(image)
                    image = IssueImage.objects.create(image=image, user=request.user)
                    issue.images.add(image)
                except Exception as e:
                    pass
            issue.save()
            openissue = Issue.objects.filter(closed=False)
            closedissue = Issue.objects.filter(closed=True)
            form = IssueForm()
            context = {"form": form, "openissue": openissue, "closedissue": closedissue, }
            return render(request, "globals/issue.html", context)
        openissue = Issue.objects.filter(closed=False)
        closedissue = Issue.objects.filter(closed=True)
        form = IssueForm(request.POST)
        context = {"form": form, "openissue": openissue, "closedissue": closedissue, }
        return render(request, "globals/issue.html", context)
    openissue = Issue.objects.filter(closed=False)
    closedissue = Issue.objects.filter(closed=True)
    form = IssueForm()
    context = {"form": form, "openissue": openissue, "closedissue": closedissue, }
    return render(request, "globals/issue.html", context)


@login_required(login_url=LOGIN_URL)
def view_issue(request, id):
    if request.method == "POST":
        issue = get_object_or_404(Issue, id=id, user=request.user)
        form = IssueForm(request.POST or None, instance=issue)
        if form.is_valid():
            issue.save()
            remove = request.POST.get("remove-images")
            if remove:
                for img in issue.images.all():
                    img.delete()
            for image in request.FILES.getlist('images'):
                try:
                    Image.open(image)
                    image = IssueImage.objects.create(image=image, user=request.user)
                    issue.images.add(image)
                except Exception as e:
                    pass
            issue.save()
            form = IssueForm(instance=issue)
            context = {
                "form": form,
                "issue": issue,
            }
            return render(request, "globals/view_issue.html", context)
        form = IssueForm(request.POST or None)
        context = {
            "form": form,
            "issue": issue,
        }
        return render(request, "globals/view_issue.html", context)
    issue = get_object_or_404(Issue, id=id)
    form = None
    if request.user == issue.user:
        form = IssueForm(instance=issue)
    context = {
        "form": form,
        "issue": issue,
    }
    return render(request, "globals/view_issue.html", context)


@login_required(login_url=LOGIN_URL)
def support_issue(request, id):
    issue = get_object_or_404(Issue, id=id)
    supported = True
    if request.user in issue.support.all():
        issue.support.remove(request.user)
        supported = False
    else:
        issue.support.add(request.user)
    support_count = issue.support.all().count()
    context = {
        "supported": supported,
        "support_count": support_count,
    }
    return HttpResponse(json.dumps(context), "application/json")
