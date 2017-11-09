from django.shortcuts import render
from applications.globals.models import Feedback, Issue, IssueImage
from applications.globals.forms import WebFeedbackForm, IssueForm
from Fusion.settings import LOGIN_URL
from django.contrib.auth.decorators import login_required
from PIL import Image

def index(request):
    context = {}

    return render(request, "globals/index1.html", context)


def login(request):
    context = {}

    return render(request, "globals/login.html", context)


def dashboard(request):
    context = {}

    return render(request, "dashboard/dashboard.html", context)


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
		if int(user_rating) > 0 and int(user_rating) <6:
			feedback.rating = user_rating
			feedback.save()
		form = WebFeedbackForm(instance=feedback)
		stars = []
		for i in range(0,int(feedback.rating)):
			stars.append(1)
		rating = 0
		for feed in Feedback.objects.all():
			rating = rating + feed.rating
		if Feedback.objects.all().count() > 0:
			rating = rating/Feedback.objects.all().count()
		context = { 'form':form, "feedback":feedback,'rating':rating, "stars":stars, "reviewed":True, "feeds":feeds }
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
		context = {"form":form, "rating":rating, "feeds":feeds}
		return render(request, "globals/feedback.html", context)
	stars = []
	for i in range(0,int(feedback.rating)):
		stars.append(1)
	context = {"rating":rating, "feedback":feedback, "stars":stars, "form":form,"reviewed":True, "feeds":feeds}
	return render(request, "globals/feedback.html", context)



@login_required(login_url=LOGIN_URL)
def issue(request):
	openissue = Issue.objects.filter(closed=False)
	closedissue = Issue.objects.filter(closed=True)
	if request.method == "POST":
		form = IssueForm(request.POST or None)
		if form.is_valid():
			issue = form.save(commit=False)
			issue.user = request.user
			issue.save()
			for image in request.FILES.getlist('images'):
				try:
					im = Image.open(image)
					image = IssueImage.objects.create(image = image, user=request.user)
					issue.images.add(image)
				except Exception as e:
					print(e)
			issue.save()
			return render(request, "globals/issue.html")
		return render(request, "globals/issue.html")
	form = IssueForm()
	context = { "form":form, "openissue":openissue, "closedissue":closedissue, }
	return render(request, "globals/issue.html", context)