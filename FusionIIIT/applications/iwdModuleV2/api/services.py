from applications.iwdModuleV2.models import *
from applications.filetracking.sdk.methods import *
from notification.views import iwd_notif

from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth.models import User

from decimal import Decimal
from collections import defaultdict
import re

from .serializers import *


def create_request_service(request, serializer, attachment, role):

    with transaction.atomic():

        formObject = serializer.save()

        receiver_desg = "Admin IWD"
        receiver_user = "kunal"

        receiver_user_obj = User.objects.get(username=receiver_user)

        create_file(
            uploader=request.user.username,
            uploader_designation=role,
            receiver=receiver_user,
            receiver_designation=receiver_desg,
            src_module="IWD",
            src_object_id=str(formObject.id),
            file_extra_JSON={"value": 2},
            attached_file=attachment
        )

        iwd_notif(request.user, receiver_user_obj, "Request_added")

        return formObject


def forward_request_service(request, fileid, receiver_user, receiver_desg, remarks, attachment):

    forward_file(
        file_id=fileid,
        receiver=receiver_user,
        receiver_designation=receiver_desg,
        file_extra_JSON={"message": "Request forwarded."},
        remarks=remarks,
        file_attachment=attachment,
    )

    receiver_user_obj = get_object_or_404(User, username=receiver_user)

    iwd_notif(request.user, receiver_user_obj, "file_forward")


def process_bill_service(request, fileid, remarks, attachment, receiver_user, receiver_desg):

    with transaction.atomic():

        request_id = File.objects.get(id=fileid).src_object_id

        forward_file(
            file_id=fileid,
            receiver=receiver_user,
            receiver_designation=receiver_desg,
            file_extra_JSON={"message": "Request forwarded."},
            remarks=remarks,
            file_attachment=attachment,
        )

        Requests.objects.filter(id=request_id).update(
            billProcessed=1,
            status="Final Bill Processed"
        )

        request_instance = Requests.objects.get(pk=request_id)

        bill = Bills.objects.create(
            request_id=request_instance,
            file=attachment
        )

        receiver_user_obj = User.objects.get(username=receiver_user)

        iwd_notif(request.user, receiver_user_obj, "file_forward")

        return bill


def create_proposal_service(serializer, items_list, request_instance):

    with transaction.atomic():

        proposal = serializer.save()

        total_budget = 0

        for item_data in items_list:

            quantity = Decimal(item_data['quantity'])
            price_per_unit = Decimal(item_data['price_per_unit'])

            total_price = quantity * price_per_unit
            total_budget += total_price

            Item.objects.create(
                proposal=proposal,
                name=item_data['name'],
                description=item_data['description'],
                unit=item_data['unit'],
                quantity=quantity,
                price_per_unit=price_per_unit,
                total_price=total_price
            )

        proposal.proposal_budget = total_budget
        proposal.save()

        Requests.objects.filter(id=request_instance.id).update(
            activeProposal=proposal.id,
            estimated_budget=total_budget
        )

        return proposal

def update_request_service(request, data, request_instance, receiver_user, receiver_desg):

    items = defaultdict(dict)

    for key in request.data:
        if key.startswith("items["):
            match = re.match(r"items\[(\d+)\]\[(\w+)\]", key)
            if match:
                index, field = match.groups()
                value = request.data[key]

                if field in ['quantity', 'price_per_unit']:
                    try:
                        value = Decimal(value)
                    except:
                        pass

                items[int(index)][field] = value

    for key in request.FILES:
        if key.startswith("items["):
            match = re.match(r"items\[(\d+)\]\[(\w+)\]", key)
            if match:
                index, field = match.groups()
                items[int(index)][field] = request.FILES.get(key)

    items_list = [items[idx] for idx in sorted(items.keys())]

    serializer = CreateProposalSerializer(data=data)

    if serializer.is_valid():

        with transaction.atomic():

            proposal = serializer.save()

            total_budget = 0

            for item_data in items_list:

                quantity = Decimal(item_data['quantity'])
                price_per_unit = Decimal(item_data['price_per_unit'])

                total_price = quantity * price_per_unit

                total_budget += total_price

                Item.objects.create(
                    proposal=proposal,
                    name=item_data['name'],
                    description=item_data['description'],
                    unit=item_data['unit'],
                    quantity=quantity,
                    price_per_unit=price_per_unit,
                    total_price=total_price
                )

            proposal.proposal_budget = total_budget
            proposal.save()

            Requests.objects.filter(id=request_instance.id).update(
                activeProposal=proposal.id
            )

            return serializer.data
        
