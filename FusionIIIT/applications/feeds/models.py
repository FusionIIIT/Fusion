from django.contrib.auth.models import Permission, User
from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
from markdown_deux import markdown

from applications.globals.models import ExtraInfo


class Constants:
	"""
	contains record of all tags and subtags 
	'TAG_LIST' - record of all tags
	'SUBTAG_LIST' -  record of all subtags
	"""
	TAG_LIST = (
		('CSE', 'CSE'),
		('ECE', 'ECE'),
		('MECHANICAL', 'MECHANICAL'),
		('TECHNICAL-CLUBS', 'TECHNICAL CLUBS'),
		('CULTURAL-CLUBS', 'CULTURAL CLUBS'),
		('SPORTS-CLUBS', 'SPORTS CLUBS'),
		('BUSINESS-AND-CAREER', 'BUSINESS AND CAREER'),
		('ENTERTAINMENT', 'ENTERTAINMENT'),
		('IIITDMJ-CAMPUS', 'IIITDMJ Campus'),
		('JABALPUR-CITY', 'JABALPUR CITY'),
		('IIITDMJ-RULES-AND-REGULATIONS', 'IIITDMJ RULES AND REGULATIONS'),
		('ACADEMICS', 'ACADEMICS'),
		('IIITDMJ', 'IIITDMJ'),
		('LIFE-RELATIONSHIPS-AND-SELF', 'LIFE RELATIONSHIPS AND SELF'),
		('TECHNOLOGY-AND-EDUCATION', 'TECHNOLOGY AND EDUCATION'),       
		('PROGRAMMES', 'PROGRAMMES'),
		('OTHERS', 'OTHERS'),
		('DESIGN', 'DESIGN'),
	)

	SUBTAG_LIST = (
		('WEB-DEVELOPMENT', 'WEB DEVELOPMENT'),
		('COMPETITIVE-PROGRAMMING', 'COMPETITIVE PROGRAMMING'),
		('PROGRAMMING-LANGUAGES', 'PROGRAMMING-LANGUAGES'),
		('DATA-SCIENCE', 'DATA-SCIENCE'),
		('ETHICAL-HACKING-AND-CYBER-SECURITY', 'ETHICAL HACKING AND CYBER SECURITY'),
		('CRYPTOGRAPHY-AND-NETWORK-SECURITY', 'CRYPTOGRAPHY AND NETWORK SECURITY'),
		('SOFTWARE-ENGINEERING', 'SOFTWARE-ENGINEERING'),
		('ALGORITHM', 'ALGORITHM'),
		('MOBILE-DEVELOPMENT', 'MOBILE-DEVELOPMENT'),
		('GAME-DEVELOPMENT', 'GAME-DEVELOPMENT'),
		('ARTIFICIAL-INTELLIGENCE', 'ARTIFICIAL INTELLIGENCE'),

		('ELECTRONICS-CIRCUIT-DESIGN', 'ELECTRONICS CIRCUIT DESIGN'),
		('WIRELESS-COMMUNICATION', 'WIRELESS COMMUNICATION'),
		('EMBEDDED-SYSTEM', 'EMBEDDED SYSTEM'),
		('VLSI', 'VLSI'),
		('CONTROL-SYSTEM', 'CONTROL SYSTEM'),
		('ROBOTICS-AND-OTHERS', 'ROBOTICS AND OTHES'),
		('MICROCONTROLLES', 'MICROCONTROLLERS'),
		('IOT', 'IOT'),

		('ROBOTICS', 'ROBOTICS'),
		('THERMODYNAMICS', 'THERMODYNAMICS'),
		('NANATECHNOLOGY', 'NANATECHNOLOGY'),
		('MANUFACTURING', 'MANUFACTURING'),

		('PROGRAMMING-AND-WEBIX-CLUB', 'PROGRAMMING AND WEBIX CLUB'),
		('ELECTRONICS-CLUB', 'ELECTRONICS CLUB'),
		('BUSINESS-AND-MANAGEMENT-CLUB', 'BUSINESS AND MANAGEMENT CLUB'),
		('ROBOTICS-CLUB', 'ROBOTICS CLUB'),
		('CAD-CLUB', 'CAD CLUB'),
		('ASTRONOMY-AND-PHYSICS-SOCIETY', 'ASTRONOMY AND PHYSICS SOCIETY'),
		('AAKRITI-THE-FILM-MAKING-AND-PHOTOGRAPHY-CLUB', 'AAKRITI-THE FILM MAKING AND PHOTOGRAPHY CLUB'),
		('AUTOMOTIVE-AND-FABRICATION-CLUB', 'AUTOMOTIVE AND FABRICATION CLUB'),
		('RACING-CLUB', 'RACING CLUB'),

		('SAAZ-MUSIC-CLUB', 'SAAZ-MUSIC CLUB'),
		('SAMVAAD-THE-LITERATURE-AND-QUIZZING-SOCIETY', 'SAMVAAD-THE LITERATURE AND QUIZZING SOCIETY'),
		('ABHIVYAKTI-ARTS-CLUB', 'ABHIVYAKTI-ARTS CLUB'),
		('JAZBAAT-THE-DRAMATICS-SOCIETY', 'JAZBAAT-THE DRAMATICS SOCIETY'),
		('AAVARTAN-DANCE-CLUB', 'AAVARTAN-DANCE CLUB'),

		('BADMINTON-CLUB', 'BADMINTON CLUB'),
		('LAWN-TENNIS-&-BASKETBALL-CLUB', 'LAWN TENNIS&BASKETBALL CLUB'),
		('TABLE-TENNIS', 'TABLE TENNIS'),
		('CHESS-&-CARROM-CLUB', 'CHESS & CARROM CLUB'),
		('CRICKET-CLUB', 'CRICKET CLUB'),
		('FOOTBALL-CLUB', 'FOOTBALL CLUB'),
		('VOLLEYBALL-CLUB', 'VOLLEYBALL CLUB'),
		('ATHLETICS-CLUB', 'ATHLETICS CLUB'),

		('BUSINES-MODELS-AND-STRATEGIES', 'BUSINES-MODELS-AND-STRATEGIES'),
		('STARTUPS-AND-STARTUP-STRATEGIES', 'STARTUP AND STARTUP STRATEGIES'),
		('ENTERPRENEURSHIP', 'ENTERPRENEURSHIP'),
		('FINANCE', 'FINANCE'),
		('MARKETING', 'MARKETING'),
		('STOCK-MARKET', 'STOCK MARKET'),
		('CAREER-ADVICE', 'CAREER ADVICE'),
		('JOB-INTERVIEWS', 'JOB INTERVIEWS'),

		('JOURNALISM', 'JOURNALISM'),
		('ENTERTAINMENT', 'ENTERTAINMENT'),
		('HOLLYWOOD-AND-MOVIES', 'HOLLYWOOD AND MOVIES'),
		('MUSIC', 'MUSIC'),
		('FASHION-AND-STYLE', 'FASHION AND STYLE'),

		('IIITDMJ-CAMPUS', 'IIITDMJ-CAMPUS'),

		('JABALPUR-CITY', 'JABALPUR CITY'),

		('IIITDMJ-RULES-AND-REGULATIONS', 'IIITDMJ RULES AND REGULATIONS'),

		('ACADEMIC-OFFICE-STUFFS', 'ACADEMIC OFFICE STUFFS'),
		('ACADEMIC-COURSES', 'ACADEMIC COURSES'),

		('CENTRAL-MESS', 'CENTRAL MESS'),
		('ALUMNI', 'ALUMNI'),
		('HOSTELS', 'HOSTELS'),
		('PHC', 'PHC'),
		('ACTIVITIES', 'ACTIVITIES'),
		('Counselling', 'Counselling'),
		('ACHIEVMENTS', 'ACHIEVMENTS'),
		('LIBRARY', 'LIBRARY'),
		('FACULTY', 'FACULTY'),
		('STAFF', 'STAFF'),
		('COLLEGE-FEST', 'COLLEGE FEST'),
		('WORKSHOPS', 'WORKSHOPS'),
		('CAMPUS-RECRUITMENTS', 'CAMPUS RECRUITMENTS'),
		('JAGRATI', 'JAGRATI'),

		('SELF-IMPROVEMENT', 'SELF IMPROVEMENT'),
		('FRIENDSHIP', 'FRIENDSHIP'),
		('EXPERIENCES', 'EXPERIENCES'),
		('DATING-AND-RELATIONSHIPS', 'DATING AND RELATIONSHIPS'),
		('INTERPERSONAL-INTERACTIONS', 'INTERPERSONAL INTERACTIONS'),
		('LIFE-AND-SOCIAL-ADVICE', 'LIFE AND SOCIAL ADVICE'),
		('PHILOSOPHY', 'PHILOSOPHY'),

		('TECHNOLOGY-TRENDS', 'TECHNOLOGY TRENDS'),
		('TED', 'TED'),
		('HIGHER-EDUCATION', 'HIGHER EDUCATION'),
		('SCIENCE-AND-UNIVERSE', 'SCIENCE AND UNIVERSE'),
		('SOCIAL-MEDIA', 'SOCIAL-MEDIA'),
		('TORON', 'TORON'),
		('JOBS-AND-INTERNSHIPS', 'JOBS AND INTERNSHIPS'),

		('BTECH', 'BTECH'),
		('MTECH', 'MTECH'),
		('BDES', 'BDES'),
		('MDES', 'MDES'),
		('PHD', 'PHD'),
		('MECHATRONICS', 'MECHATRONICS'),

		('OTHERS', 'OTHERS'),

	)


