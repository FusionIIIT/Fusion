from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from applications.globals.models import HoldsDesignation
from applications.iwdModuleV2.models import *
from .serializers import *

@api_view(['GET'])
def dashboard(request):
    userObj = request.user
    userDesignationObjects = HoldsDesignation.objects.filter(user=userObj)
    eligible = any(p.designation.name == 'Admin IWD' for p in userDesignationObjects)
    return Response({'eligible': eligible})

@api_view(['POST'])
def page1_1(request):
    if request.method == 'POST':
        project_id = request.data.get('name')
        request.session['projectId'] = project_id
        project = Projects(id=project_id)
        project.save()
        
        serializer = PageOneDetailsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(id=project)  # Assign the project instance
            return Response({'message': 'Page One Details Saved!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def AESForm(request):
    if request.method == 'POST':
        serializer = AESDetailsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(key=Projects.objects.get(id=request.session['projectId']))
            return Response({'message': 'AES Details Saved!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def page2_1(request):
    if request.method == 'POST':
        request.session['projectId'] = request.data.get('id')
        serializer = PageTwoDetailsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(id=Projects.objects.get(id=request.session['projectId']))
            return Response({'message': 'Page Two Details Saved!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def corrigendumInput(request):
    if request.method == 'POST':
        existingObject = CorrigendumTable.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
        if existingObject.count() == 1:
            existingObject.delete()

        serializer = CorrigendumTableSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(key=Projects.objects.get(id=request.session['projectId']))
            return Response({'message': 'Corrigendum Input Saved!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def addendumInput(request):
    if request.method == 'POST':
        existingObject = Addendum.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
        if existingObject.count() == 1:
            existingObject.delete()

        serializer = AddendumSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(key=Projects.objects.get(id=request.session['projectId']))
            return Response({'message': 'Addendum Input Saved!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def PreBidForm(request):
    if request.method == 'POST':
        existingObject = PreBidDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
        if existingObject.count() == 1:
            existingObject.delete()

        serializer = PreBidDetailsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(key=Projects.objects.get(id=request.session['projectId']))
            return Response({'message': 'PreBid Form Saved!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def noOfEntriesTechnicalBid(request):
    if request.method == 'POST':
        existingObject = NoOfTechnicalBidTimes.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
        if existingObject.count() == 1:
            existingObject.delete()
        
        serializer = NoOfTechnicalBidTimesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(key=Projects.objects.get(id=request.session['projectId']))
            return Response({'message': 'Number of Entries for Technical Bid Saved!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def TechnicalBidForm(request):
    if request.method == 'POST':
        numberOfTechnicalBidTimes = NoOfTechnicalBidTimes.objects.get(key=Projects.objects.get(id=request.session['projectId'])).number
        existingObject = TechnicalBidDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
        if existingObject.count() == 1:
            existingObject.delete()

        serializer = TechnicalBidDetailsSerializer(data=request.data)
        if serializer.is_valid():
            technical_bid = serializer.save(key=Projects.objects.get(id=request.session['projectId']))
            
            TechnicalBidContractorDetails.objects.filter(key=technical_bid).all().delete()
            for w in range(numberOfTechnicalBidTimes):
                contractor_serializer = TechnicalBidContractorDetailsSerializer(data={
                    'key': technical_bid,
                    'name': request.data.get(f'{w}name'),
                    'description': request.data.get(f'{w}Description'),
                })
                if contractor_serializer.is_valid():
                    contractor_serializer.save()
            
            return Response({'message': 'Technical Bid Form Saved!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST', 'GET'])
def noOfEntriesFinancialBid(request):
    project_id = request.session['projectId']
    objectTechnicalBid = TechnicalBidDetails.objects.get(key=Projects.objects.get(id=project_id))
    objects = TechnicalBidContractorDetails.objects.filter(key=objectTechnicalBid)

    listOfContractors = [t.name for t in objects]

    if request.method == 'POST':
        existingObject = FinancialBidDetails.objects.filter(key=Projects.objects.get(id=project_id))
        if existingObject.count() == 1:
            existingObject.delete()

        serializer = FinancialBidDetailsSerializer(data=request.data)
        if serializer.is_valid():
            financial_bid = serializer.save(key=Projects.objects.get(id=project_id))
            for contractor in listOfContractors:
                contractor_serializer = FinancialContractorDetailsSerializer(data={
                    'key': financial_bid,
                    'name': contractor,
                    'totalCost': request.data[contractor + 'totalCost'],
                    'estimatedCost': request.data[contractor + 'estimatedCost'],
                    'percentageRelCost': request.data[contractor + 'percentageRelCost'],
                    'perFigures': request.data[contractor + 'perFigures'],
                })
                if contractor_serializer.is_valid():
                    contractor_serializer.save()
            return Response({"message": "Financial bid details saved successfully."}, status=status.HTTP_201_CREATED)

    return Response({'list': listOfContractors}, status=status.HTTP_200_OK)

@api_view(['POST', 'GET'])
def letterOfIntent(request):
    if request.method == 'POST':
        existingObject = LetterOfIntentDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
        if existingObject.count() == 1:
            existingObject.delete()

        serializer = LetterOfIntentDetailsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(key=Projects.objects.get(id=request.session['projectId']))
            return Response({"message": "Letter of Intent saved successfully."}, status=status.HTTP_201_CREATED)

    return Response({}, status=status.HTTP_200_OK)


@api_view(['POST', 'GET'])
def workOrderForm(request):
    project_id = request.session.get('projectId')
    if request.method == 'POST':
        existingObject = WorkOrderForm.objects.filter(key=Projects.objects.get(id=project_id))
        if existingObject.exists():
            existingObject.delete()

        serializer = WorkOrderFormSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(key=Projects.objects.get(id=project_id))
            return Response({"message": "Work order saved successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response({}, status=status.HTTP_200_OK)

@api_view(['POST', 'GET'])
def AgreementInput(request):
    project_id = request.session.get('projectId')
    if request.method == 'POST':
        existingObject = Agreement.objects.filter(key=Projects.objects.get(id=project_id))
        if existingObject.exists():
            existingObject.delete()

        serializer = AgreementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(key=Projects.objects.get(id=project_id))
            return Response({"message": "Agreement saved successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response({}, status=status.HTTP_200_OK)

@api_view(['POST', 'GET'])
def milestonesForm(request):
    project_id = request.session.get('projectId')
    if request.method == 'POST':
        serializer = MilestonesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(key=Projects.objects.get(id=project_id))
            return Response({"message": "Milestone saved successfully."}, status=status.HTTP_201_CREATED)

    Milestones.objects.filter(key=Projects.objects.get(id=project_id)).delete()
    return Response({}, status=status.HTTP_200_OK)


@api_view(['POST', 'GET'])
def page3_1(request):
    if request.method == 'POST':
        request.session['projectId'] = request.data['id']
        serializer = PageThreeDetailsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(id=Projects.objects.get(id=request.session['projectId']))
            return Response({"message": "Page 3 details saved successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response({}, status=status.HTTP_200_OK)

@api_view(['POST', 'GET'])
def ExtensionOfTimeForm(request):
    project_id = request.session.get('projectId')
    if request.method == 'POST':
        serializer = ExtensionOfTimeDetailsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(key=Projects.objects.get(id=project_id))
            return Response({"message": "Extension of Time details saved successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response({}, status=status.HTTP_200_OK)

@api_view(['POST'])
def page1View(request):
    request.session['projectId'] = request.data['id']
    projectPageOne = PageOneDetails.objects.get(id=Projects.objects.get(id=request.session['projectId']))
    return Response({'x': projectPageOne}, status=status.HTTP_200_OK)

@api_view(['POST'])
def page2View(request):
    projectPageTwo = PageTwoDetails.objects.get(id=Projects.objects.get(id=request.session['projectId']))
    return Response({'x': projectPageTwo}, status=status.HTTP_200_OK)

@api_view(['GET'])
def AESView(request):
    objects = AESDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    serializer = AESDetailsSerializer(objects, many=True)
    return Response({'AES': serializer.data}, status=status.HTTP_200_OK)

@api_view(['GET'])
def financialBidView(request):
    elements = []
    objects = FinancialBidDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    for f in objects:
        contractorObjects = FinancialContractorDetails.objects.filter(key=f)
        for w in contractorObjects:
            obj = [f.sNo, f.description, w.name, w.estimatedCost, w.percentageRelCost, w.perFigures, w.totalCost]
            elements.append(obj)
    return Response({'financial': elements}, status=status.HTTP_200_OK)

@api_view(['GET'])
def technicalBidView(request):
    elements = []
    objects = TechnicalBidDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    for f in objects:
        contractorObjects = TechnicalBidContractorDetails.objects.filter(key=f)
        for w in contractorObjects:
            obj = [f.sNo, f.requirements, w.name, w.description]
            elements.append(obj)
    return Response({'technical': elements}, status=status.HTTP_200_OK)

@api_view(['GET'])
def preBidDetailsView(request):
    preBidObjects = PreBidDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    serializer = PreBidDetailsSerializer(preBidObjects, many=True)
    return Response({'preBidDetails': serializer.data}, status=status.HTTP_200_OK)

@api_view(['GET'])
def corrigendumView(request):
    try:
        corrigendumObject = CorrigendumTable.objects.get(key=Projects.objects.get(id=request.session['projectId']))
        serializer = CorrigendumTableSerializer(corrigendumObject)
        return Response({'corrigendum': serializer.data}, status=status.HTTP_200_OK)
    except CorrigendumTable.DoesNotExist:
        return Response({'error': 'Corrigendum not found.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def addendumView(request):
    try:
        addendumObject = Addendum.objects.get(key=Projects.objects.get(id=request.session['projectId']))
        serializer = AddendumSerializer(addendumObject)
        return Response({'addendum': serializer.data}, status=status.HTTP_200_OK)
    except Addendum.DoesNotExist:
        return Response({'error': 'Addendum not found.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def letterOfIntentView(request):
    try:
        letterOfIntentObject = LetterOfIntentDetails.objects.get(key=Projects.objects.get(id=request.session['projectId']))
        serializer = LetterOfIntentDetailsSerializer(letterOfIntentObject)
        return Response({'letterOfIntent': serializer.data}, status=status.HTTP_200_OK)
    except LetterOfIntentDetails.DoesNotExist:
        return Response({'error': 'Letter of Intent not found.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def workOrderFormView(request):
    try:
        workOrderFormObject = WorkOrderForm.objects.get(key=Projects.objects.get(id=request.session['projectId']))
        serializer = WorkOrderFormSerializer(workOrderFormObject)
        return Response({'workOrderForm': serializer.data}, status=status.HTTP_200_OK)
    except WorkOrderForm.DoesNotExist:
        return Response({'error': 'Work Order Form not found.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def agreementView(request):
    try:
        agreementObject = Agreement.objects.get(key=Projects.objects.get(id=request.session['projectId']))
        serializer = AgreementSerializer(agreementObject)
        return Response({'agreement': serializer.data}, status=status.HTTP_200_OK)
    except Agreement.DoesNotExist:
        return Response({'error': 'Agreement not found.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def milestoneView(request):
    milestoneObjects = Milestones.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    serializer = MilestonesSerializer(milestoneObjects, many=True)
    return Response({'milestones': serializer.data}, status=status.HTTP_200_OK)

@api_view(['GET'])
def page3View(request):
    try:
        pageThreeDetails = PageThreeDetails.objects.get(key=Projects.objects.get(id=request.session['projectId']))
        serializer = PageThreeDetailsSerializer(pageThreeDetails)
        return Response({'pageThreeDetails': serializer.data}, status=status.HTTP_200_OK)
    except PageThreeDetails.DoesNotExist:
        return Response({'error': 'Page Three Details not found.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def extensionFormView(request):
    extensionObjects = ExtensionOfTimeDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    serializer = ExtensionOfTimeDetailsSerializer(extensionObjects, many=True)
    return Response({'extension': serializer.data}, status=status.HTTP_200_OK)
