import datetime
import hashlib
import re

from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.models import Site
from django.core import mail
from django.conf import settings

from baph.auth.models import User
from baph.auth.registration.models import BaphSignup
from baph.auth.registration import settings as auth_settings
from baph.db import Session
from baph.test import TestCase


MUGSHOT_RE = re.compile('^[a-f0-9]{40}$')

class SignupModelTests(TestCase):
    """ Test the model of UserenaSignup """
    user_info = {'username': 'alice',
                 'password': 'swordfish',
                 'email': 'alice@example.com'}

    fixtures = ['users']

    def test_stringification(self):
        """
        Test the stringification of a ``UserenaSignup`` object. A
        "human-readable" representation of an ``UserenaSignup`` object.

        """
        signup = BaphSignup.objects.get(pk=1)
        self.failUnlessEqual(signup.__unicode__(),
                             signup.user.username)

    def test_change_email(self):
        """ TODO """
        pass

    def test_activation_expired_account(self):
        """
        ``UserenaSignup.activation_key_expired()`` is ``True`` when the
        ``activation_key_created`` is more days ago than defined in
        ``USERENA_ACTIVATION_DAYS``.

        """
        user = BaphSignup.objects.create_user(**self.user_info)
        user.date_joined -= datetime.timedelta(days=auth_settings.BAPH_ACTIVATION_DAYS + 1)
        user.save()

        session = Session()
        user = session.query(User).filter_by(username='alice').first()
        self.failUnless(user.signup.activation_key_expired())

    def test_activation_used_account(self):
        """
        An user cannot be activated anymore once the activation key is
        already used.

        """
        user = BaphSignup.objects.create_user(**self.user_info)
        activated_user = BaphSignup.objects.activate_user(user.signup.activation_key)
        self.failUnless(activated_user.signup.activation_key_expired())

    def test_activation_unexpired_account(self):
        """
        ``UserenaSignup.activation_key_expired()`` is ``False`` when the
        ``activation_key_created`` is within the defined timeframe.``

        """
        user = BaphSignup.objects.create_user(**self.user_info)
        self.failIf(user.signup.activation_key_expired())

    def test_activation_email(self):
        """
        When a new account is created, a activation e-mail should be send out
        by ``UserenaSignup.send_activation_email``.

        """
        new_user = BaphSignup.objects.create_user(**self.user_info)
        self.failUnlessEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user_info['email']])
