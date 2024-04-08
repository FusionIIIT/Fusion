import json
import os
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.http.response import HttpResponse,HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.conf import settings
from django.core.files.storage import default_storage

from .forms import AnswerForm, ProfileForm
from .models import (AllTags, AnsweraQuestion, AskaQuestion, Comments, Reply,
                     hidden, report, tags, Profile, Roles, QuestionAccessControl)
from applications.globals.models import ExtraInfo
from django.contrib.auth.models import User
from django.core.paginator import Paginator
import math
from django.contrib.messages import constants as message_constants
from django.contrib import messages
from django.urls import reverse

PAGE_SIZE = 4
# Create your views here.
@login_required
def feeds(request):
    """
    This function opens the homepage of feeds module after authenticatng the user,
    shows questions from page 1 , if not requested a spcefic page
    @param:
        request - contains metadata about the requested page
    @variables:
        query - fetches questions from database sorted by latest upload time (latest questions are shown first)
        paginator - no of contacts per page
        total_page - assigned total number of pages
    """
    query = AskaQuestion.objects.prefetch_related('select_tag','likes','dislikes','requests').order_by('-uploaded_at')
    paginator = Paginator(query, PAGE_SIZE) # Show 25 contacts per page.
    total_page = math.ceil(query.count()/PAGE_SIZE)
    if request.GET.get("page_number") :
        current_page = int(request.GET.get("page_number"))
    else:
        current_page = 1
    previous_page = current_page - 1
    next_page = current_page + 1
    keyword = ""
    # query = paginator.page(current_page)
    if request.GET.get("search") and request.GET.get('keyword') :
        q = request.GET.get('keyword')
        questions = AskaQuestion.objects.prefetch_related('select_tag','likes','dislikes','requests').all()
        result = questions.filter(Q(subject__icontains=q) | Q(description__icontains=q)).order_by('-uploaded_at')
        query = result
        paginator = Paginator(query, PAGE_SIZE)
        keyword = q.split(" ")
        keyword = "+".join(keyword)
        total_page = math.ceil(query.count()/PAGE_SIZE)

    if request.method == 'POST':

        if request.POST.get('add_qus') :
            question = AskaQuestion.objects.create(user=request.user)
            question.subject = request.POST.get('subject')
            question.description = request.POST.get('content')
            if request.FILES :
                question.file = request.FILES['file']
            tag = request.POST.get('Add_Tag')
            tag = tag[8:]
            ques_tag = []
            result = []
            ques_tag = [int(c) for c in tag.split(",")]

            for i in range(0, len(ques_tag)):
                result = AllTags.objects.get(id=ques_tag[i])
                question.select_tag.add(result)

            if request.POST.get('anonymous'):
                question.anonymous_ask = True;
            else:
                question.anonymous_ask = False;
            question.save()
            messages.success(request,"Question Posted Successfully !")

            role_check = Roles.objects.select_related().filter(user=request.user)
            if len(role_check) >0 :
                access = QuestionAccessControl.objects.create(question=question, canVote=True, canAnswer=True, canComment = True, posted_by = role_check[0])
                if request.POST.get("RestrictVote"):
                    access.canVote = False
                if request.POST.get("RestrictAnswer"):
                    access.canAnswer = False
                if request.POST.get("RestrictComment"):
                    access.canComment = False
                access.save()
                return redirect("/feeds/admin")
            query = AskaQuestion.objects.prefetch_related('select_tag','likes','dislikes','requests').order_by('-uploaded_at')

        if request.POST.get('search'):
            q = request.POST.get('keyword')
            questions = AskaQuestion.objects.prefetch_related('select_tag','likes','dislikes','requests').all()
            result = questions.filter(Q(subject__icontains=q) | Q(description__icontains=q)).order_by('-uploaded_at')
            query = result
            paginator = Paginator(query, PAGE_SIZE)

        # adding user's favourite tags
        if request.POST.get("add_tag"):
            fav_tag=request.POST.get('tag')                                     # returning string
            a = []
            fav_tag = fav_tag[4:]
            a= [int(c) for c in fav_tag.split(",")]                             # listing queery objects

            for i in range(0, len(a)):
                temp = AllTags.objects.get(pk=a[i])
                new = tags.objects.create(user=request.user,my_subtag=temp)
                new.my_tag = temp.tag
                new.save()
            return redirect("/feeds")

    all_tags = AllTags.objects.values('tag').distinct()
    askqus_subtags = AllTags.objects.all()

    user_tags = tags.objects.select_related().values("my_tag").distinct().filter(Q(user__username=request.user.username))
    u_tags = tags.objects.select_related().all().filter(Q(user__username=request.user.username))
    a_tags = tags.objects.select_related().values('my_subtag').filter(Q(user__username=request.user.username))
    ques = []
    try:
        query = paginator.page(current_page)
    except:
        query = []

    hid = hidden.objects.select_related('user').prefetch_related('question__select_tag','question__likes','question__dislikes','question__requests').all()
    for q in query:
        isliked = 0
        isdisliked = 0
        hidd = 0
        isSpecial = 0
        profi = Profile.objects.select_related().all().filter(user=q.user)
        if(q.likes.all().filter(username=request.user.username).count()==1):
            isliked = 1
        if(hid.all().filter(user=request.user, question = q).count()==1):
            hidd = 1
        if(q.dislikes.all().filter(username=request.user.username).count()==1):
            isdisliked = 1
        access_check = QuestionAccessControl.objects.filter(question=q)
        if len(access_check)>0:
            isSpecial = 1
        temp = {
            'access' : access_check,
            'isSpecial' : isSpecial,
            'profile':profi,
            'ques' : q,
            'isliked':isliked,
            'hidd' : hidd,
            'disliked': isdisliked,
            'votes':q.total_likes() - q.total_dislikes(),
        }
        ques.append(temp)
    add_tag_list = AllTags.objects.all()
    add_tag_list = add_tag_list.exclude(pk__in=a_tags)
    role_data = Roles.objects.select_related().all()
    context ={
        'role' : role_data,
        'hidden' : hid,
        'form_answer': AnswerForm(),
        'Tags': user_tags,
        'questions': ques,
        'username': request.user.username,
        'subtags': askqus_subtags,
        'add_tag_list' : add_tag_list,
        'pages' : {
            'current_page' : current_page,
            'total_page' : total_page,
            'previous_page' : previous_page,
            'next_page' : next_page,
        },
        "keyword": keyword,
        'a': u_tags.filter(Q(my_tag__icontains='CSE')),
        'b' : u_tags.filter(Q(my_tag__icontains='ECE')),
        'c' : u_tags.filter(Q(my_tag__icontains='Mechanical')),
        'd' : u_tags.filter(Q(my_tag__icontains='Technical-Clubs')),
        'e' : u_tags.filter(Q(my_tag__icontains='Cultural-Clubs')),
        'f' : u_tags.filter(Q(my_tag__icontains='Sports-Clubs')),
        'g' : u_tags.filter(Q(my_tag__icontains='Business-and-Career')),
        'h' : u_tags.filter(Q(my_tag__icontains='Entertainment')),
        'i' : u_tags.filter(Q(my_tag__icontains='IIITDMJ-Campus')),
        'j' : u_tags.filter(Q(my_tag__icontains='Jabalpur-city')),
        'k' : u_tags.filter(Q(my_tag__icontains='IIITDMJ-Rules-and-Regulations')),
        'l' : u_tags.filter(Q(my_tag__icontains='Academics')),
        'm' : u_tags.filter(Q(my_tag__icontains='IIITDMJ')),
        'n' : u_tags.filter(Q(my_tag__icontains='Life-Relationship-and-Self')),
        'o' : u_tags.filter(Q(my_tag__icontains='Technology-and-Education')),
        'p' : u_tags.filter(Q(my_tag__icontains='Programmes')),
        'q' : u_tags.filter(Q(my_tag__icontains='Others')),
        'r' : u_tags.filter(Q(my_tag__icontains='Design')),
    }
    # return render(request, 'feeds/feeds_main.html', context)
    return render(request,'feeds/feeds_main.html', context)

