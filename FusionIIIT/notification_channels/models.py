from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import m2m_changed, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.timesince import timesince


class NotificationManager(models.Manager):

    """ Create takes arguments of notification values and returns the notification object """

    def create(self, **kwargs):
        generator = kwargs.pop("generator", None)
        target = kwargs.get("target", None)
        action_obj = kwargs.get("action_obj", None)

        """ Merge allows users to specify if a particular notification needs to be merged or not
        """
        mergeable = generator and kwargs.pop("merge", True)
        """ Notifications to a recipient will get merged when the target and
            action_verball are same for both notifications. In the case of merge url and
            description for the more recent notification will be ignored. """
        if getattr(settings, "ALLOW_NOTIFICATION_MERGE", True) and mergeable:
            try:
                com_kwargs = kwargs
                com_kwargs["action_obj_id"] = action_obj.id

                if action_obj:
                    com_kwargs.pop("action_obj", None)
                    com_kwargs["action_obj_ctype"] = ContentType.objects.get_for_model(action_obj)
                if target:
                    com_kwargs.pop("target", None)
                    com_kwargs["target_id"] = target.id
                    com_kwargs["target_ctype"] = ContentType.objects.get_for_model(target)

                notif = super(NotificationManager, self).get(**com_kwargs)

                if generator and generator not in notif.generator.all():
                    notif.seen = False
                    notif.read = False

            except Exception as e:
                notif = super(NotificationManager, self).create(**kwargs)

        else:
            notif = super(NotificationManager, self).create(**kwargs)

        if generator:
            notif.generator.add(generator)
        notif.save()
        return notif

    """ Discard notification deletes the notification or removes the generator for the """
    def discard(self, **kwargs):
        generator = kwargs.pop("generator", None)
        target = kwargs.pop("target", None)
        action_obj = kwargs.pop("action_obj", None)

        if action_obj:
            kwargs["action_obj_id"] = action_obj.id
            kwargs["action_obj_ctype"] = ContentType.objects.get_for_model(action_obj)
        if target:
            kwargs["target_id"] = action_obj.id
            kwargs["target_ctype"] = ContentType.objects.get_for_model(target)

        notif = super(NotificationManager, self).get(**kwargs)

        if getattr(settings, "ALLOW_NOTIFICATION_MERGE", True) and \
           notif.generator.all().count() > 1:
            notif.generator.remove(generator)
            notif.save()
            read_list = map(lambda x: x.read, notif.activities.all())
            flag = True
            for i in read_list:
                if not i:
                    flag = False
            notif.read = flag

            seen_list = map(lambda x: x.seen, notif.activities.all())
            flag = True
            for i in seen_list:
                if not i:
                    flag = False
            notif.seen = flag

            notif.save()
        elif not generator and not notif.generator.all().count():
            notif.delete()
        elif generator and generator in notif.generator.all():
            notif.delete()

    def seen(self, seen=True):
        queryset = super(NotificationManager, self).get_queryset()
        queryset.update(seen=seen)
        for qry in queryset:
            qry.activities.all().update(seen=seen)

    def read(self, read=True):
        queryset = super(NotificationManager, self).get_queryset()
        queryset.update(read=read)
        for qry in queryset:
            qry.activities.all().update(read=read)


