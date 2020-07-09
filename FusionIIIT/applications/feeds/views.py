import json
import os
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.http.response import HttpResponse
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
PAGE_SIZE = 4
# Create your views here.
@login_required
def feeds(request):
    query = AskaQuestion.objects.order_by('-uploaded_at')
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
        print("searching")
        q = request.GET.get('keyword')
        questions = AskaQuestion.objects.all()
        result = questions.filter(Q(subject__icontains=q) | Q(description__icontains=q)).order_by('-uploaded_at')
        query = result
        paginator = Paginator(query, PAGE_SIZE)
        keyword = q.split(" ")
        keyword = "+".join(keyword)
        total_page = math.ceil(query.count()/PAGE_SIZE)

    if request.method == 'POST':

        if request.POST.get('add_qus') :
            print("Post a Question request received")
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
            role_check = Roles.objects.filter(user=request.user)
            if len(role_check) > 0 and request.POST.get("from_admin"):
                access = QuestionAccessControl.objects.create(question=question, canVote=True, canAnswer=True, canComment = True)
                if request.POST.get("RestrictVote"):
                    access.canVote = False
                if request.POST.get("RestrictAnswer"):
                    access.canAnswer = False
                if request.POST.get("RestrictComment"):
                    access.canComment = False
                access.save()
                return redirect("/feeds/admin")
            query = AskaQuestion.objects.order_by('-uploaded_at')

        if request.POST.get('search'):
            q = request.POST.get('keyword')
            questions = AskaQuestion.objects.all()
            result = questions.filter(Q(subject__icontains=q) | Q(description__icontains=q)).order_by('-uploaded_at')
            query = result
            paginator = Paginator(query, PAGE_SIZE)

        # adding user's favourite tags
        if request.POST.get("add_tag"):
            fav_tag=request.POST.get('tag')                                     # returning string
            a = []
            fav_tag = fav_tag[4:]
            a= [int(c) for c in fav_tag.split(",")]                             # listing queery objects
            print(a)
            for i in range(0, len(a)):                       
                temp = AllTags.objects.get(pk=a[i])
                new = tags.objects.create(user=request.user,my_subtag=temp)
                new.my_tag = temp.tag
                print(AllTags.objects.get(pk=a[i]))
                new.save()
            return redirect("/feeds")

    all_tags = AllTags.objects.values('tag').distinct()
    askqus_subtags = AllTags.objects.all()

    user_tags = tags.objects.values("my_tag").distinct().filter(Q(user__username=request.user.username))
    u_tags = tags.objects.all().filter(Q(user__username=request.user.username))
    a_tags = tags.objects.values('my_subtag').filter(Q(user__username=request.user.username))
    # print(tags.objects.all().filter(Q(my_tag__icontains='CSE')))
    ques = []
    try:
        query = paginator.page(current_page)
    except:
        query = []

    hid = hidden.objects.all()
    for q in query:
        isliked = 0
        isdisliked = 0
        hidd = 0
        isSpecial = 0
        profi = Profile.objects.all().filter(user=q.user)
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
    role_data = Roles.objects.all()
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
    return render(request, 'feeds/feeds_main.html', context)