def Request(request):
    """
    This function requests a question based on it's id
    @param:
        request - contains metadata about the requested page
    @variable:
    question - question object (from database models)
    """
    question = get_object_or_404(AskaQuestion, id=request.POST.get('id'))
    question.is_requested = False

    if question.requests.filter(id=request.user.id).exists():
        question.requests.remove(request.user)
        question.is_requested = False
        question.save()
    else:
        question.requests.add(request.user)
        question.is_requested = True
        question.save()

    context ={
        'question' : question,
        'question.is_requested' : question.is_requested,
        'question.total_requests' : question.total_requests(),
    }

    if request.is_ajax():
        html = render_to_string('feeds/question_request_count.html', context, request=request)
        return JsonResponse({'form': html})

# Ajax called for comments to saved and display them
def Comment_Text(request):
    """
    This function is to make comment on a particular question
    @param:
        request- contains metadata about the requested page

    """
    if request.method == 'POST':
        question = get_object_or_404(AskaQuestion, id=request.POST.get('id'))
        comment = Comments.objects.create(user=request.user,question=question)
        comment.comment_text = request.POST.get('comment_box')
        comment.save()
        msg = request.POST.get('comment_box', None)

        context = {
            'question': question,
            'comment': comment,
            'msg': msg,
        }
        # obj = json.dumps(context)

        # comment = Comments.objects.order_by('-commented_at')
        # return HttpResponse(obj, content_type='application/json')

        if request.is_ajax():
            html = render_to_string('feeds/comment_text.html', context, request=request)
            return JsonResponse({'form': html})

def Reply_Text(request):
    """
    This function is used for answering any selected question
    @param:
        contains metadata about the requested page

    """
    if request.method == 'POST':
        question = get_object_or_404(AskaQuestion, id=request.POST.get('ques_id'))
        comment = get_object_or_404(Comments, id=request.POST.get('id'))
        reply = Reply.objects.create(user=request.user, comment=comment)
        reply.content = request.POST.get('comment_box')

        reply.save()
        msg = request.POST.get('comment_box', None)

        context = {
            'question': question,
            'comment': comment,
            'reply': reply,
            'msg': msg,
        }
        # obj = json.dumps(context)

        # comment = Comments.objects.order_by('-commented_at')
        # return HttpResponse(obj, content_type='application/json')

        if request.is_ajax():
            html = render_to_string('feeds/comment_text.html', context, request=request)
            return JsonResponse({'form': html})

