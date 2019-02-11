from django.conf.urls import url

from . import views

app_name = 'feeds'

urlpatterns=[
	url(r'^$', views.feeds, name= 'feeds'),
	url(r'^request/$', views.Request, name= 'request'),
	url(r'^comment_text/$', views.Comment_Text, name='comment_text'),
	url(r'^reply_text/$', views.Reply_Text, name='reply_text'),
	url(r'^like_comment/$', views.LikeComment, name='like_comment'),
	url(r'^(?P<id>[0-9]+)/delete_post/$', views.delete_post, name='delete_post'),
	url(r'^(?P<id>[0-9]+)/update_post/$', views.update_post, name='update_post'),
	url(r'^(?P<string>[-\w]+)/$', views.TagsBasedView, name= 'tag_based_view'),
	url(r'^remove_tag/$', views.RemoveTag, name= 'remove_tag'),
	url(r'^question_id_/(?P<id>[0-9]+)/$', views.ParticularQuestion, name= 'single_question'),
]
