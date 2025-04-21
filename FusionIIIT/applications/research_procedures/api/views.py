from rest_framework.viewsets import ModelViewSet
from applications.research_procedures.models import *
from .serializers import *
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticatedOrReadOnly 
from django.shortcuts import redirect, render, get_object_or_404
from rest_framework.response import Response
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from applications.research_procedures.models import *
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation, Faculty
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ObjectDoesNotExist
from notification.views import RSPC_notif
from django.urls import reverse
from django.contrib.auth.decorators import login_required
import datetime
import json
from django.utils import timezone
from collections import defaultdict
from applications.filetracking.sdk.methods import *
from applications.filetracking.models import *
from applications.filetracking.api.serializers import FileHeaderSerializer
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt

def designation_user(designation):
    designation_id = Designation.objects.filter(name=designation).values_list('id', flat=True).first()
    if not designation_id:
        return None
    user_id = HoldsDesignation.objects.filter(designation=designation_id).values_list('working', flat=True).first()
    if not user_id:
        return None
    return User.objects.filter(id=user_id).first()

@api_view(['POST'])
def staff_document_upload(request):
    if request.method == 'POST':
        sid = request.data.get("sid")
        try:
            staff_instance = staff.objects.get(sid=sid)
            for file_field in ["joining_report", "id_card"]:
                if file_field in request.FILES:
                    setattr(staff_instance, file_field, request.FILES[file_field])
            staff_instance.salary_per_month = request.data.get("salary_per_month")
            staff_instance.start_date = request.data.get("start_date")
            # staff_instance.doc_approval = "Pending"
            # RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=designation_user(designation="SectionHead_RSPC"), type="Doc Created")
            RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=User.objects.filter(username=projects.objects.filter(pid=staff_instance.pid_id).first().pi_id).first(), type="Doc Created")
            staff_instance.save()
            return Response(staff_serializer(staff_instance).data, status=status.HTTP_200_OK)
        except staff.DoesNotExist:
            return Response({"Error": "Staff not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def staff_selection_report(request):
    if request.method == 'POST':
        sid = request.data.get("sid")
        try:
            staff_instance = staff.objects.get(sid=sid)
            required_fields = ["candidates_applied", "candidates_called", "candidates_interviewed"]
            if not all(request.data.get(field) for field in required_fields):
                return Response({"Error": "Missing required candidate numbers"}, status=status.HTTP_400_BAD_REQUEST)
        
            final_selection = json.loads(request.data.get("final_selection", "[]"))
            waiting_list = json.loads(request.data.get("waiting_list", "[]"))
            biodata_final = request.FILES.getlist("biodata_final")
            biodata_waiting = request.FILES.getlist("biodata_waiting")
            if (len(biodata_final) != len(final_selection) or len(biodata_waiting) != len(waiting_list)):
                return Response({"Error": "Mismatch between candidate list and resume files"}, status=status.HTTP_400_BAD_REQUEST)

            for field in required_fields:
                setattr(staff_instance, field, request.data.get(field))
            for file_field in ["ad_file", "comparative_file"]:
                if file_field in request.FILES:
                    setattr(staff_instance, file_field, request.FILES[file_field])
            staff_instance.approval = "Committee Approval"
            staff_instance.final_selection = final_selection
            staff_instance.waiting_list = waiting_list
            staff_instance.biodata_final = [
                f"{settings.MEDIA_URL}{default_storage.save(f'RSPC/biodatas/{file.name}', ContentFile(file.read()))}"
                for file in biodata_final
            ]
            staff_instance.biodata_waiting = [
                f"{settings.MEDIA_URL}{default_storage.save(f'RSPC/biodatas/{file.name}', ContentFile(file.read()))}"
                for file in biodata_waiting
            ]

            staff_instance.save()
            for role, members in staff_instance.selection_committee.items():
                if isinstance(members, list):
                    for name in members:
                        recipient = User.objects.filter(username=name).first()
                        if recipient:
                            RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=recipient, type="Report Created")
                else:
                    recipient = User.objects.filter(username=members).first()
                    if recipient:
                        RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=recipient, type="Report Created")
            return Response(staff_serializer(staff_instance).data, status=status.HTTP_200_OK)
        except staff.DoesNotExist:
            return Response({"Error": "Staff not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def committee_action(request):
    if request.method == 'POST':
        sid = request.data.get("sid")
        action = request.data.get("action")
        username = request.user.username
        if not sid or not action:
            return Response({"Error": "Missing staff ID or action"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            staff_instance = staff.objects.get(sid=sid)
            if action == "approve":
                if username not in staff_instance.gave_verdict:
                    staff_instance.gave_verdict.append(username)
                committee_members = set()
                for key, members in staff_instance.selection_committee.items():
                    if key == "Co-PI":
                        if isinstance(members, list):
                            for copi in members:
                                if project_access.objects.filter(pid=staff_instance.pid_id, copi_id=copi, type="Internal").exists():
                                    committee_members.add(copi)
                        else:
                            if project_access.objects.filter(pid=staff_instance.pid_id, copi_id=members, type="Internal").exists():
                                committee_members.add(members)
                    else:
                        if isinstance(members, list):
                            committee_members.update(members)
                        else:
                            committee_members.add(members)
                if committee_members.issubset(set(staff_instance.gave_verdict)):
                    staff_instance.approval = "HoD Forward"
                    RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=designation_user(f"HOD ({projects.objects.filter(pid=staff_instance.pid_id).first().dept})"), type="Committee Complete")
                RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=User.objects.filter(username=projects.objects.filter(pid=staff_instance.pid_id).first().pi_id).first(), type="Committee Approved")
            
            elif action == "reject":
                if staff_instance.biodata_final:
                    for file_path in staff_instance.biodata_final:
                        default_storage.delete(file_path)  # Delete stored files
                if staff_instance.biodata_waiting:
                    for file_path in staff_instance.biodata_waiting:
                        default_storage.delete(file_path)
                if staff_instance.ad_file:
                    default_storage.delete(staff_instance.ad_file.path)
                if staff_instance.comparative_file:
                    default_storage.delete(staff_instance.comparative_file.path)
                staff_instance.candidates_applied = None
                staff_instance.candidates_called = None
                staff_instance.candidates_interviewed = None
                staff_instance.final_selection = []
                staff_instance.waiting_list = []
                staff_instance.biodata_final = []
                staff_instance.gave_verdict = []
                staff_instance.biodata_waiting = []
                staff_instance.approval = "Hiring"
                RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=User.objects.filter(username=projects.objects.filter(pid=staff_instance.pid_id).first().pi_id).first(), type="Report Rejected")

            staff_instance.save()
            return Response({"message": "Verdict recorded. Selection report will be approved once all committee members have voted."}, status=status.HTTP_200_OK)
        except staff.DoesNotExist:
            return Response({"Error": "Staff not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_budget(request):
    pid = request.GET.get('pid') 
    if pid is not None:
        details = budget.objects.filter(pid=pid).first()
        if details:
            response_data = {
                    "manpower": details.manpower,
                    "travel": details.travel,
                    "contingency": details.contingency,
                    "consumables": details.consumables,
                    "equipments": details.equipments,
                    "overhead": details.overhead,
                    "current_funds": details.current_funds
                }
            return Response(response_data, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_200_OK)
    else:
        return Response({"Error": "pid is required"}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def get_staff_positions(request):
    pid = request.GET.get('pid') 
    if pid is not None:
        details = staff_positions.objects.filter(pid=pid).first()
        if details:
            response_data = {
                "positions": details.positions,
                "incumbents": details.incumbents
            }
            return Response(response_data, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_200_OK)
    else:
        return Response({"Error": "pid is required"}, status=status.HTTP_400_BAD_REQUEST)

def create_staff_positions(pid, positions_data):
    positions = {}
    incumbents = {}
    try:
        project_instance = projects.objects.get(pid=pid)  # Get the project instance
    except projects.DoesNotExist:
        raise ValueError(f"Project with pid {pid} does not exist.")
    for pos in positions_data:
        type_name = pos.get("type")
        available_count = int(pos.get("available") or 0)
        occupied_count = int(pos.get("occupied") or 0)
        positions[type_name] = [available_count, occupied_count]
        incumbents[type_name] = pos.get("incumbents", [])
    staff_positions_data = {
        "pid": project_instance,
        "positions": positions,
        "incumbents": incumbents,
    }

    staff_position, created = staff_positions.objects.update_or_create(
        pid=project_instance, defaults=staff_positions_data
    )
    staff_positions_data["pid"]=pid
    serializer = staff_positions_serializer(instance=staff_position, data=staff_positions_data)
    if serializer.is_valid():
        serializer.save()
    else:
        print("Staff Positions Serializer Errors:", serializer.errors)
        raise ValueError(serializer.errors)

# def create_staff_file(request, ad, selection_committee):
#     try:
#         uploader_designation = request.query_params.get('u_d')
#         receiver = request.query_params.get('r')
#         receiver_designation = request.query_params.get('r_d')
#         if not all([uploader_designation, receiver, receiver_designation]):
#             raise ValueError("Missing required query parameters.")

#         file_id = create_file(
#             uploader=request.user.username,
#             uploader_designation=uploader_designation,
#             receiver=receiver,
#             receiver_designation=receiver_designation,
#             subject="New Staff Request",
#             description=f"Staff request created for {ad.get('type')}.",
#             src_module="RSPC",
#             src_object_id="",
#         )
#         print(f"File created successfully with ID: {file_id}")
#         return file_id
#     except Exception as e:
#         print(f"Failed to create file: {e}")
#         raise ValueError("Failed to create file")
    
@api_view(['POST'])
def add_ad_committee(request):
    if request.method == 'POST':
        data=request.data.copy()
        positions_data = json.loads(data.pop('positions', [''])[0])
        advertisements_data = json.loads(data.pop("advertisements", [''])[0])

        members_data = json.loads(data.pop("members", [''])[0])
        selection_committee = {}
        for member in members_data:
            role = member.get("role")
            name = member.get("name")
            recipient = User.objects.filter(username=name).first()
            if recipient:
                RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=recipient, type="Selection Committee")
            if role in selection_committee:
                if isinstance(selection_committee[role], list):
                    selection_committee[role].append(name)
                else:
                    selection_committee[role] = [selection_committee[role], name]
            else:
                selection_committee[role] = name
        try:
            create_staff_positions(int(data.get("pid")), positions_data)
        except ValueError as e:
            return Response({"Error": f"Failed in adding staff positions - {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        for ad in advertisements_data:
            staff_data = {
                "pid": int(data.get("pid")),
                "type": ad.get("type", ""),
                "duration": int(ad.get("duration")),
                "salary": float(ad.get("salary")),
                "eligibility": ad.get("eligibility", ""),
                "has_funds": data.get("has_funds"),
                "submission_date": ad.get("submission_date"),
                "interview_date": ad.get("interview_date"),
                "test_date": ad.get("test_date"),
                "test_mode": ad.get("test_mode"),
                "interview_place": ad.get("interview_place"),
                "approval": "HoD Forward",
                "selection_committee": selection_committee,  # Store members in selection_committee JSON field
            }
            serializer = staff_serializer(data=staff_data)

            if serializer.is_valid():
                staff_instance = serializer.save()
                if request.FILES.get('post_on_website'):
                    staff_instance.post_on_website = request.FILES.get('post_on_website')
                    staff_instance.save()
                RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=designation_user(f"HOD ({projects.objects.filter(pid=staff_data['pid']).first().dept})"), type="Ad Created")
        return Response({"message":"Data added successfully"}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def staff_decision(request):
    if request.method == 'POST':
        sid = request.data.get("sid")
        action = request.data.get("action")
        form = request.data.get("form")
        if not sid or not action:
            return Response({"Error": "Missing staff ID or action"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            staff_instance = staff.objects.get(sid=sid)
            if action == "forward":
                staff_instance.approval = "RSPC Approval"
                staff_instance.current_approver = "rspc_admin"
                staff_instance.save()
                type = "Ad Forwarded" if form == "ad" else "Report Forwarded"
                RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=designation_user(designation="rspc_admin"), type=type)

            elif action == "approve":
                if form == "ad":
                    if staff_instance.current_approver == "rspc_admin":
                        staff_instance.current_approver = "SectionHead_RSPC"
                        staff_instance.save()
                        RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=designation_user(designation="SectionHead_RSPC"), type="Ad Forwarded")
                    else:
                        staff_instance.approval = "Hiring"
                        staff_instance.current_approver = None
                        staff_instance.save()
                        RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=User.objects.filter(username=projects.objects.filter(pid=staff_instance.pid_id).first().pi_id).first(), type="Hiring")
                # elif form == "doc":
                #     staff_instance.doc_approval = "Approved"
                #     staff_instance.save()
                #     RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=User.objects.filter(username=projects.objects.filter(pid=staff_instance.pid_id).first().pi_id).first(), type="Doc Approved")
                elif form == "report":
                    if staff_instance.current_approver == "rspc_admin":
                        staff_instance.current_approver = "SectionHead_RSPC"
                        staff_instance.save()
                        RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=designation_user(designation="SectionHead_RSPC"), type="Report Forwarded")
                    else:
                        staff_instance.approval = "Approved"
                        staff_instance.current_approver = None
                        staff_instance.save()
                        final_selections = staff_instance.final_selection
                        for index, candidate in enumerate(final_selections):
                            name, salary, duration, begin, end = (
                                candidate.get("name"),
                                candidate.get("salary"),
                                candidate.get("duration"),
                                candidate.get("begin"),
                                candidate.get("end"),
                            )
                            if index == 0:
                                staff_instance.person = name
                                staff_instance.salary = salary
                                staff_instance.duration = duration
                                staff_instance.start_date = begin
                                staff_instance.biodata_number = index
                                staff_instance.save()
                            else:
                                final_staff_data = staff_instance.__dict__.copy()
                                final_staff_data.pop("_state")
                                final_staff_data.pop("sid")
                                final_staff_data.update({
                                    "person": name,
                                    "salary": salary,
                                    "duration": duration,
                                    "start_date": begin,
                                    "biodata_number": index,
                                })
                                new_staff_instance = staff.objects.create(**final_staff_data)
                                new_staff_instance.save()
                    
                        staff_pos_instance = staff_positions.objects.filter(pid=staff_instance.pid).first()
                        positions = staff_pos_instance.positions or {}
                        incumbents = staff_pos_instance.incumbents or {}
                        staff_type = staff_instance.type
                        if staff_type in positions:
                            positions[staff_type][1] += len(final_selections)
                        else:
                            positions[staff_type] = [0, len(final_selections)]
                        new_incumbents = [{"name": candidate.get("name"), "date": candidate.get("end")} for candidate in final_selections]
                        if staff_type in incumbents:
                            incumbents[staff_type].extend(new_incumbents)
                        else:
                            incumbents[staff_type] = new_incumbents
                        staff_pos_instance.positions = positions
                        staff_pos_instance.incumbents = incumbents
                        staff_pos_instance.save()
                        RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=User.objects.filter(username=projects.objects.filter(pid=staff_instance.pid_id).first().pi_id).first(), type="Approved")

            elif action == "reject":
                type=""
                if form == "ad":
                    if staff_instance.post_on_website:
                        default_storage.delete(staff_instance.post_on_website.path)
                    staff_instance.delete()
                    type="Ad Rejected"
                elif form == "doc":
                    if staff_instance.joining_report:
                        default_storage.delete(staff_instance.joining_report.path)
                    if staff_instance.id_card:
                        default_storage.delete(staff_instance.id_card.path)
                    staff_instance.doc_approval=None
                    staff_instance.salary_per_month=0
                    staff_instance.save()
                    type="Doc Rejected"
                elif form == "report":
                    if staff_instance.biodata_final:
                        for file_path in staff_instance.biodata_final:
                            default_storage.delete(file_path)  # Delete stored files
                    if staff_instance.biodata_waiting:
                        for file_path in staff_instance.biodata_waiting:
                            default_storage.delete(file_path)
                    if staff_instance.ad_file:
                        default_storage.delete(staff_instance.ad_file.path)
                    if staff_instance.comparative_file:
                        default_storage.delete(staff_instance.comparative_file.path)
                    staff_instance.candidates_applied = None
                    staff_instance.candidates_called = None
                    staff_instance.candidates_interviewed = None
                    staff_instance.final_selection = []
                    staff_instance.waiting_list = []
                    staff_instance.biodata_final = []
                    staff_instance.gave_verdict = []
                    staff_instance.biodata_waiting = []
                    staff_instance.approval = "Hiring"
                    staff_instance.save()
                    type="Report Rejected"
                RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=User.objects.filter(username=projects.objects.filter(pid=staff_instance.pid_id).first().pi_id).first(), type=type)

            return Response({"message": "Action successful"}, status=status.HTTP_200_OK)
        except staff.DoesNotExist:
            return Response({"Error": "Staff not found"}, status=status.HTTP_404_NOT_FOUND)

def get_copis(pid):
    if pid is not None:
        return list(project_access.objects.filter(pid=pid).values_list('copi_id', flat=True))
    return []

def create_budget(pid, budget_data, overhead):
    parsed_budget = {
        "pid": pid, 
        "manpower": [int(year["manpower"]) if year["manpower"] else 0 for year in budget_data],
        "travel": [int(year["travel"]) if year["travel"] else 0 for year in budget_data],
        "contingency": [int(year["contingency"]) if year["contingency"] else 0 for year in budget_data],
        "consumables": [int(year["consumables"]) if year["consumables"] else 0 for year in budget_data],
        "equipments": [int(year["equipments"]) if year["equipments"] else 0 for year in budget_data],
        "overhead": int(overhead) if overhead else 0
    }
    serializer = budget_serializer(data=parsed_budget)
    if serializer.is_valid():
        serializer.save()
    else:
        print("Budget Serializer Errors:", serializer.errors)
        raise ValueError(serializer.errors)

def create_copis(pid, coPIs_data, sender_username):
     for copi in coPIs_data:
        copi["pid"] = pid
        serializer = project_access_serializer(data=copi)
        if serializer.is_valid():
            if(copi["type"]=="Internal"):
                RSPC_notif(sender=User.objects.filter(username=sender_username).first(), recipient=User.objects.filter(username=copi["copi_id"]).first(), type="Co-PI")
            serializer.save()
        else:
            print("Co-PIs Serializer Errors:", serializer.errors)
            raise ValueError(serializer.errors)

@api_view(['POST'])
def add_project(request):
    if request.method == 'POST':
        data=request.data.copy()
        budget_data = json.loads(data.pop('budget', [''])[0])
        coPIs_data = json.loads(data.pop('coPIs', [''])[0])
        overhead = data.pop('overhead', ['0'])[0]

        pi = User.objects.filter(username=data["pi_id"]).first()
        pi_name = f"{pi.first_name} {pi.last_name}"
        data["pi_name"] = pi_name
        serializer = projects_serializer(data=data)
        
        if serializer.is_valid():
            new_project=serializer.save()
            try:
                create_budget(new_project.pid, budget_data, overhead)
                create_copis(new_project.pid, coPIs_data, request.user.username)
            except ValueError as e:
                new_project.delete()
                return Response({"Error": f"Failed in adding CoPIs or Budget - {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
            
            RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=designation_user(designation=f"HOD ({data['dept']})"), type="Proposal Created")
            RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=designation_user(designation="SectionHead_RSPC"), type="Proposal Created")
            return Response(serializer.data, status=status.HTTP_201_CREATED)      
        print("Project Serializer Errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def register_commence_project(request):
    if request.method == 'POST':
        pid = request.POST.get("pid")
        if pid is not None:
            try:
                project_instance = projects.objects.get(pid=pid)
                updatable_fields = ["name", "type", "access", "sponsored_agency", "sanction_date", "sanctioned_amount", "status"] if "sanction_date" in request.POST else ["start_date", "initial_amount", "status"]
                for field in updatable_fields:
                    value = request.POST.get(field)
                    setattr(project_instance, field, value)
                if request.FILES.get('file'):
                    project_instance.file=request.FILES.get('file')
                if request.FILES.get('registration_form'):
                    project_instance.registration_form=request.FILES.get('registration_form')
                if "initial_amount" in request.POST:
                    budget_instance = budget.objects.filter(pid=pid).first()
                    if budget_instance:
                        budget_instance.current_funds = request.POST.get("initial_amount")
                        budget_instance.save()
                project_instance.save()
                
                if "sanction_date" in request.POST:
                    RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=designation_user(designation=f"HOD ({project_instance.dept})"), type="Registration Created")
                    RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=designation_user(designation="SectionHead_RSPC"), type="Registration Created")
                else:
                    RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=User.objects.filter(username=project_instance.pi_id).first(), type="Project Commenced")
                return Response({"message": "Project Details Updated Successfully"}, status=status.HTTP_200_OK)
            except projects.DoesNotExist:
                return Response({"Error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"Error": f"Failed to update project details - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({"Error": "pid is required"}, status=status.HTTP_400_BAD_REQUEST)    

@api_view(['POST'])
def project_closure(request):
    if request.method == 'POST':
        pid = request.data.get('pid')
        if pid is not None:
            try:
                project_instance = projects.objects.get(pid=pid)
                project_instance.end_report=request.FILES.get('end_report', None)
                # project_instance.end_approval="Pending"
                project_instance.status = "Completed"
                project_instance.save()
                RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=designation_user(designation="SectionHead_RSPC"), type="UC/SE Created")
                return Response({"message": "Project Closure Successful"}, status=status.HTTP_200_OK)
            except projects.DoesNotExist:
                return Response({"Error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"Error": f"Failed to close project: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({"Error": "pid is required"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_projects(request):
    pid_list = request.GET.getlist('pids[]')  # Fetching multiple PIDs from query parameters
    all_projects = projects.objects.filter(pid__in=pid_list) if pid_list else projects.objects.all()
    serializer = projects_serializer(all_projects, many=True)
    project_data = serializer.data
    for project in project_data:
        project["copis"] = get_copis(project["pid"])
    return Response(project_data, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_PIDs(request):
    pi_id=request.user.username
    role = request.GET.get('role')
    if pi_id is not None and "Professor" in role:
        PIDs = projects.objects.filter(pi_id=pi_id).values_list('pid', flat=True)
        return Response(PIDs, status=status.HTTP_200_OK)
    elif pi_id is not None and "HOD" in role:
        dept = role.split("(")[-1].strip(")")
        PIDs = projects.objects.filter(dept=dept).values_list('pid', flat=True)
        return Response(PIDs, status=status.HTTP_200_OK)
    elif pi_id is not None and role in {"rspc_admin", "SectionHead_RSPC"}:
        PIDs = projects.objects.values_list('pid', flat=True)
        return Response(PIDs, status=status.HTTP_200_OK)
    else:
        return Response({"Error": "pi_id is required"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_staff(request):
    role = request.GET.get('role')
    type = int(request.GET.get('type'))
    if type == 3:
        pid_list = request.GET.getlist('pids[]')
        all_staff = staff.objects.filter(Q(approval="Approved") & Q(pid__in=pid_list))
        all_project = projects.objects.filter(pid__in=pid_list).values('pid', 'name', 'sponsored_agency', 'duration', 'pi_name', 'start_date')
        project_dict = {proj['pid']: proj for proj in all_project}
        serializer = staff_serializer(all_staff, many=True)
        staff_data = serializer.data
        for entry in staff_data:
            pid = entry["pid"]
            project = project_dict.get(pid, {})
            entry["project_title"] = project.get("name", "")
            entry["sponsor_agency"] = project.get("sponsored_agency", "")
            entry["pi_name"] = project.get("pi_name", "")
            entry["duration_project"] = project.get("duration", "")
            entry["project_start_date"] = project.get("start_date", "")
        return Response(staff_data, status=status.HTTP_200_OK)
    elif type == 1:
            pid_list = request.GET.getlist('pids[]')
            mem_id=request.user.username
            all_staff = staff.objects.filter(pid__in=pid_list)
            all_project = projects.objects.filter(pid__in=pid_list).values('pid', 'name', 'sponsored_agency', 'duration', 'pi_name', 'start_date')
            project_dict = {proj['pid']: proj for proj in all_project}
            serializer = staff_serializer(all_staff, many=True)
            staff_data = serializer.data
            for entry in staff_data:
                pid = entry["pid"]
                project = project_dict.get(pid, {})
                entry["project_title"] = project.get("name", "")
                entry["sponsor_agency"] = project.get("sponsored_agency", "")
                entry["pi_name"] = project.get("pi_name", "")
                entry["duration_project"] = project.get("duration", "")
                entry["project_start_date"] = project.get("start_date", "")
            return Response(staff_data, status=status.HTTP_200_OK)
    elif role is not None and "Professor" in role:
        pid_list = request.GET.getlist('pids[]')
        mem_id=request.user.username
        additional_staff = staff.objects.filter(
            Q(approval="Committee Approval") &
            ~Q(gave_verdict__icontains=mem_id) &
            (Q(selection_committee__icontains=f'"{mem_id}"') | Q(selection_committee__icontains=f"'{mem_id}'"))
        )
        additional_pids = additional_staff.values_list('pid', flat=True).distinct()
        additional_projects = projects.objects.filter(pid__in=additional_pids).values('pid', 'name', 'sponsored_agency', 'duration', 'start_date')
        additional_project_dict = {proj['pid']: proj for proj in additional_projects}
        additional_serializer = staff_serializer(additional_staff, many=True)
        additional_staff_data = additional_serializer.data
        for entry in additional_staff_data:
            pid = entry["pid"]
            project = additional_project_dict.get(pid, {})
            entry["project_title"] = project.get("name", "")
            entry["sponsor_agency"] = project.get("sponsored_agency", "")
            entry["duration_project"] = project.get("duration", "")
            entry["project_start_date"] = project.get("start_date", "")
        return Response(additional_staff_data, status=status.HTTP_200_OK)
    elif role is not None and "HOD" in role:
        pid_list = request.GET.getlist('pids[]')
        all_staff = staff.objects.filter(Q(approval="HoD Forward") & Q(pid__in=pid_list))
        staff_pids = all_staff.values_list('pid', flat=True)
        all_project = projects.objects.filter(pid__in=staff_pids).values('pid', 'name', 'sponsored_agency', 'duration', 'pi_name', 'sanction_date', 'start_date')
        project_dict = {proj['pid']: proj for proj in all_project}
        serializer = staff_serializer(all_staff, many=True)
        staff_data = serializer.data
        for entry in staff_data:
            pid = entry["pid"]
            project = project_dict.get(pid, {})
            entry["project_title"] = project.get("name", "")
            entry["sponsor_agency"] = project.get("sponsored_agency", "")
            entry["sanction_date"] = project.get("sanction_date", "")
            entry["project_start_date"] = project.get("start_date", "")
            entry["pi_name"] = project.get("pi_name", "")
            entry["duration_project"] = project.get("duration", "")
        return Response(staff_data, status=status.HTTP_200_OK)
    
    elif role is not None and role in {"rspc_admin", "SectionHead_RSPC"}:
        all_staff = staff.objects.filter(Q(approval="RSPC Approval") & Q(current_approver=role))
        # all_staff = staff.objects.filter(approval="Submitted")
        staff_pids = all_staff.values_list('pid', flat=True)
        all_project = projects.objects.filter(pid__in=staff_pids).values('pid', 'name', 'sponsored_agency', 'duration', 'pi_name', 'sanction_date', 'start_date')
        project_dict = {proj['pid']: proj for proj in all_project}
        serializer = staff_serializer(all_staff, many=True)
        staff_data = serializer.data
        for entry in staff_data:
            pid = entry["pid"]
            project = project_dict.get(pid, {})
            entry["project_title"] = project.get("name", "")
            entry["sponsor_agency"] = project.get("sponsored_agency", "")
            entry["sanction_date"] = project.get("sanction_date", "")
            entry["project_start_date"] = project.get("start_date", "")
            entry["pi_name"] = project.get("pi_name", "")
            entry["duration_project"] = project.get("duration", "")
        return Response(staff_data, status=status.HTTP_200_OK)
    return Response({"Error": "Role is required"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_profIDs(request):
    faculty_entries = Faculty.objects.all()
    prof_ids = [faculty.id.user.username for faculty in faculty_entries]  # Assuming ExtraInfo has a user field
    return Response({"profIDs": prof_ids}, status=status.HTTP_200_OK)
    pid = request.GET.get('pid') 
    if pid is not None:
        try:
            project_instance = projects.objects.get(pid=pid)
            project_instance.status = "Completed"
            project_instance.save()
            sender_notif = User.objects.get(username=request.user.username)
            recipient_notif = User.objects.get(username=project_instance.pi_id)
            RSPC_notif(sender=sender_notif, recipient=recipient_notif, type="Over")
            return Response({"message": "Project Ending Successful"}, status=status.HTTP_200_OK)
        except projects.DoesNotExist:
            return Response({"Error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": f"Failed to complete project: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({"Error": "pid is required"}, status=status.HTTP_400_BAD_REQUEST)