# Create your models here.


class AllTags(models.Model):
	"""
	records tags and subtags in database 
	"""
    # new = models.CharField(max_length=100, blank=True, null=True)
	tag = models.CharField(max_length=100, default='CSE', choices=Constants.TAG_LIST)
	subtag = models.CharField(max_length=100, unique=True, default='Web-Development', choices=Constants.SUBTAG_LIST)

	def __str__(self):
		return '{} - {}'.format(self.tag, self.subtag)

class AskaQuestion(models.Model):
	"""
	Records questions asked by users
	"""
	can_delete=models.BooleanField(default=False)
	can_update=models.BooleanField(default=False)
	user = models.ForeignKey(User, default=1,on_delete=models.CASCADE)
	subject = models.CharField(max_length=100, blank=False)
	description = models.CharField(max_length=500, null=True, blank=True, default="")
	select_tag = models.ManyToManyField(AllTags)
	file = models.FileField(null=True, blank=True,upload_to='feeds/files')
	uploaded_at = models.DateTimeField(auto_now_add=False, auto_now=False, default=timezone.now)
	likes = models.ManyToManyField(User, default=1,related_name='likes', blank=True)
	dislikes = models.ManyToManyField(User, default=1,related_name='dislikes', blank=True)
	requests = models.ManyToManyField(User, default=1,related_name='requests', blank=True)
	is_liked=models.BooleanField(default=False)
	is_requested=models.BooleanField(default=False)
	request = models.IntegerField(default=0)
	anonymous_ask = models.BooleanField(default=False)
	total_likes=models.IntegerField(default=0)
	total_dislikes=models.IntegerField(default=0)

	# class Meta:
	# 	unique_together = ('subject', 'select_tag')

	def total_likes(self):
		return self.likes.count()
	
	def total_dislikes(self):
		return self.dislikes.count()

	def total_requests(self):
		return self.requests.count()

	def get_markdown(self):
		content = self.description
		markdown_text = markdown(content)
		markdown_text = mark_safe(markdown_text)
		return markdown_text
			
	def __str__(self):
		return '{} added ----> {} in {}'.format(self.user, self.subject, self.select_tag)