def Request(request):
    question = get_object_or_404(AskaQuestion, id=request.POST.get('id'))
    print('Python')
    question.is_requested = False

    if question.requests.filter(id=request.user.id).exists():
        question.requests.remove(request.user)
        question.is_requested = False
        question.save()
    else:
        question.requests.add(request.user)
        question.is_requested = True
        question.save()
        
    print(question.total_requests())

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
    if request.method == 'POST':
        print('Ajax called')
        question = get_object_or_404(AskaQuestion, id=request.POST.get('id'))
        comment = Comments.objects.create(user=request.user,question=question)
        comment.comment_text = request.POST.get('comment_box')
        comment.save()
        print(comment.id)
        msg = request.POST.get('comment_box', None)
        print('saved')

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
    if request.method == 'POST':
        print('Ajax called')
        question = get_object_or_404(AskaQuestion, id=request.POST.get('ques_id'))
        print(request.POST.get('ques_id'))
        comment = get_object_or_404(Comments, id=request.POST.get('id'))
        reply = Reply.objects.create(user=request.user, comment=comment)
        reply.content = request.POST.get('comment_box')

        reply.save()
        print(comment.id)
        msg = request.POST.get('comment_box', None)
        print('saved')

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
    # question = get_object_or_404(AskaQuestion, id=request.POST.get('id'))
    comment = Comments.objects.get(id=request.POST.get('id'))
    # comment.question = question
    print('Liking comment')
    # print(comment.likes_comment.filter(id=request.user.id).exists())

    print(comment.is_liked)

    if comment.is_liked:
        comment.is_liked = False
        comment.likes_comment.remove(request.user)
        comment.save()    
    else:
        comment.is_liked = True
        comment.likes_comment.add(request.user)
        print(comment.total_likes_comment())
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
    if request.method == 'POST':
        print("deleting comment")
        comment_id = request.POST.get("comment_id")
        comment = Comments.objects.filter(pk=comment_id)
        comment.delete()
        print(comment)
        return JsonResponse({"done":1})

def delete_answer(request):
    if request.method == 'POST':
        print("deleting answer")
        answer_id = request.POST.get("answer_id")
        print(answer_id)
        answer = AnsweraQuestion.objects.filter(pk=answer_id)
        answer.delete()
        # print(answer)
        return JsonResponse({"done":1})
        
def delete_post(request, id):
    if request.method == 'POST' and request.POST.get("delete"):
        ques = AskaQuestion.objects.filter(pk=id)[0]
        if ques.file:
            pth = os.path.join(settings.BASE_DIR, '..')
            default_storage.delete(pth+ques.file.url)
        ques.delete()
        return redirect ('/feeds/')

def hide_post(request, id):
    if request.method == 'POST' and request.POST.get("hide"):
        ques = AskaQuestion.objects.filter(pk=id)[0]
        print(ques)
        hid = hidden(user = request.user, question = ques);
        hid.save()
        print(hid,"sid")
    return redirect ('/feeds/')

def unhide_post(request, id):
    if request.method == 'POST' and request.POST.get("unhide"):
        ques = AskaQuestion.objects.filter(pk=id)[0]
        print(ques)
        hid = hidden.objects.filter(user=request.user )
        hid.delete()
    return redirect ('/feeds/')

def update_post(request, id):
    if request.method == 'POST' and request.POST.get("update"):
        print(request.POST.get('anonymous_update'))
        question= AskaQuestion.objects.get(pk=id)
        question.subject = request.POST.get('subject')
        question.description = request.POST.get('description')

        tag = request.POST.get('Add_Tag')
        tag = tag[8:]
        ques_tag = []
        result = []
        ques_tag = [int(c) for c in tag.split(",")]
        question.select_tag.clear()

        for i in range(0, len(ques_tag)):
            result = AllTags.objects.get(id=ques_tag[i])
            question.select_tag.add(result)

        if request.POST.get('anonymous_update')==None :
            question.user= request.user
            question.anonymous_ask=False
        else :
            question.anonymous_ask=True
        #question.anonymous_ask = request.POST.get('anonymous_update')
        #print(request.POST.get('anonymous_update'))
        question.save()
        #if request.POST.get("anonymous")== True:
        return redirect ('/feeds/')

