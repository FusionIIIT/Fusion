from django.conf.urls import url

from . import views

app_name = 'feeds'

urlpatterns=[
	#feeds homepage,profile and feeds admin
	url(r'^$', views.feeds, name= 'feeds'),
	url(r'^profile/(?P<string>[-\w]+)/$', views.profile, name= 'profile'),
	url(r'^administrative/(?P<string>[-\w]+)/$', views.administrativeView, name= 'administrative_view'),
	url(r'^admin',views.admin, name='feeds_admin'),
	url(r'^request/$', views.Request, name= 'request'),
	#deleting and updating comments and answers
	url(r'^comment_text/$', views.Comment_Text, name='comment_text'),
	url(r'^reply_text/$', views.Reply_Text, name='reply_text'),
	url(r'^update_answer/$', views.update_answer, name='update_answer'),
	url(r'^update_comment/$', views.update_comment, name='update_comment'),
	url(r'^delete_comment/$', views.delete_comment, name='delete_comment'),
	url(r'^delete_answer/$', views.delete_answer, name='delete_answer'),
	url(r'^like_comment/$', views.LikeComment, name='like_comment'),
	#deleting, updating, hiding and unhiding a post
	url(r'^(?P<id>[0-9]+)/delete_post/$', views.delete_post, name='delete_post'),
	url(r'^(?P<id>[0-9]+)/update_post/$', views.update_post, name='update_post'),
	url(r'^(?P<id>[0-9]+)/hide_post/$', views.hide_post, name='hide_post'),
	url(r'^(?P<id>[0-9]+)/unhide_post/$', views.unhide_post, name='unhide_post'),
	#remove a tag from taglist
	url(r'^remove_tag/$', views.RemoveTag, name= 'remove_tag'),
	#going to a particular question 
	url(r'^question_id_/(?P<id>[0-9]+)/$', views.ParticularQuestion, name= 'single_question'),
	#upvoting and downvoting a question and answers
	url(r'^upvote_ques/(?P<id>[0-9]+)$', views.upvoteQuestion, name='upvote_ques'),
	url(r'^downvote_ques/(?P<id>[0-9]+)$', views.downvoteQuestion, name='upvote_ques'),
	url(r'^upvote_answer/(?P<id>[0-9]+)$', views.upvoteAnswer, name='upvote_answer'),
	url(r'^downvote_answer/(?P<id>[0-9]+)$', views.downvoteAnswer, name='upvote_answer'),
	#questions selected based on selected tags
	url(r'^(?P<string>[-\w]+)/$', views.TagsBasedView, name= 'tag_based_view'),
]