class AnsweraQuestion(models.Model):
	"""
	Records answers on a question
	"""
	user = models.ForeignKey(User, default=1, on_delete=models.CASCADE)
	content = models.TextField(max_length=1000, blank=False)
	question = models.ForeignKey(AskaQuestion, default=1, on_delete=models.CASCADE)
	uploaded_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=timezone.now)
	answers = models.ManyToManyField(User, default=1, related_name='answers', blank=True)
	total_answers = models.IntegerField(default=0)
	likes = models.ManyToManyField(User, default=1,related_name='answer_likes', blank=True)
	dislikes = models.ManyToManyField(User, default=1,related_name='answer_dislikes', blank=True)
	is_liked=models.BooleanField(default=False)

	def total_likes(self):
		return self.likes.count()
	
	def total_votes(self):
		return self.likes.count() - self.dislikes.count()

	def total_dislikes(self):
		return self.dislikes.count()

	def total_requests(self):
		return self.requests.count()
		
	def __str__(self):
		return '{} - answered the question - {}'.format(self.content, self.question)

	def get_markdown(self):
		content = self.content
		markdown_text = markdown(content)
		markdown_text = mark_safe(markdown_text)
		return markdown_text

	def total_answers(self):
		return self.answers.count()

class Comments(models.Model):
	"""
	Records comments on posts
	"""
	user = models.ForeignKey(User, default=1, on_delete=models.CASCADE)
	question = models.ForeignKey(AskaQuestion, default=1 , on_delete = models.CASCADE)
	comment_text = models.CharField(max_length=5000)
	likes_comment = models.ManyToManyField(User, default=1,related_name='likes_comment', blank=True)
	total_likes_comment = models.IntegerField(default=0)
	commented_at = models.DateTimeField(auto_now_add=False, auto_now=False, default=timezone.now)
	is_liked = models.BooleanField(default=False)

	def __str__(self):
		return self.comment_text

	def total_likes_comment(self):
		return self.likes_comment.count()

