# -*- coding: utf-8 -*-
from collections import OrderedDict

#from baph.sites.models import get_current_site
from django.template.loader import render_to_string
from django import forms
from django.contrib.auth.forms import SetPasswordForm as BaseSetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.template import RequestContext
from django.utils.http import int_to_base36
from django.utils.translation import ugettext_lazy as _

from baph.contrib.auth.models import User, Organization #UNUSABLE_PASSWORD


class PasswordResetForm(forms.Form):
    email = forms.EmailField(label=_('E-mail'), max_length=75)

    def clean_email(self):
        '''Validates that a user exists with the given e-mail address.'''
        if getattr(User, 'AUTH_CLASS', None):
            cls = User.AUTH_CLASS
        else:
            cls = User
        email = self.cleaned_data['email']

        users = cls.objects.filter_by(email=email).all()
        '''
        session = orm.sessionmaker()
        users = session.query(cls).filter_by(email=email).all()
        '''
        if len(users) == 0:
            raise forms.ValidationError(_(u'''\
That e-mail address doesn't have an associated user account. Are you sure
you've registered?'''))
        self.users_cache = [u for u in users if u.has_usable_password()]
        if len(self.users_cache) == 0:
            raise forms.ValidationError(_(u'''\
That e-mail address doesn't allow the password to be set.'''))
        return email

    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None):
        '''Generates a one-use only link for resetting password and sends to
        the user.
        '''
        from django.core.mail import send_mail
        print 'users_cache:'
        for user in self.users_cache:
            print '\t', user
            if not user.has_usable_password():
                continue
            if not domain_override:
                org = Organization.get_current(request=request)
                if isinstance(org, dict):
                    site_name = org['name']
                    domain = org['host']
                else:
                    site_name = org.name
                    domain = org.host

            else:
                site_name = domain = domain_override

            context = {
                'email': user.email,
                'domain': domain,
                'site_name': site_name,
                'uid': int_to_base36(user.id),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': use_https and 'https' or 'http',
            }
            subject = render_to_string(subject_template_name, context,
                                       request=request)
            subject = ''.join(subject.splitlines())
            email = render_to_string(email_template_name, context,
                                     request=request)
            send_mail(subject, email, from_email, [user.email])

class SetPasswordForm(BaseSetPasswordForm):
    '''A form that lets a user change set his/her password without entering
    the old password.
    '''
    '''
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }

    def __init__(self, user, *args, **kwargs):
        self.user = user
        self.session = orm.sessionmaker()
        super(SetPasswordForm, self).__init__(user, *args, **kwargs)

    def save(self, commit=True):
        user = getattr(self.user, 'auth', self.user)
        user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.session.commit()
        return self.user
    '''
    pass
class PasswordChangeForm(SetPasswordForm):
    error_messages = dict(SetPasswordForm.error_messages, **{
        'password_incorrect': _("Your old password was entered incorrectly. "
                                "Please enter it again."),
    })
    old_password = forms.CharField(label=_("Old password"),
                                   widget=forms.PasswordInput)

    def clean_old_password(self):
        """
        Validates that the old_password field is correct.
        """
        old_password = self.cleaned_data["old_password"]
        user = getattr(self.user, 'auth', self.user)
        if not user.check_password(old_password):
            raise forms.ValidationError(
                self.error_messages['password_incorrect'])
        return old_password

PasswordChangeForm.base_fields = OrderedDict([
    (k, PasswordChangeForm.base_fields[k])
    for k in ['old_password', 'new_password1', 'new_password2']
])

