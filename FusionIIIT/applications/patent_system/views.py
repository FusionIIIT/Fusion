from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
import json

# -----------------------------------------
# 🔹 Applicant Views
# -----------------------------------------

def applicant_dashboard(request):
    return JsonResponse({"message": "Applicant Dashboard"})


def applicant_main_dashboard(request):
    return JsonResponse({"message": "Applicant Main Dashboard"})


def view_applications(request):
    applications = list(PatentApplication.objects.values("id", "title", "status"))
    return JsonResponse({"applications": applications})


def saved_drafts(request):
    drafts = list(PatentApplication.objects.filter(status="Draft").values("id", "title"))
    return JsonResponse({"drafts": drafts})


@csrf_exempt
def submit_application(request):
    if request.method == "POST":
        data = json.loads(request.body)
        application = PatentApplication.objects.create(
            title=data["title"], description=data["description"], status="Submitted"
        )
        return JsonResponse({"message": "Application submitted", "app_id": application.id})
    return JsonResponse({"error": "Invalid request method"}, status=405)


def applicant_notifications(request):
    return JsonResponse({"notifications": ["Patent approved", "Review required"]})


def application_form(request):
    return JsonResponse({"message": "Load application form"})


def ip_filing_form(request):
    return JsonResponse({"message": "Load IP filing form"})


def status_view(request):
    return JsonResponse({"message": "View application status"})


# -----------------------------------------
# 🔹 Director Views
# -----------------------------------------

def director_main_dashboard(request):
    return JsonResponse({"message": "Director Main Dashboard"})


def director_dashboard(request):
    return JsonResponse({"message": "Director Dashboard"})


@csrf_exempt
def director_accept_reject(request):
    if request.method == "POST":
        data = json.loads(request.body)
        try:
            application = PatentApplication.objects.get(id=data["app_id"])
            application.status = data["status"]
            application.save()
            return JsonResponse({"message": f"Application {data['status']} by Director"})
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Application not found"}, status=404)
    return JsonResponse({"error": "Invalid request method"}, status=405)


def recents_view(request):
    recents = list(PatentApplication.objects.order_by("-updated_at").values("id", "title", "status")[:5])
    return JsonResponse({"recent_applications": recents})


def pending_reviews(request):
    pending = list(PatentApplication.objects.filter(status="Pending").values("id", "title"))
    return JsonResponse({"pending_reviews": pending})


def reviewed_applications(request):
    reviewed = list(PatentApplication.objects.filter(status="Reviewed").values("id", "title"))
    return JsonResponse({"reviewed_applications": reviewed})


def active_applications(request):
    active = list(PatentApplication.objects.filter(status="Active").values("id", "title"))
    return JsonResponse({"active_applications": active})


def director_status_view(request):
    return JsonResponse({"message": "Director Status View"})


def director_notifications(request):
    return JsonResponse({"notifications": ["New submission", "Pending review"]})


def submitted_applications(request):
    submitted = list(PatentApplication.objects.filter(status="Submitted").values("id", "title"))
    return JsonResponse({"submitted_applications": submitted})


# -----------------------------------------
# 🔹 PCC Admin Views
# -----------------------------------------

def pcc_admin_main_dashboard(request):
    return JsonResponse({"message": "PCC Admin Main Dashboard"})


def pcc_admin_dashboard(request):
    return JsonResponse({"message": "PCC Admin Dashboard"})


def review_applications(request):
    applications = list(PatentApplication.objects.filter(status="Under Review").values("id", "title"))
    return JsonResponse({"review_applications": applications})


@csrf_exempt
def manage_attorney(request):
    if request.method == "POST":
        data = json.loads(request.body)
        return JsonResponse({"message": f"Attorney assigned to application {data['app_id']}"})
    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def notify_applicant(request):
    if request.method == "POST":
        data = json.loads(request.body)
        return JsonResponse({"message": f"Notification sent to applicant of application {data['app_id']}"})
    return JsonResponse({"error": "Invalid request method"}, status=405)


def downloads_page(request):
    return JsonResponse({"message": "Downloads Page"})


def insights_page(request):
    return JsonResponse({"message": "Insights Page"})


def pcc_admin_status_view(request):
    return JsonResponse({"message": "PCC Admin Status View"})