class Reply(models.Model):
	"""
	Records replies on a post
	"""
	user = models.ForeignKey(User, default=1, on_delete=models.CASCADE)
	comment = models.ForeignKey(Comments,default=1, on_delete=models.CASCADE)
	msg = models.CharField(max_length=1000)
	content = models.CharField(max_length=5000, default="")
	replies = models.ManyToManyField(User, default=1,related_name='replies', blank=True)
	total_replies = models.IntegerField(default=0)
	replied_at = models.DateTimeField(auto_now_add=False, auto_now=False, default=timezone.now)

	def __str__(self):
		return '{} - replied on  - {} at {}'.format(self.user, self.comment, self.replied_at)

	def total_replies(self):
		return self.replies.count()

class report(models.Model):
	"""
	records report on a quesiton
	"""
	user = models.ForeignKey(User, default=1, on_delete=models.CASCADE)
	question = models.ForeignKey(AskaQuestion, default=1, on_delete = models.CASCADE)
	report_msg = models.CharField(max_length=1000,default="")

	# class Meta:
	# 	unique_together = ('user', 'question')

class hidden(models.Model):
	"""
	records a hidden question
	"""
	user = models.ForeignKey(User, default=1, on_delete=models.CASCADE)
	question = models.ForeignKey(AskaQuestion, default=1, on_delete=models.CASCADE)
	# hide = models.BooleanField(default=False)

	class Meta:
		unique_together = ('user', 'question')

	def __str__(self):
		return '{} - hide - {}'.format(self.user, self.question)

class tags(models.Model):
	"""
	records tags for a user
	
	"""
	user = models.ForeignKey(User, default=1, on_delete=models.CASCADE)
	my_tag = models.CharField(max_length=100, default=1, choices=Constants.TAG_LIST)
	my_subtag = models.ForeignKey(AllTags, default=1, on_delete = models.CASCADE)

	class Meta:
		unique_together = ('user', 'my_subtag')

	def __str__(self):
		return '%s is interested in ----> %s - %s' % (self.user, self.my_tag, self.my_subtag.subtag)

class Profile(models.Model):
	"""
	records profile details of a user
	"""
	user = models.ForeignKey(User, default=1, on_delete=models.CASCADE)
	bio = models.CharField(max_length=250,blank=True)
	profile_picture = models.ImageField(null=True, blank=True, upload_to='feeds/profile_pictures')
	profile_view = models.IntegerField(default=0)
	def __str__(self):
		return '%s\'s Bio is  ----> %s' % (self.user, self.bio)

class Roles(models.Model):
	"""
	Records role a for a user 
	"""
	user = models.ForeignKey(User, default=1, on_delete=models.CASCADE)
	role = models.CharField(max_length=100, blank=False)
	active = models.BooleanField(default=True)
	def __str__(self):
	 return '%s is assigned %s role' % (self.user, self.role)

class QuestionAccessControl(models.Model):
	"""
	records the different access permissions like the user can comment on a question or not, can vot or not for a user
	"""
	Question = models.ForeignKey(AskaQuestion, related_name='question_list', default=1, on_delete=models.CASCADE)
	can_vote = models.BooleanField()
	can_answer = models.BooleanField()
	can_comment = models.BooleanField()
	posted_by = models.ForeignKey(Roles, default=1, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=False, auto_now=False, default=timezone.now)
	def __str__(self):
		return "question number " + str(self.Question.id)
	