@login_required
def LikeComment(request):
    """
    This function is for liking any comment on any question or answer
    @param:
        request - contians metadata about the requested page
    @variables :
        comment - contains Comments model objects based on a question's id
    """
    # question = get_object_or_404(AskaQuestion, id=request.POST.get('id'))
    comment = Comments.objects.get(id=request.POST.get('id'))
    # comment.question = question

    if comment.is_liked:
        comment.is_liked = False
        comment.likes_comment.remove(request.user)
        comment.save()
    else:
        comment.is_liked = True
        comment.likes_comment.add(request.user)
        comment.save()

    context ={
        'comment' : comment,
        'comment.is_liked' : comment.is_liked,
        # 'comment.likes': comment.like,
        'comment.total_likes_comment' : comment.total_likes_comment(),
    }


    if request.is_ajax():
        html = render_to_string('feeds/like_section_comment.html', context, request=request)
        return JsonResponse({'form': html})

def delete_comment(request):
    """
    The 'delete_comment' function is for deleting commnents on a question
    @param:
        request - contains metadata about the requested page
    """
    if request.method == 'POST':
        comment_id = request.POST.get("comment_id")
        comment = Comments.objects.filter(pk=comment_id)
        comment.delete()
        return JsonResponse({"done":1})

def delete_answer(request):
    """
    The 'delete_answer' function is for deleting a answer
    @param:
        request - contains metadata about the requested page
    """
    if request.method == 'POST':
        answer_id = request.POST.get("answer_id")
        answer = AnsweraQuestion.objects.filter(pk=answer_id)
        answer.delete()
        return JsonResponse({"done":1})

def delete_post(request, id):
    """
    The 'delete_post' function is for deleting a post
    @param:
        request - contains metadata about the requested page
    """
    if request.method == 'POST' and request.POST.get("delete"):
        ques = AskaQuestion.objects.prefetch_related('select_tag','likes','dislikes','requests').filter(pk=id)[0]
        if ques.file:
            pth = os.path.join(settings.BASE_DIR, '..')
            default_storage.delete(pth+ques.file.url)
        ques.delete()
        messages.success(request,"Post deleted successfully !")
        return redirect ('/feeds/')

def hide_post(request, id):
    """
    This function hides a post when we click on the hide button given inside the three dots on left of a post
    @param:
        request - contains metadata about the requested page
    """
    if request.method == 'POST' and request.POST.get("hide"):
        ques = AskaQuestion.objects.prefetch_related('select_tag','likes','dislikes','requests').filter(pk=id)[0]
        hid = hidden(user = request.user, question = ques);
        hid.save()
        messages.success(request,"Post was hidden successfully !")
    return redirect ('/feeds/')

def unhide_post(request, id):
    """
    This function unhides a post when we click on the unhide button given inside the three dots on left of a post if the post is hidden
    @param:
        request - contains metadata about the requested page
    """
    if request.method == 'POST' and request.POST.get("unhide"):
        ques = AskaQuestion.objects.prefetch_related('select_tag','likes','dislikes','requests').filter(pk=id)[0]
        hid = hidden.objects.select_related('user').prefetch_related('question__select_tag','question__likes','question__dislikes','question__requests').filter(user=request.user )
        hid.delete()
        messages.success(request,"Post was unhidden successfully !")
    return redirect ('/feeds/')

def update_post(request, id):
    """
    update_post function makes us able to update a post with new details
    @param :
        request - contains metadata of requested page
    @variables:
        redirect_to : used to redirect us to feeds homepage when a post is updated
    """
    redirect_to = "/feeds"
    if request.method == 'POST' and request.POST.get("update"):
        question= AskaQuestion.objects.prefetch_related('select_tag','likes','dislikes','requests').get(pk=id)
        question.subject = request.POST.get('subject')
        question.description = request.POST.get('description')

        tag = request.POST.get('Add_Tag')
        tag = tag[8:]
        ques_tag = []
        result = []
        ques_tag = [int(c) for c in tag.split(",")]


        for i in range(0, len(ques_tag)):
            result = AllTags.objects.get(id=ques_tag[i])
            question.select_tag.add(result)

        if request.POST.get('anonymous_update')==None :
            question.user= request.user
            question.anonymous_ask=False
        else :
            question.anonymous_ask=True

        if request.POST.get("isSpecial"):
            access = QuestionAccessControl.objects.filter(Question = question)[0]
            if request.POST.get("RestrictVote"):
                access.canVote = False
            else:
                access.canVote = True
            if request.POST.get("RestrictAnswer"):
                access.canAnswer = False
            else:
                access.canAnswer = True
            if request.POST.get("RestrictComment"):
                access.canComment = False
            else:
                access.canComment = True
            access.save()
        if request.POST.get("from_url"):
            redirect_to = request.POST.get("from_url")
        question.save()
        messages.success(request,"Post updated successfully !")
        return redirect (redirect_to)

