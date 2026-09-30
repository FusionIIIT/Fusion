import shutil
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch

from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from django.test import RequestFactory, SimpleTestCase, TestCase

from Fusion.urls import serve_media
from applications.globals.authentication import ExpiringTokenAuthentication
from applications.globals.api.views import _deliver_otp_email
from applications.globals.decorators import active_designation, held_designations
from applications.globals.models import Designation, ExtraInfo, HoldsDesignation
from applications.globals.programme_scope import (
    canonical_programme_name,
    programme_display_name,
)


class ProgrammeNameTests(SimpleTestCase):
    def test_phd_spellings_share_one_internal_value(self):
        for value in ('PhD', 'Ph.D', 'Ph.D.', 'PHD', 'phd'):
            self.assertEqual(canonical_programme_name(value), 'PhD')

    def test_phd_display_name_is_stable_for_legacy_values(self):
        for value in ('PhD', 'Ph.D', 'Ph.D.'):
            self.assertEqual(
                programme_display_name(value),
                'Doctor of Philosophy',
            )


class OtpDeliveryTests(SimpleTestCase):
    """The reply must not wait on SMTP: the OTP row is saved before the send,
    and the caller is told the same thing whether or not delivery works."""

    class _SlowMail:
        def __init__(self):
            self.sent = threading.Event()

        def send(self):
            time.sleep(0.3)
            self.sent.set()

    def test_a_slow_mail_host_does_not_hold_the_request(self):
        mail = self._SlowMail()
        started = time.perf_counter()
        worker = threading.Thread(target=_deliver_otp_email, args=(mail, "u1"),
                                  daemon=True)
        worker.start()
        dispatch = time.perf_counter() - started

        self.assertLess(dispatch, 0.1)
        self.assertTrue(mail.sent.wait(timeout=5))

    def test_a_delivery_failure_is_logged_and_swallowed(self):
        class Broken:
            def send(self):
                raise OSError("smtp unreachable")

        with patch("applications.globals.api.views._security_log") as log:
            _deliver_otp_email(Broken(), "u1")
        self.assertTrue(log.exception.called)


class ActingRoleTests(TestCase):
    """Authority follows the role being acted in, not every role ever held."""

    def setUp(self):
        self.user = User.objects.create_user(username='intern')
        ExtraInfo.objects.create(id='intern', user=self.user, user_type='student')
        for name in ('student', 'acadadmin'):
            HoldsDesignation.objects.create(
                user=self.user, working=self.user,
                designation=Designation.objects.create(name=name))

    def _act_as(self, role):
        self.user.extrainfo.last_selected_role = role
        self.user.extrainfo.save(update_fields=['last_selected_role'])
        self.user.refresh_from_db()

    def test_an_office_held_but_not_acted_in_grants_nothing(self):
        self._act_as('student')
        self.assertEqual(active_designation(self.user), 'student')

    def test_the_office_applies_while_it_is_the_acting_role(self):
        self._act_as('acadadmin')
        self.assertEqual(active_designation(self.user), 'acadadmin')

    def test_never_having_switched_does_not_lock_the_office_out(self):
        """The column is null for anyone who has not used the switcher."""
        self.assertEqual(active_designation(self.user), 'acadadmin')

    def test_a_role_that_is_no_longer_held_falls_back_to_one_that_is(self):
        self._act_as('acadadmin')
        HoldsDesignation.objects.filter(
            designation__name='acadadmin').delete()
        self.assertEqual(active_designation(self.user), 'student')

    def test_a_stand_in_is_authorised_and_the_absent_holder_is_not(self):
        """`working` is the occupant; `user` is the substantive holder."""
        absent = User.objects.create_user(username='absent')
        post = Designation.objects.create(name='registrar')
        HoldsDesignation.objects.create(
            user=absent, working=self.user, designation=post)
        self.assertIn('registrar', held_designations(self.user))
        self.assertNotIn('registrar', held_designations(absent))


class MediaServingTests(TestCase):
    """An upload shares this origin with the portal, so it must not be a page."""

    def setUp(self):
        self.media = tempfile.mkdtemp()
        Path(self.media, 'evil.html').write_text('<script>alert(1)</script>')

    def tearDown(self):
        shutil.rmtree(self.media, ignore_errors=True)

    def test_an_uploaded_page_is_handed_over_as_a_download(self):
        request = RequestFactory().get('/media/evil.html')
        response = serve_media(request, 'evil.html', document_root=self.media)

        self.assertEqual(response['Content-Disposition'], 'attachment')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertIn('sandbox', response['Content-Security-Policy'])


class ExpiringTokenTests(TestCase):
    """A token kept in localStorage must not be a credential for ever."""

    def setUp(self):
        self.user = User.objects.create_user(username='tokenholder')
        self.token = Token.objects.create(user=self.user)
        self.auth = ExpiringTokenAuthentication()

    def test_a_token_within_its_life_still_works(self):
        user, _ = self.auth.authenticate_credentials(self.token.key)
        self.assertEqual(user, self.user)

    def test_an_old_token_is_refused_and_destroyed(self):
        Token.objects.filter(pk=self.token.pk).update(
            created=timezone.now() - timedelta(hours=48))
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate_credentials(self.token.key)
        self.assertFalse(Token.objects.filter(pk=self.token.pk).exists())


class PlainStudentTests(TestCase):
    """Most people hold no office at all. They must keep their own screens."""

    def setUp(self):
        self.user = User.objects.create_user(username='student1')
        ExtraInfo.objects.create(id='student1', user=self.user, user_type='student')
        HoldsDesignation.objects.create(
            user=self.user, working=self.user,
            designation=Designation.objects.create(name='student'))

    def test_a_student_holding_only_the_basic_role_still_acts_in_it(self):
        self.assertEqual(active_designation(self.user), 'student')

    def test_somebody_holding_nothing_acts_in_nothing(self):
        bare = User.objects.create_user(username='nobody')
        self.assertIsNone(active_designation(bare))
