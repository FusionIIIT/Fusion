from django.conf.urls import url

from . import views

app_name = 'feeds'

urlpatterns=[
	#Feeds Home
	url(r'^$', views.feeds, name= 'feeds'),

	#User 
	url(r'^profile/(?P<string>[-\w]+)/$', views.profile, name= 'profile'),

	#Admin
	url(r'^administrative/(?P<string>[-\w]+)/$', views.administrative_view, name= 'administrative_view'),
	url(r'^admin',views.admin, name='feeds_admin'),

	#View Questions,their answers and comments on them,
	url(r'^request/$', views.Request, name= 'request'),
	url(r'^comment_text/$', views.comment_text, name='comment_text'),
	url(r'^reply_text/$', views.reply_text, name='reply_text'),

	#Update answers, update comments on a Question, delete a comment or a answer or like a comment 
	url(r'^update_answer/$', views.update_answer, name='update_answer'),
	url(r'^update_comment/$', views.update_comment, name='update_comment'),
	url(r'^delete_comment/$', views.delete_comment, name='delete_comment'),
	url(r'^delete_answer/$', views.delete_answer, name='delete_answer'),
	url(r'^like_comment/$', views.like_comment, name='like_comment'),

	#Delete a post or hide or unhide it
	url(r'^(?P<id>[0-9]+)/delete_post/$', views.delete_post, name='delete_post'),
	url(r'^(?P<id>[0-9]+)/update_post/$', views.update_post, name='update_post'),
	url(r'^(?P<id>[0-9]+)/hide_post/$', views.hide_post, name='hide_post'),
	url(r'^(?P<id>[0-9]+)/unhide_post/$', views.unhide_post, name='unhide_post'),

	#Tags
	url(r'^remove_tag/$', views.remove_tag, name= 'remove_tag'),
	#A particular Question
	url(r'^question_id_/(?P<id>[0-9]+)/$', views.particular_question, name= 'single_question'),

	#Upvote or downvote a question or answer of a question
	url(r'^upvote_ques/(?P<id>[0-9]+)$', views.upvote_question, name='upvote_ques'),
	url(r'^downvote_ques/(?P<id>[0-9]+)$', views.downvote_question, name='downvote_ques'),
	url(r'^upvote_answer/(?P<id>[0-9]+)$', views.upvote_answer, name='upvote_answer'),
	url(r'^downvote_answer/(?P<id>[0-9]+)$', views.downvote_answer, name='down_answer'),

	#View Posts based on Tags
	url(r'^(?P<string>[-\w]+)/$', views.tags_based_view, name= 'tag_based_view'),
]