@login_required
def TagsBasedView(request, string):
    """
    This function makes us able to select posts based on a selected tag or tags like if want the posts posted under CSE tag , we can choose CSE tag to get all those posts
    @param:
        request - contains metadata about the requested page
        string - contians the selected tags
    @variables:
        questions - questions object from model AskaQuestion
    """

    questions = AskaQuestion.objects.prefetch_related('select_tag','likes','dislikes','requests').order_by('-uploaded_at')

    result = questions.filter(Q(select_tag__subtag__icontains=string))

    paginator = Paginator(result, PAGE_SIZE) # Show 25 contacts per page.
    total_page = math.ceil(result.count()/PAGE_SIZE)
    if request.GET.get("page_number") :
        current_page = int(request.GET.get("page_number"))
    else:
        current_page = 1
    previous_page = current_page - 1
    next_page = current_page + 1
    # result = paginator.page(current_page)

    user_tags = tags.objects.select_related().values("my_tag").distinct().filter(Q(user__username=request.user.username))
    u_tags = tags.objects.select_related().all().filter(Q(user__username=request.user.username))
    a_tags = tags.objects.select_related().values('my_subtag').filter(Q(user__username=request.user.username))

    add_tag_list = AllTags.objects.all()
    add_tag_list = add_tag_list.exclude(pk__in=a_tags)

    askqus_subtags = AllTags.objects.all()
    ques = []
    result = paginator.page(current_page)
    hid = hidden.objects.select_related('user').prefetch_related('question__select_tag','question__likes','question__dislikes','question__requests').all()
    for q in result:
        isliked = 0
        isdisliked = 0
        hidd = 0
        isSpecial = 0
        profi = Profile.objects.select_related().all().filter(user=q.user)
        if(q.likes.all().filter(username=request.user.username).count()==1):
            isliked = 1
        if(hid.all().filter(user=request.user, question = q).count()==1):
            hidd = 1
        if(q.dislikes.all().filter(username=request.user.username).count()==1):
            isdisliked = 1
        access_check = QuestionAccessControl.objects.filter(question=q)
        if len(access_check)>0:
            isSpecial = 1
        temp = {
            'access' : access_check,
            'isSpecial' : isSpecial,
            'profile':profi,
            'ques' : q,
            'isliked':isliked,
            'hidd' : hidd,
            'disliked': isdisliked,
            'votes':q.total_likes() - q.total_dislikes(),
        }
        ques.append(temp)
    role_data = Roles.objects.select_related().all()
    context = {
        "role":role_data,
        'form_answer': AnswerForm(),
        'Tags': user_tags,
        'questions': ques,
        'username': request.user.username,
        'subtags': askqus_subtags,
        'add_tag_list' : add_tag_list,
        'pages' : {
            'current_page' : current_page,
            'total_page' : total_page,
            'previous_page' : previous_page,
            'next_page' : next_page,
            },

        'a':   u_tags.filter(Q(my_tag__icontains='CSE')),
        'b' :   u_tags.filter(Q(my_tag__icontains='ECE')),
        'c' :   u_tags.filter(Q(my_tag__icontains='Mechanical')),
        'd' :   u_tags.filter(Q(my_tag__icontains='Technical-Clubs')),
        'e' :   u_tags.filter(Q(my_tag__icontains='Cultural-Clubs')),
        'f' :   u_tags.filter(Q(my_tag__icontains='Sports-Clubs')),
        'g' :   u_tags.filter(Q(my_tag__icontains='Business-and-Career')),
        'h' :   u_tags.filter(Q(my_tag__icontains='Entertainment')),
        'i' :   u_tags.filter(Q(my_tag__icontains='IIITDMJ-Campus')),
        'j' :   u_tags.filter(Q(my_tag__icontains='Jabalpur-city')),
        'k' :   u_tags.filter(Q(my_tag__icontains='IIITDMJ-Rules-and-Regulations')),
        'l' :   u_tags.filter(Q(my_tag__icontains='Academics')),
        'm' :   u_tags.filter(Q(my_tag__icontains='IIITDMJ')),
        'n' :   u_tags.filter(Q(my_tag__icontains='Life-Relationship-and-Self')),
        'o' :   u_tags.filter(Q(my_tag__icontains='Technology-and-Education')),
        'p' :   u_tags.filter(Q(my_tag__icontains='Programmes')),
        'q' :   u_tags.filter(Q(my_tag__icontains='Others')),
        'r' :   u_tags.filter(Q(my_tag__icontains='Design')),
    }

    return render(request, 'feeds/feeds_main.html', context)

def RemoveTag(request):
    """
    This function removes a tag from our selected tags given on feeds homepage left side
    @param:
        request - contains the metadata about the requested page
    """
    if request.method == 'POST':
        userTags = tags.objects.select_related().all().filter(Q(user=request.user))
        tagto_delete = AllTags.objects.all().filter(Q(subtag=request.POST.get('id')))
        userTags.filter(Q(my_subtag__in=tagto_delete)).delete()
        return JsonResponse({"done":"1"})
    else:
        return JsonResponse({"done":"0"})