@login_required
def TagsBasedView(request, string):
    print('Tag based View')
    questions = AskaQuestion.objects.order_by('-uploaded_at')
    
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
    
    user_tags = tags.objects.values("my_tag").distinct().filter(Q(user__username=request.user.username))
    u_tags = tags.objects.all().filter(Q(user__username=request.user.username))
    a_tags = tags.objects.values('my_subtag').filter(Q(user__username=request.user.username))
    
    add_tag_list = AllTags.objects.all()
    add_tag_list = add_tag_list.exclude(pk__in=a_tags)

    askqus_subtags = AllTags.objects.all()
    ques = []
    result = paginator.page(current_page)
    hid = hidden.objects.all()
    for q in result:
        isliked = 0
        isdisliked = 0
        hidd = 0
        isSpecial = 0
        profi = Profile.objects.all().filter(user=q.user)
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
    role_data = Roles.objects.all()
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
    if request.method == 'POST':
        print(request.POST.get('id'))
        userTags = tags.objects.all().filter(Q(user=request.user))
        tagto_delete = AllTags.objects.all().filter(Q(subtag=request.POST.get('id')))
        userTags.filter(Q(my_subtag__in=tagto_delete)).delete()
        return JsonResponse({"done":"1"})
    else:
        return JsonResponse({"done":"0"})
        

def ParticularQuestion(request, id):
    result = AskaQuestion.objects.get(id=id)
    a_tags = tags.objects.values('my_subtag').filter(Q(user__username=request.user.username))
    all_tags_list = AllTags.objects.all()
    all_tags_list= all_tags_list.exclude(pk__in=a_tags)
    all_tags = AllTags.objects.values('tag').distinct()
    u_tags = tags.objects.all().filter(Q(user__username=request.user.username))
    askqus_subtags = AllTags.objects.all()
    profile = Profile.objects.all().filter(user=result.user)
    isliked = 0
    isdisliked = 0
    user_tags = tags.objects.values("my_tag").distinct().filter(Q(user__username=request.user.username))
    if(result.likes.all().filter(username=request.user.username).count()==1):
            isliked = 1
    if(result.dislikes.all().filter(username=request.user.username).count()==1):
        isdisliked = 1

    a_tags = tags.objects.values('my_subtag').filter(Q(user__username=request.user.username))
    add_tag_list = AllTags.objects.all()
    add_tag_list = add_tag_list.exclude(pk__in=a_tags)
    isSpecial = 0
    access_check = QuestionAccessControl.objects.filter(question=result)
    if len(access_check)>0:
        isSpecial = 1

    if request.method == 'POST':
        if request.POST.get("answer_button"):
            print('Particular Question')
            form_answer = AnswerForm(request.POST)
            if form_answer.is_valid():
                instance = form_answer.save(commit=False)
                instance.question = result
                instance.user = request.user
                instance.save()
                role_data = Roles.objects.all()
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
        # print(instance.content)
    
    role_data = Roles.objects.all()
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
    if request.method == "POST":
        profile = Profile.objects.all().filter(user=request.user)
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
    print("Profile Loading ......")
    try:
        usr = User.objects.get(username=string)
    except:
        return redirect("/feeds")
    profile = Profile.objects.all().filter(user=usr)
    ques = AskaQuestion.objects.all().filter(user=usr)
    ans = AnsweraQuestion.objects.all().filter(user=usr)
    extra = ExtraInfo.objects.all().filter(user=usr)
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
    hid = hidden.objects.all().filter(user = request.user)
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

def printques(a):
    print(a.can_delete)
    print(a.can_update)
    print(a.user)
    print(a.subject)
    print(a.description)
    print(a.select_tag)
    print(a.file)
    print(a.uploaded_at)
    print(a.likes)
    print(a.requests)
	#dislikes = models.ManyToManyField(User, related_name='dislikes', blank=True)
    print(a.is_liked)
    print(a.is_requested)
    print(a.request)
    print(a.anonymous_ask)
    print(a.total_likes)
    print(a.total_dislikes)

def upvoteQuestion(request,id):
    question = AskaQuestion.objects.get(id=request.POST.get('id'))
    print('upvoting question')
    print("-------------likes--------------")
    print(question.likes.all())
    print("-------------dislikes--------------")
    print(question.dislikes.all())
    question.dislikes.remove(request.user)
    isupvoted = question.likes.all().filter(username=request.user.username).count()
    if request.is_ajax() and isupvoted == 0:
        question.likes.add(request.user)
        return JsonResponse({'done': "1",'votes':question.total_likes() - question.total_dislikes(),})
    else:
        return JsonResponse({"done":"0",'votes':question.total_likes() - question.total_dislikes(),})

