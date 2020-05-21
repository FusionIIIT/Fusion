from django.conf.urls import url

from . import views

app_name = 'feeds'

urlpatterns=[
	url(r'^$', views.feeds, name= 'feeds'),
	url(r'^profile/(?P<string>[-\w]+)/$', views.profile, name= 'profile'),
	url(r'^request/$', views.Request, name= 'request'),
	url(r'^comment_text/$', views.Comment_Text, name='comment_text'),
	url(r'^reply_text/$', views.Reply_Text, name='reply_text'),
	url(r'^update_answer/$', views.update_answer, name='update_answer'),
	url(r'^update_comment/$', views.update_comment, name='update_comment'),
	url(r'^delete_comment/$', views.delete_comment, name='delete_comment'),
	url(r'^delete_answer/$', views.delete_answer, name='delete_answer'),
	url(r'^like_comment/$', views.LikeComment, name='like_comment'),
	url(r'^(?P<id>[0-9]+)/delete_post/$', views.delete_post, name='delete_post'),
	url(r'^(?P<id>[0-9]+)/update_post/$', views.update_post, name='update_post'),
	url(r'^remove_tag/$', views.RemoveTag, name= 'remove_tag'),
	url(r'^question_id_/(?P<id>[0-9]+)/$', views.ParticularQuestion, name= 'single_question'),
	url(r'^upvote_ques/(?P<id>[0-9]+)$', views.upvoteQuestion, name='upvote_ques'),
	url(r'^downvote_ques/(?P<id>[0-9]+)$', views.downvoteQuestion, name='upvote_ques'),
	url(r'^upvote_answer/(?P<id>[0-9]+)$', views.upvoteAnswer, name='upvote_answer'),
	url(r'^downvote_answer/(?P<id>[0-9]+)$', views.downvoteAnswer, name='upvote_answer'),
	url(r'^(?P<string>[-\w]+)/$', views.TagsBasedView, name= 'tag_based_view'),
]