def ParticularQuestion(request, id):
    """
    The function 'particular_question' takes us to a selected a question when we click on 'see more...' given down to every question , where we can answer the question or comment on it
    @param:
        request - contains metadata of the requested page
        id - selected particular quesiton id
    @variables:
        result - contains selected particular question object from Model 'AskaQuestion'
        a_tags-
        all_tags_list-
        u_tags-
        askqus_subtags-
        profile-
        is_liked-
        is_disliked-
        user_tags-

    """
    result = AskaQuestion.objects.prefetch_related('select_tag','likes','dislikes','requests').get(id=id)
    a_tags = tags.objects.select_related().values('my_subtag').filter(Q(user__username=request.user.username))
    all_tags_list = AllTags.objects.all()
    all_tags_list= all_tags_list.exclude(pk__in=a_tags)
    all_tags = AllTags.objects.values('tag').distinct()
    u_tags = tags.objects.select_related().all().filter(Q(user__username=request.user.username))
    askqus_subtags = AllTags.objects.all()
    profile = Profile.objects.select_related().all().filter(user=result.user)
    isliked = 0
    isdisliked = 0
    user_tags = tags.objects.select_related().values("my_tag").distinct().filter(Q(user__username=request.user.username))
    if(result.likes.all().filter(username=request.user.username).count()==1):
            isliked = 1
    if(result.dislikes.all().filter(username=request.user.username).count()==1):
        isdisliked = 1

    a_tags = tags.objects.select_related().values('my_subtag').filter(Q(user__username=request.user.username))
    add_tag_list = AllTags.objects.all()
    add_tag_list = add_tag_list.exclude(pk__in=a_tags)
    isSpecial = 0
    access_check = QuestionAccessControl.objects.filter(question=result)
    if len(access_check)>0:
        isSpecial = 1

    if request.method == 'POST':
        if request.POST.get("answer_button"):
            form_answer = AnswerForm(request.POST)
            if form_answer.is_valid():
                instance = form_answer.save(commit=False)
                instance.question = result
                instance.user = request.user
                instance.save()

                role_data = Roles.objects.select_related().all()
                context = {
                    'access' : access_check,
                    'isSpecial' : isSpecial,
                    'role' : role_data,
                    'isliked':isliked,
                    'disliked': isdisliked,
                    'votes':result.total_likes() - result.total_dislikes(),
                    'form_answer': AnswerForm(),
                    'instance': instance,
                    'question': result,
                    'Tags': user_tags,
                    'subtags': askqus_subtags,
                    'add_tag_list' : add_tag_list,
                    'profile' : profile,
                    'a':   u_tags.filter(Q(my_tag__icontains='CSE')),
                    'b' :   u_tags.filter(Q(my_tag__icontains='ECE')),
                    'c' :   u_tags.filter(Q(my_tag__icontains='Mechanical')),
                    'd' :   u_tags.filter(Q(my_tag__icontains='Technical-Clubs')),
                    'e' :   u_tags.filter(Q(my_tag__icontains='Cultural-Clubs')),
                    'f' :   u_tags.filter(Q(my_tag__icontains='Sports-Clubs')),
                    'g' :   u_tags.filter(Q(my_tag__icontains='Business-and-Career')),
                    'h' :   u_tags.filter(Q(my_tag__icontains='Entertainment')),
                    'i' :   u_tags.filter(Q(my_tag__icontains='IIITDMJ-Campus')),
                    'j' :   u_tags.filter(Q(my_tag__icontains='Jabalpur-city')),
                    'k' :   u_tags.filter(Q(my_tag__icontains='IIITDMJ-Rules-and-Regulations')),
                    'l' :   u_tags.filter(Q(my_tag__icontains='Academics')),
                    'm' :   u_tags.filter(Q(my_tag__icontains='IIITDMJ')),
                    'n' :   u_tags.filter(Q(my_tag__icontains='Life-Relationship-and-Self')),
                    'o' :   u_tags.filter(Q(my_tag__icontains='Technology-and-Education')),
                    'p' :   u_tags.filter(Q(my_tag__icontains='Programmes')),
                    'q' :   u_tags.filter(Q(my_tag__icontains='Others')),
                    'r' :   u_tags.filter(Q(my_tag__icontains='Design')),
                }

                return render(request, 'feeds/single_question.html', context)


    else:
        form = AnswerForm()
        # instance = AnsweraQuestion.objects.get(question__id=id)

    role_data = Roles.objects.select_related().all()
    context = {
        'access' : access_check,
        'isSpecial' : isSpecial,
        "role" : role_data,
        'isliked':isliked,
        'disliked': isdisliked,
        'votes':result.total_likes() - result.total_dislikes(),
        'question': result,
        'form_answer': form,
        'question': result,
        'Tags': user_tags,
        'add_tag_list' : add_tag_list,
        'profile' : profile,
        'subtags': askqus_subtags,
        'a':   u_tags.filter(Q(my_tag__icontains='CSE')),
        'b' :   u_tags.filter(Q(my_tag__icontains='ECE')),
        'c' :   u_tags.filter(Q(my_tag__icontains='Mechanical')),
        'd' :   u_tags.filter(Q(my_tag__icontains='Technical-Clubs')),
        'e' :   u_tags.filter(Q(my_tag__icontains='Cultural-Clubs')),
        'f' :   u_tags.filter(Q(my_tag__icontains='Sports-Clubs')),
        'g' :   u_tags.filter(Q(my_tag__icontains='Business-and-Career')),
        'h' :   u_tags.filter(Q(my_tag__icontains='Entertainment')),
        'i' :   u_tags.filter(Q(my_tag__icontains='IIITDMJ-Campus')),
        'j' :   u_tags.filter(Q(my_tag__icontains='Jabalpur-city')),
        'k' :   u_tags.filter(Q(my_tag__icontains='IIITDMJ-Rules-and-Regulations')),
        'l' :   u_tags.filter(Q(my_tag__icontains='Academics')),
        'm' :   u_tags.filter(Q(my_tag__icontains='IIITDMJ')),
        'n' :   u_tags.filter(Q(my_tag__icontains='Life-Relationship-and-Self')),
        'o' :   u_tags.filter(Q(my_tag__icontains='Technology-and-Education')),
        'p' :   u_tags.filter(Q(my_tag__icontains='Programmes')),
        'q' :   u_tags.filter(Q(my_tag__icontains='Others')),
        'r' :   u_tags.filter(Q(my_tag__icontains='Design')),
    }

    return render(request, 'feeds/single_question.html', context)

