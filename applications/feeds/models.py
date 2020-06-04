from django.contrib.auth.models import Permission, User
from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
from markdown_deux import markdown

from applications.globals.models import ExtraInfo


class Constants:

	TAG_LIST = (
		('CSE', 'CSE'),
		('ECE', 'ECE'),
		('Mechanical', 'Mechanical'),
		('Technical-Clubs', 'Technical Clubs'),
		('Cultural-Clubs', 'Cultural Clubs'),
		('Sports-Clubs', 'Sports Clubs'),
		('Business-and-Career', 'Business and Career'),
		('Entertainment', 'Entertainment'),
		('IIITDMJ-Campus', 'IIITDMJ Campus'),
		('Jabalpur-city', 'Jabalpur city'),
		('IIITDMJ-Rules-and-Regulations', 'IIITDMJ rules and regulations'),
		('Academics', 'Academics'),
		('IIITDMJ', 'IIITDMJ'),
		('Life-Relationship-and-Self', 'Life Relationship and Self'),
		('Technology-and-Education', 'Technology and Education'),       
		('Programmes', 'Programmes'),
		('Others', 'Others'),
	)

	SUBTAG_LIST = (
		('Web-Development', 'Web Development'),
		('Competitive-Programming', 'Competitive Programming'),
		('Programming-Languages', 'Programming-Languages'),
		('Data-Science', 'Data-Science'),
		('Ethical-Hacking-and-Cyber-Security', 'Ethical hacking and cyber security'),
		('Cryptography-and-Network-Security', 'cryptography and network security'),
		('Software-Engineering', 'Software-Engineering'),
		('Algorithm', 'Algorithm'),
		('Mobile-Development', 'Mobile-Development'),
		('Game-Development', 'Game-Development'),
		('Artificial-Intelligence', 'Artificial Intelligence'),

		('Electronics-Circuit-Design', 'Electronics Circuit Design'),
		('Wireless-Communication', 'Wireless Communication'),
		('Embedded-System', 'Embedded Systems'),
		('VLSI', 'VLSI'),
		('Control-System', 'Control Systems'),
		('Robotics-and-others', 'Robotics and Others'),
		('Microcontrollers', 'Microcontrollers'),
		('IOT', 'IOT'),

		('Robotics', 'Robotics'),
		('Thermodynamics', 'Thermodynamics'),
		('Nanatechnology', 'Nanatechnology'),
		('Manufacturing', 'Manufacturing'),

		('Programming-and-Webix-Club', 'Programming and Webix Club'),
		('Electronics-Club', 'Electronics Club'),
		('Business-and-Management-Club', 'Business and Management Club'),
		('Robotics-Club', 'Robotics Club'),
		('CAD-Club', 'CAD Club'),
		('Astronomy-and-Physics-Society', 'ASTRONOMY AND PHYSICS SOCIETY'),
		('Aakriti-The-Film-Making-and-Photography-Club', 'AAKRITI-THE FILM MAKING AND PHOTOGRAPHY CLUB'),
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

		('Business-Models-and-Strategies', 'Business Models and strategies'),
		('Startups-and-Stratup-Strategies', 'Startups and Stratup Strategies'),
		('Entrepreneurship', 'Entrepreneurship'),
		('Finance', 'Finance'),
		('Marketing', 'Marketing'),
		('Stock-Market', 'Stock market'),
		('Career-Advice', 'Career Advice'),
		('Job-Interviews', 'Job Interviews'),

		('Journalism', 'Journalism'),
		('Entertainment', 'Entertainment'),
		('Hollywood-and-Movies', 'Hollywood and Movies'),
		('Music', 'Music'),
		('Fashion-and-Style', 'Fashion and Style'),

		('IIITDMJ-Campus', 'IIITDMJ-Campus'),

		('Jabalpur-City', 'Jabalpur City'),

		('IIITDMJ-rules-and-Regulations', 'IIITDMJ rules and regulations'),

		('Academic-Office-Stuffs', 'Academic office stuffs'),
		('Academic-Courses', 'Academic courses'),

		('Central-Mess', 'Central Mess'),
		('Alumni', 'Alumni'),
		('Hostels', 'Hostels'),
		('PHC', 'PHC'),
		('Activities', 'Activities'),
		('Counselling', 'Counselling'),
		('Achievments', 'Achievments'),
		('Library', 'Library'),
		('Faculty', 'Faculty'),
		('Staff', 'Staff'),
		('College-Fest', 'College Fest'),
		('Workshops', 'Workshops'),
		('Campus-Recruitments', 'Campus Recruitments'),
		('Jagrati', 'Jagrati'),

		('Self-Improvement', 'Self Improvement'),
		('Friendship', 'Friendship'),
		('Experiences', 'Experiences'),
		('Dating-and-Relationships', 'Dating and Relationships'),
		('Interpersonal-Interactions', 'Interpersonal Interactions'),
		('Life-and-Social-Advice', 'Life and Social Advice'),
		('Philosophy', 'Philosophy'),

		('Technology-Trends', 'Technology Trends'),
		('TED', 'TED'),
		('Higher-Education', 'Higher Education'),
		('Science-and-Universe', 'Science and Universe'),
		('Social-Media', 'Social-Media'),
		('Toron', 'Toron'),
		('Jobs-and-Internships', 'Jobs and Internships'),

		('Btech', 'Btech'),
		('Mtech', 'Mtech'),
		('Bdes', 'Bdes'),
		('Mdes', 'Mdes'),
		('Phd', 'Phd'),
		('Mechatronics', 'Mechatronics'),

		('others', 'others'),

	)


