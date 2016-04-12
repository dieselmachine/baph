from datetime import datetime
import re

from sqlalchemy.orm import joinedload

from baph.contrib.auth.models import User, Organization, UserManager
from baph.contrib.auth.registration import settings as auth_settings
from baph.contrib.auth.utils import generate_sha1


SHA1_RE = re.compile('^[a-f0-9]{40}$')

class SignupManager(UserManager):

    def create_user(self, username, email, password, active=False,
                    send_email=True, **kwargs):
        
        new_user = get_user_model().objects.create_user(
            username, email, password, **kwargs)
        new_user.is_active = active
        new_user.save()

        signup = self.create_signup(new_user)

        if send_email:
            signup.send_activation_email()

        return new_user

    def create_signup(self, user):

        if isinstance(user.username, text_type):
            user.username = smart_text(user.username)
        salt, activation_key = generate_sha1(user.username)

        try:
            signup = self.get(user=user)
        except self.model.DoesNotExist:
            signup = self.create(user=user, activation_key=activation_key)
        return profile

    def reissue_activation(self, activation_key):
        """
        Creates a new ``activation_key`` resetting activation timeframe when
        users let the previous key expire.

        :param activation_key:
            String containing the secret SHA1 activation key.

        """
        try:
            signup = self.get(activation_key=activation_key)
        except self.model.DoesNotExist:
            return False
        try:
            salt, new_activation_key = generate_sha1(signup.user.username)
            signup.activation_key = new_activation_key
            signup.save(using=self._db)
            signup.user.date_joined = get_datetime_now()
            signup.user.save(using=self._db)
            signup.send_activation_email()
            return True
        except Exception:
            return False

    def activate_user(self, activation_key):
        """
        Activate an :class:`User` by supplying a valid ``activation_key``.

        If the key is valid and an user is found, activates the user and
        return it. Also sends the ``activation_complete`` signal.

        :param activation_key:
            String containing the secret SHA1 for a valid activation.

        :return:
            The newly activated :class:`User` or ``False`` if not successful.

        """
        if SHA1_RE.search(activation_key):
            try:
                signup = self.get(activation_key=activation_key)
            except self.model.DoesNotExist:
                return False
            if not signup.activation_key_expired():
                signup.activation_key = auth_settings.BAPH_ACTIVATED
                user = signup.user
                user.is_active = True
                signup.save(using=self._db)
                user.save(using=self._db)

                # Send the activation_complete signal
                #userena_signals.activation_complete.send(sender=None,
                #                                         user=user)
                return user
        return False

    def check_expired_activation(self, activation_key):
        """
        Check if ``activation_key`` is still valid.

        Raises a ValueError exception if activation_key is invalid

        Raises a ``sqlalchemy.orm.exc.NoResultFound`` exception if key is not
            present

        :param activation_key:
            String containing the secret SHA1 for a valid activation.

        :return:
            True if the key has expired, False if still valid.

        """
        if SHA1_RE.search(activation_key):
            signup = self.get(activation_key=activation_key)
            return signup.activation_key_expired()
        raise self.model.DoesNotExist

    def confirm_email(self, confirmation_key):
        """
        Confirm an email address by checking a ``confirmation_key``.

        A valid ``confirmation_key`` will set the newly wanted e-mail
        address as the current e-mail address. Returns the user after
        success or ``False`` when the confirmation key is
        invalid. Also sends the ``confirmation_complete`` signal.

        :param confirmation_key:
            String containing the secret SHA1 that is used for verification.

        :return:
            The verified :class:`User` or ``False`` if not successful.

        """
        if SHA1_RE.search(confirmation_key):
            try:
                signup = self.get(email_confirmation_key=confirmation_key,
                                  email_unconfirmed__isnull=False)
            except self.model.DoesNotExist:
                return False
            else:
                user = signup.user
                old_email = user.email
                user.email = signup.email_unconfirmed
                signup.email_unconfirmed, signup.email_confirmation_key = '',''
                userena.save(using=self._db)
                user.save(using=self._db)

                # Send the confirmation_complete signal
                #userena_signals.confirmation_complete.send(sender=None,
                #                                           user=user,
                #                                           old_email=old_email)

            return user
        return False

    def delete_expired_users(self):
        """
        Checks for expired users and delete's the ``User`` associated with
        it. Skips if the user ``is_staff``.

        :return: A list containing the deleted users.

        """
        deleted_users = []
        for user in get_user_model().objects.filter(is_staff=False,
                                                    is_active=False):
            if user.signup.activation_key_expired():
                deleted_users.append(user)
                user.delete()
        return deleted_users

    '''
    @staticmethod
    def get(pk=None, **kwargs):
        session = orm.sessionmaker()
        if pk:
            obj = session.query(UserRegistration).get(pk)
        else:
            obj = session.query(UserRegistration).filter_by(**kwargs).first()
        return obj
    '''
#UserRegistration.objects = SignupManager