@login_required
def profile(request, string):
    """
    This function, first authenticates and then shows the profile of a user who has created a post when we click on the profile icon given upper-left side of a post
    @param-
        request- contains metadata of the requested page
        string- user's username
    @variables
    """
    print("user is this", request)
    if request.method == "POST":
        profile = Profile.objects.select_related().all().filter(user=request.user)
        Pr = None
        if len(profile) == 0:
            Pr = Profile(user = request.user)
        else:
            Pr = profile[0]
        if request.POST.get("bio"):
            if request.POST.get("bio") != "":
                Pr.bio = request.POST.get("bio")
        if request.FILES:
            if Pr.profile_picture :
                pth = os.path.join(settings.BASE_DIR, '..')
                default_storage.delete(pth+Pr.profile_picture.url)
            Pr.profile_picture = request.FILES["profile_img"]
        Pr.save()
        messages.success(request,"Profile updated successfully !")
    try:
        usr = User.objects.get(username=string)
    except:
        return redirect("/feeds")
    profile = Profile.objects.select_related().all().filter(user=usr)
    ques = AskaQuestion.objects.prefetch_related('select_tag','likes','dislikes','requests').all().filter(user=usr)
    ans = AnsweraQuestion.objects.all().filter(user=usr)
    extra = ExtraInfo.objects.select_related().all().filter(user=usr)
    tags = set()
    top_ques = ""
    top_ans = ans
    for q in ques:
        if top_ques == "":
            top_ques = q;
        for t in q.select_tag.all():
            tags.add(t)
    prf = ""
    ext = ""
    no_img = True
    if len(profile) == 0:
        prf = Profile(user =usr )
        prf.save()
    else:
        prf = profile[0]
        if prf.profile_picture :
            pth = os.path.join(settings.BASE_DIR, '..')
            if os.path.exists(pth+prf.profile_picture.url):
                no_img=False
        else :
            no_img :True

    if len(extra) == 0:
        ext = ""
    else:
        ext = extra[0]
    hid = hidden.objects.select_related('user').prefetch_related('question__select_tag','question__likes','question__dislikes','question__requests').all().filter(user = request.user)
    context = {
        'profile': prf,
        # 'profile_image' : profile[0].profile_picture,
        'question_asked' : len(ques),
        'answer_given' : len(ans),
        'last_login' : usr.last_login,
        'extra' : ext,
        'hidden_ques' : hid,
        'tags' : tags,
        'top_ques' : ques,
        'top_ques_len' : len(ques),
        'top_ans' : ans,
        'top_ans_len' : len(ans),
        'no_img' : no_img
    }
    return render(request, 'feeds/profile.html',context)

def upvoteQuestion(request,id):
    """
    this function makes us to upvote a question, when we click on upvote icon given down to every question
    @param:
        request - contains metadata of the requested page
        id - question id
    @variables:
        question - question object from model 'AskaQuestion' which is to be upvoted
        is_upvoted - count of how many times this question is upvoted
    """
    question = AskaQuestion.objects.prefetch_related('select_tag','likes','dislikes','requests').get(id=request.POST.get('id'))
    question.dislikes.remove(request.user)
    isupvoted = question.likes.all().filter(username=request.user.username).count()
    if request.is_ajax() and isupvoted == 0:
        question.likes.add(request.user)
        return JsonResponse({'done': "1",'votes':question.total_likes() - question.total_dislikes(),})
    else:
        return JsonResponse({"done":"0",'votes':question.total_likes() - question.total_dislikes(),})

def downvoteQuestion(request,id):
    """
    this function makes us to downvote a question, when we click on downvote icon given down to every question
    @param:
        request - contains metadata of the requested page
        id - question id
    @variables:
        question - question object from model 'AskaQuestion' which is to be upvoted
        is_downvoted - count of how many times this question is downvoted
    """
    question = AskaQuestion.objects.prefetch_related('select_tag','likes','dislikes','requests').get(id=request.POST.get('id'))
    question.likes.remove(request.user)
    isdownvoted = question.dislikes.all().filter(username=request.user.username).count()
    if request.is_ajax() and isdownvoted == 0:
        question.dislikes.add(request.user)
        return JsonResponse({'done': "1",'votes':question.total_likes() - question.total_dislikes(),})
    else:
        return JsonResponse({"done":"0",'votes':question.total_likes() - question.total_dislikes(),})

def upvoteAnswer(request,id):
    """
    this function makes us to upvote a answer, when we click on upvote icon given down to every answer
    @param:
        request - contains metadata of the requested page
        id - answer id
    @variables:
        answer - answer object from model 'AnsweraQuestion' which is to be upvoted
        is_upvoted - count of how many times this answer is upvoted
    """
    answer = AnsweraQuestion.objects.get(id=request.POST.get('id'))
    answer.dislikes.remove(request.user)
    isupvoted = answer.likes.all().filter(username=request.user.username).count()
    if request.is_ajax() and isupvoted == 0:
        answer.likes.add(request.user)
        return JsonResponse({'done': "1",'votes':answer.total_likes() - answer.total_dislikes(),})
    else:
        return JsonResponse({"done":"0",'votes':answer.total_likes() - answer.total_dislikes(),})