class Notification(models.Model):

    """ Type can be used to group different types of notifications together """
    notif_type = models.CharField(max_length=255, blank=True, null=True)

    recipient = models.ForeignKey(User, null=False, blank=False,
                                  related_name="notifications", on_delete=models.CASCADE)

    """ Generator can be a single person in order to maintain activity stream for a user. """
    generator = models.ManyToManyField(User, related_name='activity_notifications', blank=True)

    """ target of any type can create a notification """
    target_ctype = models.ForeignKey(ContentType, related_name='related_notifications',
                                     blank=True, null=True, on_delete=models.CASCADE)
    target_id = models.CharField(max_length=255, blank=True, null=True,)
    target = GenericForeignKey('target_ctype', 'target_id')

    """ Action object can be of any type that's related to any certain notification
        for eg. a notification like '<generator> liked your post' has post as action object """
    action_obj_ctype = models.ForeignKey(ContentType, related_name='action_notifications',
                                         blank=True, null=True, on_delete=models.CASCADE)
    action_obj_id = models.CharField(max_length=255, blank=True, null=True,)
    action_obj = GenericForeignKey('action_obj_ctype', 'action_obj_id')

    """ Action verb is the activity that produced the notification
        eg. <generator> commented on <action_obj>
            <description>
        where 'commented on' is an action verb """

    """" Notification read or not """
    read = models.BooleanField(default=False, blank=False)

    """ Notification seen or not """
    seen = models.BooleanField(default=False, blank=False)

    """ action verb is the bridging verb defining the generation reason """
    action_verb = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=True, blank=True)

    """ A text to display instead of autogenerated one """
    display_text = models.CharField(max_length=255, null=True, blank=True)

    """ Reference URL points to the web address the notification needs
        to redirect the recipient to on click """
    reference_url = models.CharField(max_length=1023, blank=True, null=True, default="#")

    timestamp = models.DateTimeField(auto_now=True)

    """ Managing creation and manipulation of model """
    objects = NotificationManager()

    def __str__(self):
        if self.display_text:
            return self.display_text
        timedlta = timesince(self.timestamp, timezone.now())
        count = self.generator.all().count()
        if count == 1:
            gen = self.generator.all()[0].username
        elif count == 2:
            gen = self.generator.all()[0].username + " and " + self.generator.all()[1].username
        elif count == 0:
            gen = ""
        else:
            gen = self.generator.all()[0].username + " , " + self.generator.all()[1].username + \
                  " and " + str(count-2) + " others"
        fields = {
            'recipient': self.recipient,
            'generator': gen,
            'action_obj': self.action_obj,
            'target': self.target,
            'action_verb': self.action_verb,
            'timesince': timedlta,
        }

        if self.generator:
            if self.action_obj:
                if self.target:
                    return u'%(generator)s %(action_verb)s %(target)s on %(action_obj)s' % fields
                return u'%(generator)s %(action_verb)s %(action_obj)s' % fields
            return u'%(generator)s %(action_verb)s' % fields

        if self.action_obj:
            if self.target:
                return u'%(action_verb)s %(target)s on %(action_obj)s' % fields
            return u'%(action_verb)s %(action_obj)s' % fields
        return u'%(action_verb)s' % fields

    def __unicode__(self):
        return self.__str__(self)

    def mark_seen(self, seen=True):
        self.seen = seen
        super(Notification, self).save()

    def mark_read(self, read=True):
        self.read = read
        super(Notification, self).save()


""" Activities are to keep track of user's activity for mergeable and
    non-mergeable notifications for notification generators """


class Activity(models.Model):
    user = models.ForeignKey(User, null=False, blank=False, related_name="activities",
                             on_delete=models.CASCADE)
    notification = models.ForeignKey(Notification, null=False, blank=False,
                                     related_name="activities", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    """ Notification seen or not """
    seen = models.BooleanField(default=False, blank=False)

    """" Notification read or not """
    read = models.BooleanField(default=False, blank=False)

    def __str__(self):
        return self.user.username+" - "+self.notification.__str__()

    def __unicode__(self):
        return self.__str__()


class PushSubscriptionInfo(models.Model):
    browser_id = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(User, related_name="push_abscription")
    end_point = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    p256dh = models.CharField(max_length=255)

    def __str__(self):
        return self.user.username + "- " + self.browser_id

    def __unicode__(self):
        return self.__str__(self)


def sync_notif_add(notification, generators):
    for user in generators:
        try:
            activity = Activity.objects.get(user=user, notification=notification)
        except:
            activity = Activity.objects.create(user=user, notification=notification)
            activity.save()
        if not activity:
            activity = Activity.objects.create(user=user, notification=notification)
            activity.save()


def sync_notif_delete(notification, generators):
    for activ in notification.activities.all():
        if activ.user not in generators:
            activ.delete()


@receiver(m2m_changed, sender=Notification.generator.through)
def create_activity(sender, instance, **kwargs):
    generators = instance.generator.all()
    sync_notif_delete(instance, generators)
    sync_notif_add(instance, generators)


@receiver(post_delete, sender=Notification)
def delete_activity(sender, instance, *args, **kwargs):
    instance.activities.all().delete()


@receiver(post_delete, sender=Activity)
def remove_activity_trace(sender, instance, *args, **kwargs):
    instance.notification.generator.remove(instance.user)
