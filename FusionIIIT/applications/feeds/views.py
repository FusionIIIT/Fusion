import json

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from .forms import AnswerForm
from .models import (AllTags, AnsweraQuestion, AskaQuestion, Comments, Reply,
                     hidden, report, tags)


# Create your views here.
@login_required
def feeds(request):
    query = AskaQuestion.objects.order_by('-uploaded_at')

    if request.method == 'POST':
        if request.POST.get('add_qus') and request.FILES or None:
            print('file')
            question = AskaQuestion.objects.create()
            question.user = request.user
            question.subject = request.POST.get('subject')
            question.description = request.POST.get('description')
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
            query = AskaQuestion.objects.order_by('-uploaded_at')

        if request.POST.get('search'):
            q = request.POST.get('keyword')
            questions = AskaQuestion.objects.all()
            result = questions.filter(Q(subject__icontains=q) | Q(description__icontains=q)).order_by('-uploaded_at')
            query = result

        # adding user's favourite tags
        if request.POST.get("add_tag"):
            fav_tag=request.POST.get('tag')                                     # returning string
            a = []
            fav_tag = fav_tag[4:]
            a= [int(c) for c in fav_tag.split(",")]                             # listing queery objects

            for i in range(0, len(a)):                       
                new = tags.objects.create()
                new.user = request.user
                new.my_tag = AllTags.objects.values_list('tag').get(pk=a[i])
                new.my_subtag = AllTags.objects.get(pk=a[i])
                new.save()

    all_tags = AllTags.objects.values('tag').distinct()
    askqus_subtags = AllTags.objects.all()
    print('asd')
    for i in askqus_subtags:
        print('0')

    user_tags = tags.objects.filter(Q(user__username=request.user.username))
    u_tags = user_tags.values_list('my_subtag')
    a_tags = tags.objects.values('my_subtag').filter(Q(user__username=request.user.username))

    #query = question.filter(select_tag__in=list(u_tags))

    # # if len(u_tags) == 0:
    # query = AskaQuestion.objects.order_by('-uploaded_at')

    # items in add tag menu
    add_tag_list = AllTags.objects.all()
    add_tag_list = add_tag_list.exclude(pk__in=a_tags)

    context ={
        'form_answer': AnswerForm(),
        'my_tags': all_tags,
        'questions': query,
        'username': request.user.username,
        'subtags': askqus_subtags,
        'add_tag_list' : add_tag_list,

        'a': user_tags.filter(Q(my_tag__icontains='CSE')),
        'b' : user_tags.filter(Q(my_tag__icontains='ECE')),
        'c' : user_tags.filter(Q(my_tag__icontains='Mechanical')),
        'd' : user_tags.filter(Q(my_tag__icontains='Design')),
        'e' : user_tags.filter(Q(my_tag__icontains='Business-and-Career')),
        'f' : user_tags.filter(Q(my_tag__icontains='Entertainment')),
        'g' : user_tags.filter(Q(my_tag__icontains='Jabalpur-city')),
        'h' : user_tags.filter(Q(my_tag__icontains='IIITDMJ-Rules-and-Regulations')),
        'i' : user_tags.filter(Q(my_tag__icontains='Life-Relationship-and-Self')),
        'j' : user_tags.filter(Q(my_tag__icontains='IIITDMJ-Campus')),
        'k' : user_tags.filter(Q(my_tag__icontains='Programmes')),
    }
    return render(request, 'feeds/feeds_main.html', context)


def Request(request):
    question = get_object_or_404(AskaQuestion, id=request.POST.get('id'))
    print('Python')
    question.is_requested = False;

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
        comment = Comments.objects.create()
        comment.question = question
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
        reply = Reply.objects.create()
        reply.comment = comment
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
    print('coming')
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

def delete_post(request, id):
    if request.method == 'POST' and request.POST.get("delete"):
        AskaQuestion.objects.filter(pk=id).delete()
        return redirect ('/feeds/')

def update_post(request, id):
    if request.method == 'POST' and request.POST.get("update"):
        print(request.POST.get('anonymous_update'))
        question= AskaQuestion.objects.get(pk=id)
        question.subject = request.POST.get('subject')
        question.description = request.POST.get('description')
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

def TagsBasedView(request, string):
    print('coming')
    questions = AskaQuestion.objects.all()
    result = questions.filter(Q(select_tag__subtag__icontains=string))
    user_tags = tags.objects.filter(Q(user__username=request.user.username))
    a_tags = tags.objects.values('my_subtag').filter(Q(user__username=request.user.username))
    all_tags_list = AllTags.objects.all()
    all_tags_list = all_tags_list.exclude(pk__in=a_tags)
    all_tags = AllTags.objects.values('tag').distinct()

    context = {
        'form_answer': AnswerForm(),
        'questions': result,
        'my_tags': all_tags,
        'all_tags_list': all_tags_list,

        'a': user_tags.filter(Q(my_tag__icontains='CSE')),
        'b' : user_tags.filter(Q(my_tag__icontains='ECE')),
        'c' : user_tags.filter(Q(my_tag__icontains='Mechanical')),
        'd' : user_tags.filter(Q(my_tag__icontains='Design')),
        'e' : user_tags.filter(Q(my_tag__icontains='Business-and-Career')),
        'f' : user_tags.filter(Q(my_tag__icontains='Entertainment')),
        'g' : user_tags.filter(Q(my_tag__icontains='Jabalpur-city')),
        'h' : user_tags.filter(Q(my_tag__icontains='IIITDMJ-Rules-and-Regulations')),
        'i' : user_tags.filter(Q(my_tag__icontains='Life-Relationship-and-Self')),
        'j' : user_tags.filter(Q(my_tag__icontains='IIITDMJ-Campus')),
        'k' : user_tags.filter(Q(my_tag__icontains='Programmes')),
    }

    return render(request, 'feeds/feeds_main.html', context)