def downvoteAnswer(request,id):
    """
    this function makes us to downvote a answer, when we click on downvote icon given down to every answer
    @param:
        request - contains metadata of the requested page
        id - answer id
    @variables:
        answer - answer object from model 'AnsweraQuestion' which is to be downvoted
        is_downvoted - count of how many times this answer is downvoted
    """
    answer = AnsweraQuestion.objects.get(id=request.POST.get('id'))
    answer.likes.remove(request.user)
    isdownvoted = answer.dislikes.all().filter(username=request.user.username).count()
    if request.is_ajax() and isdownvoted == 0:
        answer.dislikes.add(request.user)
        return JsonResponse({'done': "1",'votes':answer.total_likes() - answer.total_dislikes(),})
    else:
        return JsonResponse({"done":"0",'votes':answer.total_likes() - answer.total_dislikes(),})


def update_answer(request):
    """
    update_answer function makes us able to update a answer with new details
    @param :
        request - contains metadata of requested page
    @variables:

    """
    try:
        ques_id = request.POST.get("ques_id")
        answer_id = request.POST.get("answer_id")
        question = AskaQuestion.objects.prefetch_related('select_tag','likes','dislikes','requests').get(pk=ques_id)
        answer = AnsweraQuestion.objects.get(pk=answer_id)
        new_answer = request.POST.get("comment_box")
        answer.content = new_answer
        answer.save()
        if request.is_ajax():
            return JsonResponse({'success': 1})
    except:
        if request.is_ajax():
            return JsonResponse({'sucess': 0})

def update_comment(request):
    """
    update_comment function makes us able to update a comment on a question
    @param :
        request - contains metadata of requested page
    @variables:

    """
    try:
        ques_id = request.POST.get("ques_id")
        comment_id = request.POST.get("comment_id")
        question = AskaQuestion.objects.prefetch_related('select_tag','likes','dislikes','requests').get(pk=ques_id)
        comment = Comments.objects.get(pk=comment_id)
        new_comment = request.POST.get("comment_box")
        comment.comment_text = new_comment
        comment.save()
        if request.is_ajax():
            return JsonResponse({'success': 1})
    except:
        if request.is_ajax():
            return JsonResponse({'sucess': 0})

def get_page_info(current_page, query):
    """
    this function gives us details of pages like which page is showing currently , next page number and previous page number
    @param:
        current_page - current page number
        query-
    @variables:
        paginator-a Page object with the given 1-based index
        total_page

    """
    paginator = Paginator(query, PAGE_SIZE) # Show 25 contacts per page.
    total_page = math.ceil(query.count()/2)
    if request.GET.get("page_number") :
        current_page = int(request.GET.get("page_number"))
    else:
        current_page = 1
    previous_page = current_page - 1
    next_page = current_page + 1
    query = paginator.page(current_page)
    return {
            'total_page' : total_page,
            'previous_page' : previous_page,
            'next_page' : next_page,
        }

@login_required
def admin(request):
    """
    For assigning and unassigning roles to user, if user is a admin
    @param:
        request- contains metadata of the requested page
    @variables-

    """
    error = {
        "user":"",
        "role" : ""
        }
    success = {
        "user":"",
        }
    if request.method == 'POST' and request.POST.get("addrole"):
        user = request.POST.get("user")
        role = request.POST.get("role")
        try:
            user_check = User.objects.get(username=user)
            role_check = Roles.objects.select_related().filter(user=user_check)
            if(len(role_check)==0):
                role_check_role = Roles.objects.select_related().filter(role__iexact=role)
                if(len(role_check_role)==0):
                    role = Roles.objects.create(user=user_check, role=role)
                    success["user"] = "Role added."
                else:
                    error["role"] = "This role is assigned to different person."
            else:
                error["user"] = "User already assigned a role."
        except User.DoesNotExist:
            error["user"] = "User Does not exist."

    if request.method == 'POST' and request.POST.get("unassignrole"):
        if request.POST.get("unassignrole_value"):
            try:
                role_unassign = Roles.objects.select_related().get(role = request.POST.get("unassignrole_value"))
                role_unassign.active = False
                success["update"] = "Role Unassigned."
                role_unassign.delete()
            except :
                error["update"] = "Incorrect Username provided."

    if request.method == 'POST' and request.POST.get("reassignrole"):
        if request.POST.get("reassignrole_value"):
            try:
                role_unassign = Roles.objects.select_related().get(role = request.POST.get("reassignrole_value"))
                role_unassign.active = True
                role_unassign.save()
                success["updatere"] = "Role Reassigned."
            except :
                error["updatere"] = "Error occurred."


    if request.method == 'POST' and request.POST.get("unassignrole_update"):
        try:
            role_unassign = Roles.objects.select_related().get(role = request.POST.get("unassignrole_value"))
            user_check = User.objects.get(username=request.POST.get("unassignrole_update"))
            role_unassign.user = user_check
            role_unassign.save()
            success["update"] = "Role Reassigned."
        except :
            error["updateerror"] = "Incorrect Username provided."

    role_data = Roles.objects.select_related().all()
    role_user = ""
    askqus_subtags = AllTags.objects.all()
    isAdmin = False
    administrativeRole = False
    try:
        admin = User.objects.get(username = "siddharth")
        if admin == request.user:
            isAdmin = True
    except:
        isAdmin = False

    try:
        admin_role = Roles.objects.select_related().filter(user = request.user)
        if len(admin_role) >0 :
            if admin_role[0].active == True:
                role_user = admin_role[0].role
                administrativeRole = True
            else:
                role_user = ""
    except:
        administrativeRole = False
    context = {
        "role_user" : role_user,
        "administrativeRole" : administrativeRole,
        "isAdmin" : isAdmin,
        'form_answer': AnswerForm(),
        "error" : error,
        "success" : success,
        "role" : role_data,
        'subtags': askqus_subtags,
    }
    return render(request, 'feeds/admin.html', context)