# Create your models here.


class AllTags(models.Model):
    # new = models.CharField(max_length=100, blank=True, null=True)
	tag = models.CharField(max_length=100, default='CSE', choices=Constants.TAG_LIST)
	subtag = models.CharField(max_length=100, unique=True, default='Web-Development', choices=Constants.SUBTAG_LIST)

	def __str__(self):
		return '{} - {}'.format(self.tag, self.subtag)

class AskaQuestion(models.Model):
	can_delete=models.BooleanField(default=False)
	can_update=models.BooleanField(default=False)
	user = models.ForeignKey(User, default=1,on_delete=models.CASCADE)
	subject = models.CharField(max_length=100, blank=False)
	description = models.CharField(max_length=500, null=True, blank=True, default="")
	select_tag = models.ManyToManyField(AllTags)
	file = models.FileField(null=True, blank=True)
	uploaded_at = models.DateTimeField(auto_now_add=False, auto_now=False, default=timezone.now)
	#like = models.IntegerField(default=0)
	likes = models.ManyToManyField(User, default=1,related_name='likes', blank=True)
	requests = models.ManyToManyField(User, default=1,related_name='requests', blank=True)
	#dislikes = models.ManyToManyField(User, related_name='dislikes', blank=True)
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
	user = models.ForeignKey(User, default=1, on_delete=models.CASCADE)
	content = models.TextField(max_length=1000, blank=False)
	question = models.ForeignKey(AskaQuestion, default=1, on_delete=models.CASCADE)
	uploaded_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=timezone.now)
	answers = models.ManyToManyField(User, default=1, related_name='answers', blank=True)
	total_answers = models.IntegerField(default=0)

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
	user = models.ForeignKey(User, default=1, on_delete=models.CASCADE)
	question = models.ForeignKey(AskaQuestion, default=1, on_delete = models.CASCADE)
	report_msg = models.CharField(max_length=1000,default="")

	# class Meta:
	# 	unique_together = ('user', 'question')



class hidden(models.Model):
	user = models.ForeignKey(User, default=1, on_delete=models.CASCADE)
	question = models.ForeignKey(AskaQuestion, default=1, on_delete=models.CASCADE)
	# hide = models.BooleanField(default=False)

	class Meta:
		unique_together = ('user', 'question')

	def __str__(self):
		return '{} - hide - {}'.format(self.user, self.question)


class tags(models.Model):
	user = models.ForeignKey(User, default=1, on_delete=models.CASCADE)
	my_tag = models.CharField(max_length=100, default=1, choices=Constants.TAG_LIST)
	my_subtag = models.ForeignKey(AllTags, default=1, on_delete = models.CASCADE)

	# class Meta:
	# 	unique_together = ('user', 'my_subtag')

	def __str__(self):
		return '%s is interested in ----> %s - %s' % (self.user, self.my_tag, self.my_subtag.subtag)