def RemoveTag(request):
    questions = AskaQuestion.objects.all()
    user_tags = tags.objects.filter(Q(user__username=request.user.username))
    user_tags.filter(Q(my_subtag__subtag__icontains=request.POST.get('id'))).delete()
    a_tags = tags.objects.values('my_subtag').filter(Q(user__username=request.user.username))
    all_tags_list = AllTags.objects.ALL()
    all_tags_list= all_tags_list.exclude(pk__in=a_tags)
    all_tags = AllTags.objects.values('tag').distinct()

    context = {
        'form_answer': AnswerForm(),
        'questions': result,
        'my_tags': all_tags,
        'all_tags_list': all_tags_list,

        'a': user_tags.filter(Q(my_tag__icontains='CSE')),
        'b' : user_tags.filter(Q(my_tag__icontains='ECE')),
        'c' : user_tags.filter(Q(my_tag__icontains='Mechanical')),
        'd' : user_tags.filter(Q(my_tag__icontains='Design')),
        'e' : user_tags.filter(Q(my_tag__icontains='Business-and-Career')),
        'f' : user_tags.filter(Q(my_tag__icontains='Entertainment')),
        'g' : user_tags.filter(Q(my_tag__icontains='Jabalpur-city')),
        'h' : user_tags.filter(Q(my_tag__icontains='IIITDMJ-Rules-and-Regulations')),
        'i' : user_tags.filter(Q(my_tag__icontains='Life-Relationship-and-Self')),
        'j' : user_tags.filter(Q(my_tag__icontains='IIITDMJ-Campus')),
        'k' : user_tags.filter(Q(my_tag__icontains='Programmes')),
    }

    return render(request, 'feeds/feeds_main.html', context)


def ParticularQuestion(request, id):
    result = AskaQuestion.objects.get(id=id)
    print(id)
    print(result.subject)
    user_tags = tags.objects.filter(Q(user__username=request.user.username))
    a_tags = tags.objects.values('my_subtag').filter(Q(user__username=request.user.username))
    all_tags_list = AllTags.objects.all()
    all_tags_list= all_tags_list.exclude(pk__in=a_tags)
    all_tags = AllTags.objects.values('tag').distinct()

    if request.method == 'POST':
        if request.POST.get("answer_button"):
            print('coming')
            form_answer = AnswerForm(request.POST)
            if form_answer.is_valid():
                instance = form_answer.save(commit=False)
                instance.question = result
                instance.save()

                context = {
                    'form_answer': AnswerForm(),
                    'instance': instance,        
                    'question': result,
                    'my_tags': all_tags,
                    'all_tags_list': all_tags_list,

                    'a': user_tags.filter(Q(my_tag__icontains='CSE')),
                    'b' : user_tags.filter(Q(my_tag__icontains='ECE')),
                    'c' : user_tags.filter(Q(my_tag__icontains='Mechanical')),
                    'd' : user_tags.filter(Q(my_tag__icontains='Design')),
                    'e' : user_tags.filter(Q(my_tag__icontains='Business-and-Career')),
                    'f' : user_tags.filter(Q(my_tag__icontains='Entertainment')),
                    'g' : user_tags.filter(Q(my_tag__icontains='Jabalpur-city')),
                    'h' : user_tags.filter(Q(my_tag__icontains='IIITDMJ-Rules-and-Regulations')),
                    'i' : user_tags.filter(Q(my_tag__icontains='Life-Relationship-and-Self')),
                    'j' : user_tags.filter(Q(my_tag__icontains='IIITDMJ-Campus')),
                    'k' : user_tags.filter(Q(my_tag__icontains='Programmes')),
                }

                return render(request, 'feeds/single_question.html', context)

    else:
        form = AnswerForm()
        # instance = AnsweraQuestion.objects.get(question__id=id)
        # print(instance.content)

    context = {
        'question': result,
        'form_answer': form,
        'question': result,
        'my_tags': all_tags,
        'all_tags_list': all_tags_list,

        'a': user_tags.filter(Q(my_tag__icontains='CSE')),
        'b' : user_tags.filter(Q(my_tag__icontains='ECE')),
        'c' : user_tags.filter(Q(my_tag__icontains='Mechanical')),
        'd' : user_tags.filter(Q(my_tag__icontains='Design')),
        'e' : user_tags.filter(Q(my_tag__icontains='Business-and-Career')),
        'f' : user_tags.filter(Q(my_tag__icontains='Entertainment')),
        'g' : user_tags.filter(Q(my_tag__icontains='Jabalpur-city')),
        'h' : user_tags.filter(Q(my_tag__icontains='IIITDMJ-Rules-and-Regulations')),
        'i' : user_tags.filter(Q(my_tag__icontains='Life-Relationship-and-Self')),
        'j' : user_tags.filter(Q(my_tag__icontains='IIITDMJ-Campus')),
        'k' : user_tags.filter(Q(my_tag__icontains='Programmes')),
    }

    return render(request, 'feeds/single_question.html', context)