@login_required
def administrativeView(request, string):
    # questions = AskaQuestion.objects.order_by('-uploaded_at')
    role_user = Roles.objects.select_related().filter(role=string)
    try :
        role_user = role_user[0]
    except:
        redirect("/feeds")
    result = QuestionAccessControl.objects.select_related('posted_by__user').prefetch_related('question__select_tag','question__likes','question__dislikes','question__requests').filter(posted_by=role_user).order_by('-created_at')
    paginator = Paginator(result, PAGE_SIZE) # Show 25 contacts per page.
    total_page = math.ceil(result.count()/PAGE_SIZE)
    if request.GET.get("page_number") :
        current_page = int(request.GET.get("page_number"))
    else:
        current_page = 1
    previous_page = current_page - 1
    next_page = current_page + 1
    # result = paginator.page(current_page)

    user_tags = tags.objects.select_related().values("my_tag").distinct().filter(Q(user__username=request.user.username))
    u_tags = tags.objects.select_related().all().filter(Q(user__username=request.user.username))
    a_tags = tags.objects.select_related().values('my_subtag').filter(Q(user__username=request.user.username))

    add_tag_list = AllTags.objects.all()
    add_tag_list = add_tag_list.exclude(pk__in=a_tags)

    askqus_subtags = AllTags.objects.all()
    ques = []
    result = paginator.page(current_page)
    hid = hidden.objects.select_related('user').prefetch_related('question__select_tag','question__likes','question__dislikes','question__requests').all()
    for q in result:
        isliked = 0
        isdisliked = 0
        hidd = 0
        isSpecial = 0
        profi = Profile.objects.select_related().all().filter(user=q.question.user)
        if(q.question.likes.all().filter(username=request.user.username).count()==1):
            isliked = 1
        if(hid.all().filter(user=request.user, question = q.question).count()==1):
            hidd = 1
        if(q.question.dislikes.all().filter(username=request.user.username).count()==1):
            isdisliked = 1
        access_check = q
        isSpecial = 1
        temp = {
            'access' : access_check,
            'isSpecial' : isSpecial,
            'profile':profi,
            'ques' : q.question,
            'isliked':isliked,
            'hidd' : hidd,
            'disliked': isdisliked,
            'votes':q.question.total_likes() - q.question.total_dislikes(),
        }
        ques.append(temp)
    role_data = Roles.objects.select_related().all()
    context = {
        "role":role_data,
        'form_answer': AnswerForm(),
        'Tags': user_tags,
        'questions': ques,
        'username': request.user.username,
        'subtags': askqus_subtags,
        'add_tag_list' : add_tag_list,
        'pages' : {
            'current_page' : current_page,
            'total_page' : total_page,
            'previous_page' : previous_page,
            'next_page' : next_page,
            },

        'a':   u_tags.filter(Q(my_tag__icontains='CSE')),
        'b' :   u_tags.filter(Q(my_tag__icontains='ECE')),
        'c' :   u_tags.filter(Q(my_tag__icontains='Mechanical')),
        'd' :   u_tags.filter(Q(my_tag__icontains='Technical-Clubs')),
        'e' :   u_tags.filter(Q(my_tag__icontains='Cultural-Clubs')),
        'f' :   u_tags.filter(Q(my_tag__icontains='Sports-Clubs')),
        'g' :   u_tags.filter(Q(my_tag__icontains='Business-and-Career')),
        'h' :   u_tags.filter(Q(my_tag__icontains='Entertainment')),
        'i' :   u_tags.filter(Q(my_tag__icontains='IIITDMJ-Campus')),
        'j' :   u_tags.filter(Q(my_tag__icontains='Jabalpur-city')),
        'k' :   u_tags.filter(Q(my_tag__icontains='IIITDMJ-Rules-and-Regulations')),
        'l' :   u_tags.filter(Q(my_tag__icontains='Academics')),
        'm' :   u_tags.filter(Q(my_tag__icontains='IIITDMJ')),
        'n' :   u_tags.filter(Q(my_tag__icontains='Life-Relationship-and-Self')),
        'o' :   u_tags.filter(Q(my_tag__icontains='Technology-and-Education')),
        'p' :   u_tags.filter(Q(my_tag__icontains='Programmes')),
        'q' :   u_tags.filter(Q(my_tag__icontains='Others')),
        'r' :   u_tags.filter(Q(my_tag__icontains='Design')),
    }

    return render(request, 'feeds/feeds_main.html', context)