def downvoteQuestion(request,id):
    question = AskaQuestion.objects.get(id=request.POST.get('id'))
    print('upvoting question')
    print("-------------likes--------------")
    print(question.likes.all())
    print("-------------dislikes--------------")
    print(question.dislikes.all())
    question.likes.remove(request.user)
    isdownvoted = question.dislikes.all().filter(username=request.user.username).count()
    if request.is_ajax() and isdownvoted == 0:
        question.dislikes.add(request.user)
        return JsonResponse({'done': "1",'votes':question.total_likes() - question.total_dislikes(),})
    else:
        return JsonResponse({"done":"0",'votes':question.total_likes() - question.total_dislikes(),})

def upvoteAnswer(request,id):
    answer = AnsweraQuestion.objects.get(id=request.POST.get('id'))
    print('upvoting answer')
    print("-------------likes--------------")
    print(answer.likes.all())
    print("-------------dislikes--------------")
    print(answer.dislikes.all())
    answer.dislikes.remove(request.user)
    isupvoted = answer.likes.all().filter(username=request.user.username).count()
    if request.is_ajax() and isupvoted == 0:
        answer.likes.add(request.user)
        return JsonResponse({'done': "1",'votes':answer.total_likes() - answer.total_dislikes(),})
    else:
        return JsonResponse({"done":"0",'votes':answer.total_likes() - answer.total_dislikes(),})

def downvoteAnswer(request,id):
    answer = AnsweraQuestion.objects.get(id=request.POST.get('id'))
    print('upvoting answer')
    print("-------------likes--------------")
    print(answer.likes.all())
    print("-------------dislikes--------------")
    print(answer.dislikes.all())
    answer.likes.remove(request.user)
    isdownvoted = answer.dislikes.all().filter(username=request.user.username).count()
    if request.is_ajax() and isdownvoted == 0:
        answer.dislikes.add(request.user)
        return JsonResponse({'done': "1",'votes':answer.total_likes() - answer.total_dislikes(),})
    else:
        return JsonResponse({"done":"0",'votes':answer.total_likes() - answer.total_dislikes(),})


def update_answer(request):
    try:
        ques_id = request.POST.get("ques_id")
        answer_id = request.POST.get("answer_id")
        question = AskaQuestion.objects.get(pk=ques_id)
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
    try:
        ques_id = request.POST.get("ques_id")
        comment_id = request.POST.get("comment_id")
        question = AskaQuestion.objects.get(pk=ques_id)
        comment = Comments.objects.get(pk=comment_id)
        new_comment = request.POST.get("comment_box")
        print(new_comment)
        comment.comment_text = new_comment
        comment.save()
        if request.is_ajax():
            return JsonResponse({'success': 1})
    except:
        if request.is_ajax():
            return JsonResponse({'sucess': 0})

def get_page_info(current_page, query):
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
    error = {
        "user":"",
        "role" : ""
        }
    success = {
        "user":"",
        }
    if request.method == 'POST' and request.POST.get("addrole"):
        print(request.POST.get("addrole"))
        user = request.POST.get("user")
        role = request.POST.get("role")
        try:
            user_check = User.objects.get(username=user)
            print(user_check)
            role_check = Roles.objects.filter(user=user_check)
            if(len(role_check)==0):
                role_check_role = Roles.objects.filter(role__iexact=role)
                if(len(role_check_role)==0):
                    role = Roles.objects.create(user=user_check, role=role)
                    success["user"] = "Role added."
                else:
                    error["role"] = "This role is assigned to different person."
            else:
                error["user"] = "User already assigned a role."
        except User.DoesNotExist:
            error["user"] = "User Does not exist."
    role_data = Roles.objects.all()
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
        admin_role = Roles.objects.filter(user = request.user)
        if len(admin_role) >0 :
            role_user = admin_role[0].role
            administrativeRole = True
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
