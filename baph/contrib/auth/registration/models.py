import datetime

from django.conf import settings as django_settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from sqlalchemy import *
from sqlalchemy.orm import relationship, backref, joinedload

from baph.contrib.auth.models import User, Organization
from baph.contrib.auth.registration import settings
from baph.contrib.auth.registration.managers import SignupManager
from baph.contrib.auth.registration.utils import get_protocol
from baph.contrib.auth.utils import generate_sha1
from baph.db.models.base import Model as Base


auth_class = getattr(User, 'AUTH_CLASS', User)
auth_col = getattr(auth_class, 'id')

class UserRegistration(Base):
    __tablename__ = 'baph_auth_user_registration'
    user_id = Column(Integer, ForeignKey(auth_col), primary_key=True)
    last_active = Column(DateTime)
    activation_key = Column(String(40))
    activation_notification_send = Column(Boolean, default=False)
    email_unconfirmed = Column(String(255))
    email_confirmation_key = Column(String(40))
    email_confirmation_key_created = Column(DateTime)

    user = relationship(auth_class, backref=backref('signup', uselist=False,
        cascade='all, delete, delete-orphan'))

    objects = SignupManager()

    def __unicode__(self):
        return '%s' % self.user.username

    def change_email(self, email):
        """
        Changes the email address for a user.

        A user needs to verify this new email address before it becomes
        active. By storing the new email address in a temporary field --
        ``temporary_email`` -- we are able to set this email address after the
        user has verified it by clicking on the verification URI in the email.
        This email gets send out by ``send_verification_email``.

        :param email:
            The new email address that the user wants to use.

        """
        self.email_unconfirmed = email

        salt, hash = generate_sha1(self.user.username)
        self.email_confirmation_key = hash
        self.email_confirmation_key_created = datetime.datetime.now()
        self.save()

        # Send email for activation
        self.send_confirmation_email()

    def send_confirmation_email(self):
        """
        Sends an email to confirm the new email address.

        This method sends out two emails. One to the new email address that
        contains the ``email_confirmation_key`` which is used to verify this
        this email address with :func:`UserenaUser.objects.confirm_email`.

        The other email is to the old email address to let the user know that
        a request is made to change this email address.

        """
        context = {'user': self.user,
                  'without_usernames': settings.BAPH_AUTH_WITHOUT_USERNAMES,
                  'new_email': self.email_unconfirmed,
                  'protocol': get_protocol(),
                  'confirmation_key': self.email_confirmation_key,
                  'org': Organization.get_current(),
                  'settings': django_settings,
                  }
        # Email to the old address, if present
        subject_old = render_to_string(
            'registration/emails/confirmation_email_subject_old.txt', context)
        subject_old = ''.join(subject_old.splitlines())

        message_old = render_to_string(
            'registration/emails/confirmation_email_message_old.txt', context)
        if self.user.email:
            send_mail(subject_old,
                      message_old,
                      django_settings.DEFAULT_FROM_EMAIL,
                    [self.user.email])

        # Email to the new address
        subject_new = render_to_string(
            'registration/emails/confirmation_email_subject_new.txt', context)
        subject_new = ''.join(subject_new.splitlines())

        message_new = render_to_string(
            'registration/emails/confirmation_email_message_new.txt', context)

        send_mail(subject_new,
                  message_new,
                  django_settings.DEFAULT_FROM_EMAIL,
                  [self.email_unconfirmed, ])

    def activation_key_expired(self):
        """
        Checks if activation key is expired.

        Returns ``True`` when the ``activation_key`` of the user is expired and
        ``False`` if the key is still valid.

        The key is expired when it's set to the value defined in
        ``USERENA_ACTIVATED`` or ``activation_key_created`` is beyond the
        amount of days defined in ``USERENA_ACTIVATION_DAYS``.

        """
        expiration_days = datetime.timedelta(days=settings.BAPH_ACTIVATION_DAYS)
        expiration_date = self.user.date_joined + expiration_days
        if self.activation_key == settings.BAPH_ACTIVATED:
            return True
        dt = datetime.datetime.now()
        if dt >= expiration_date:
            return True
        return False

    def send_activation_email(self):
        """
        Sends a activation email to the user.

        This email is send when the user wants to activate their newly created
        user.

        """
        context = {'user': self.user,
                  'without_usernames': settings.BAPH_AUTH_WITHOUT_USERNAMES,
                  'protocol': get_protocol(),
                  'activation_days': settings.BAPH_ACTIVATION_DAYS,
                  'activation_key': self.activation_key,
                  'org': Organization.get_current(),
                  'settings': django_settings,
                  }

        subject = render_to_string('registration/emails/activation_email_subject.txt',
                                   context)
        subject = ''.join(subject.splitlines())

        message = render_to_string('registration/emails/activation_email_message.txt',
                                   context)
        send_mail(subject,
                  message,
                  django_settings.DEFAULT_FROM_EMAIL,
                  [self.user.email, ])

