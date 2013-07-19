# -*- coding: utf-8 -*-
'''
:mod:`baph.auth.registration.forms` -- Registration-related Forms
=================================================================

Forms and validation code for user registration.
'''
from hashlib import sha1 as sha_constructor
import random
#from baph.db.orm import ORM
#from baph.utils.importing import import_any_module
#dforms = import_any_module(['django.forms'])
from django import forms
from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _
from sqlalchemy.orm import joinedload
#forms = import_any_module(['registration.forms'])
#Checkbox = dforms.CheckboxInput
#orm = ORM.get()
#TERMS_ERROR_MSG = _(u'You must agree to the terms to register')
#TERMS_LABEL = _(u'I have read and agree to the Terms of Service')
from baph.auth.models import User, Organization
from baph.auth.registration import settings
from baph.auth.registration.managers import SignupManager
from baph.auth.registration.models import BaphSignup
from baph.auth.utils import generate_sha1
from baph.db import Session


attrs_dict = {'class': 'required'}

"""
class RegistrationForm(forms.RegistrationForm):
    '''An SQLAlchemy-based version of django-registration's
    ``RegistrationForm``.
    '''

    def clean_username(self):
        '''Validate that the username is alphanumeric and is not already in
        use.
        '''
        session = orm.sessionmaker()
        user_ct = session.query(User) \
                         .filter_by(username=self.cleaned_data['username']) \
                         .count()
        if user_ct == 0:
            return self.cleaned_data['username']
        else:
            raise dforms.ValidationError(_(u'''\
A user with that username already exists.'''))
"""
"""
class RegistrationFormTermsOfService(RegistrationForm):
    '''Subclass of :class:`RegistrationForm` which adds a required checkbox
    for agreeing to a site's Terms of Service.
    '''
    tos = dforms.BooleanField(widget=Checkbox(attrs=forms.attrs_dict),
                              label=TERMS_LABEL,
                              error_messages={'required': TERMS_ERROR_MSG})


class RegistrationFormUniqueEmail(RegistrationForm):
    '''Subclass of :class:`RegistrationForm`, which enforces uniqueness of
    email addresses.
    '''
    def clean_email(self):
        '''Validate that the supplied email address is unique for the site.'''
        session = orm.sessionmaker()
        user_ct = session.query(User) \
                         .filter_by(email=self.cleaned_data['email']) \
                         .count()
        if user_ct == 0:
            return self.cleaned_data['email']
        else:
            raise dforms.ValidationError(_(u'''\
This email address is already in use. Please supply a different email
address.'''.replace('\n', ' ')))


class RegistrationFormNoFreeEmail(RegistrationForm):
    '''Subclass of :class:`RegistrationForm` which disallows registration with
    email addresses from popular free webmail services; moderately useful for
    preventing automated spam registrations.

    To change the list of banned domains, subclass this form and
    override the attribute ``bad_domains``.
    '''
    bad_domains = ['aim.com', 'aol.com', 'email.com', 'gmail.com',
                   'googlemail.com', 'hotmail.com', 'hushmail.com',
                   'msn.com', 'mail.ru', 'mailinator.com', 'live.com',
                   'yahoo.com']

    def clean_email(self):
        '''Check the supplied email address against a list of known free
        webmail domains.
        '''
        email_domain = self.cleaned_data['email'].split('@')[1]
        if email_domain in self.bad_domains:
            raise dforms.ValidationError(_(u'''\
Registration using free email addresses is prohibited. Please supply a
different email address.'''.replace('\n', ' ')))
        return self.cleaned_data['email']
"""

def identification_field_factory(label, error_required):
    """
    A simple identification field factory which enable you to set the label.

    :param label:
        String containing the label for this field.

    :param error_required:
        String containing the error message if the field is left empty.

    """
    return forms.CharField(label=label,
                           widget=forms.TextInput(attrs=attrs_dict),
                           max_length=75,
                           error_messages={'required': _("%(error)s") % {'error': error_required}})

class AuthenticationForm(forms.Form):
    """
    A custom form where the identification can be a e-mail address or username.

    """
    identification = identification_field_factory(_(u"Email or username"),
                       _(u"Either supply us with your email or username."))
    password = forms.CharField(label=_("Password"),
          widget=forms.PasswordInput(attrs=attrs_dict, render_value=False))
    remember_me = forms.BooleanField(widget=forms.CheckboxInput(),
                                     required=False,
                                     label=_(u'Remember me for %(days)s') \
               % {'days': _(settings.BAPH_REMEMBER_ME_DAYS[0])})

    def __init__(self, *args, **kwargs):
        """ A custom init because we need to change the label if no usernames is used """
        super(AuthenticationForm, self).__init__(*args, **kwargs)
        # Dirty hack, somehow the label doesn't get translated without declaring
        # it again here.
        self.fields['remember_me'].label = _(u'Remember me for %(days)s') \
            % {'days': _(settings.BAPH_REMEMBER_ME_DAYS[0])}
        if settings.BAPH_WITHOUT_USERNAMES:
            self.fields['identification'] = identification_field_factory(
                _(u"Email"),
                _(u"Please supply your email."))

    def clean(self):
        """
        Checks for the identification and password.

        If the combination can't be found will raise an invalid sign in error.

        """
        identification = self.cleaned_data.get('identification')
        password = self.cleaned_data.get('password')

        if identification and password:
            user = authenticate(identification=identification, password=password)
            if user is None:
                raise forms.ValidationError(_(u"Please enter a correct "
                    "username or email and password. Note that both fields "
                    "are case-sensitive."))
        return self.cleaned_data

class SignupForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        base_form = User.get_form_class()
        if not settings.BAPH_WITHOUT_USERNAMES:
            field_name = User.USERNAME_FIELD
            self.fields[field_name] = base_form.base_fields[field_name]
        for field_name in User.REQUIRED_FIELDS:
            self.fields[field_name] = base_form.base_fields[field_name]
        for field_name in ['password1', 'password2']:
            label = 'Create password' if field_name == 'password1' \
                else 'Repeat Password'
            self.fields[field_name] = forms.CharField(
                widget=forms.PasswordInput(attrs=attrs_dict,
                    render_value=False),
                label=_(label))

    def clean_username(self):
        col = getattr(User, User.USERNAME_FIELD)
        session = Session()
        user = session.query(User) \
            .options(joinedload('signup')) \
            .filter(col==self.cleaned_data[User.USERNAME_FIELD]) \
            .first()
        if user and user.signup and user.signup.activation_key != settings.BAPH_ACTIVATED:
            raise forms.ValidationError(_('This username is already taken but '
                'not yet confirmed. Please check your email for verification '
                'steps.'))
        if user:
            raise forms.ValidationError(_('This username is already taken'))
        return self.cleaned_data[User.USERNAME_FIELD]

    def clean_email(self):
        col = getattr(User, 'email')
        session = Session()
        user = session.query(User) \
            .options(joinedload('signup')) \
            .filter(col==self.cleaned_data['email']) \
            .first()
        if user and user.signup and user.signup.activation_key != settings.BAPH_ACTIVATED:
            raise forms.ValidationError(_('This email is already taken but '
                'not yet confirmed. Please check your email for verification '
                'steps.'))
        if user:
            raise forms.ValidationError(_('This email is already taken'))
        return self.cleaned_data['email']

    def clean(self):
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_('The two password fields didn\'t match.'))
        return self.cleaned_data

    def save(self):
        """ Creates a new user and account. Returns the newly created user. """
        username, email, password = (self.cleaned_data[User.USERNAME_FIELD],
                                     self.cleaned_data['email'],
                                     self.cleaned_data['password1'])
        extra_kwargs = dict(i for i in self.cleaned_data.items() if i[0] not in
                       [User.USERNAME_FIELD, 'email', 'password1', 'password2'])

        new_user = SignupManager.create_user(username,
                                             email,
                                             password,
                                             not settings.BAPH_ACTIVATION_REQUIRED,
                                             settings.BAPH_ACTIVATION_REQUIRED,
                                             **extra_kwargs)
        return new_user


class SignupFormOnlyEmail(SignupForm):
    """
    Form for creating a new user account but not needing a username.

    This form is an adaptation of :class:`SignupForm`. It's used when
    ``USERENA_WITHOUT_USERNAME`` setting is set to ``True``. And thus the user
    is not asked to supply an username, but one is generated for them. The user
    can than keep sign in by using their email.

    """
    def __init__(self, *args, **kwargs):
        super(SignupFormOnlyEmail, self).__init__(*args, **kwargs)
        if 'username' in self.fields:
            del self.fields['username']

    def save(self):
        """ Generate a random username before falling back to parent signup form """
        session = Session()
        while True:
            username = sha_constructor(str(random.random())).hexdigest()[:5]
            user = session.query(User).filter(User.username==username).first()
            if not user:
                break

        self.cleaned_data['username'] = username
        return super(SignupFormOnlyEmail, self).save()

class ChangeEmailForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict,
                                                               maxlength=75)),
                             label=_(u"New email"))

    def __init__(self, user, *args, **kwargs):
        """
        The current ``user`` is needed for initialisation of this form so
        that we can check if the email address is still free and not always
        returning ``True`` for this query because it's the users own e-mail
        address.

        """
        super(ChangeEmailForm, self).__init__(*args, **kwargs)
        if not isinstance(user, User):
            raise TypeError, "user must be an instance of %s" % User._meta.model_name
        else: self.user = user

    def clean_email(self):
        """ Validate that the email is not already in use """
        if self.cleaned_data['email'].lower() == self.user.email:
            raise forms.ValidationError(_(u'You\'re already known under this '
                'email.'))
        session = Session()
        user = session.query(User) \
            .filter(User.email == self.cleaned_data['email']) \
            .filter(User.email != self.user.email) \
            .first()
        if user:
            raise forms.ValidationError(_(u'This email is already in use. '
                'Please supply a different email.'))
        return self.cleaned_data['email']

    def save(self):
        """
        Save method calls :func:`user.change_email()` method which sends out an
        email with an verification key to verify and with it enable this new
        email address.

        """
        return self.user.signup.change_email(self.cleaned_data['email'])