def issue_work_order_service(request, data):

    request_id = data.get("request_id")

    with transaction.atomic():

        request_instance = get_object_or_404(Requests, pk=request_id)

        active_proposal = request_instance.activeProposal

        proposal_obj = get_object_or_404(Proposal, pk=active_proposal)

        data['estimate_budget'] = proposal_obj.proposal_budget

        serializer = WorkOrderFormSerializer(data=data)

        if serializer.is_valid():

            serializer.save(request_id=request_instance)

            request_instance.status = "Work Order issued"

            request_instance.issuedWorkOrder = 1

            request_instance.save()

            return {"success": True}

    return {"success": False, "error": serializer.errors}

def handle_dean_process_service(request, fileid, remarks, attachment, receiver_user, receiver_desg):

    with transaction.atomic():

        request_id = File.objects.get(id=fileid).src_object_id

        forward_file(
            file_id=fileid,
            receiver=receiver_user,
            receiver_designation=receiver_desg,
            file_extra_JSON={"message": "Request forwarded."},
            remarks=remarks,
            file_attachment=attachment,
        )

        Requests.objects.filter(id=request_id).update(
            deanProcessed=1,
            status="Approved by the dean",
            directorApproval=0
        )

        receiver_user_obj = User.objects.get(username=receiver_user)

        iwd_notif(request.user, receiver_user_obj, "file_forward")

        return True
    

# -------------------------------
# Director Approval
# -------------------------------
def handle_director_approval_service(request, fileid, action, remarks, attachment, receiver_user, receiver_desg):

    request_id = File.objects.get(id=fileid).src_object_id

    forward_file(
        file_id=fileid,
        receiver=receiver_user,
        receiver_designation=receiver_desg,
        file_extra_JSON={"message": "Request forwarded."},
        remarks=remarks,
        file_attachment=attachment,
    )

    receiver_user_obj = get_object_or_404(User, username=receiver_user)

    iwd_notif(request.user, receiver_user_obj, "file_forward")

    if action == "approve":

        Requests.objects.filter(id=request_id).update(
            directorApproval=1,
            status="Approved by the director"
        )

    elif action == "reject":

        Requests.objects.filter(id=request_id).update(
            directorApproval=-1,
            status="Rejected by the director",
            iwdAdminApproval=0,
            activeProposal=None
        )


# -------------------------------
# Audit Document
# -------------------------------
def audit_document_service(request, fileid, remarks, attachment, receiver_user, receiver_desg):

    request_id = File.objects.get(id=fileid).src_object_id

    forward_file(
        file_id=fileid,
        receiver=receiver_user,
        receiver_designation=receiver_desg,
        file_extra_JSON={"message": "Request forwarded."},
        remarks=remarks,
        file_attachment=attachment,
    )

    Requests.objects.filter(id=request_id).update(
        status="Bill Audited"
    )


# -------------------------------
# Admin Approval
# -------------------------------
def admin_approval_service(request, fileid, action, remarks, attachment, receiver_user, receiver_desg):

    request_id = File.objects.get(id=fileid).src_object_id

    forward_file(
        file_id=fileid,
        receiver=receiver_user,
        receiver_designation=receiver_desg,
        file_extra_JSON={"message": "Request forwarded."},
        remarks=remarks,
        file_attachment=attachment,
    )

    receiver_user_obj = get_object_or_404(User, username=receiver_user)

    iwd_notif(request.user, receiver_user_obj, "file_forward")

    request_instance = Requests.objects.get(id=request_id)

    if action == "approve":

        if request_instance.activeProposal:

            Requests.objects.filter(id=request_id).update(
                iwdAdminApproval=1,
                status="Proposal created"
            )

        else:

            Requests.objects.filter(id=request_id).update(
                iwdAdminApproval=1,
                status="Approved by the IWD Admin"
            )

    elif action == "reject":

        Requests.objects.filter(id=request_id).update(
            iwdAdminApproval=-1,
            status="Rejected",
            activeProposal=None
        )


# -------------------------------
# Work Completed
# -------------------------------
def work_completed_service(request_id):

    Requests.objects.filter(id=request_id).update(
        workCompleted=1,
        status="Work Completed"
    )


# -------------------------------
# Bill Generated
# -------------------------------
def bill_generated_service(request_id):

    if request_id:

        Requests.objects.filter(id=request_id).update(
            status="Bill Generated",
            billGenerated=1
        )

    requests_object = Requests.objects.filter(
        issuedWorkOrder=1,
        billGenerated=0
    )

    obj = []

    for x in requests_object:

        element = {
            "id": x.id,
            "name": x.name,
            "area": x.area,
            "description": x.description,
            "requestCreatedBy": x.requestCreatedBy,
            "workCompleted": x.workCompleted,
        }

        obj.append(element)

    return obj