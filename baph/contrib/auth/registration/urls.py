try:
    from django.conf.urls import *
except:
    from django.conf.urls import *
    
from django.contrib.auth import views as auth_views

from baph.contrib.auth.registration import settings


urlpatterns = patterns('',
    # Signup, signin and signout
    url(r'^signup/$',
        'baph.contrib.auth.registration.views.signup',
        name='baph_signup'),
    url(r'^signin/$',
        'baph.contrib.auth.registration.views.signin',
       name='baph_signin'),
    url(r'^signout/$',
       'baph.contrib.auth.registration.views.signout',
       name='baph_signout'),
    url(r'^signup/complete/$',
       'baph.contrib.auth.registration.views.signup_complete',
       {'template_name': 'registration/signup_complete.html',
        'extra_context': {'baph_activation_required': settings.BAPH_ACTIVATION_REQUIRED,
                          'baph_activation_days': settings.BAPH_ACTIVATION_DAYS}},
       name='baph_signup_complete'),

    # Activate
    url(r'^activate/(?P<activation_key>\w+)/$',
       'baph.contrib.auth.registration.views.activate',
       name='baph_activate'),
    url(r'^activate/retry/(?P<activation_key>\w+)/$',
        'baph.contrib.auth.registration.views.activate_retry',
        name='baph_activate_retry'),

    # Change password
    url(r'^password/$',
       'baph.contrib.auth.registration.views.password_change',
       name='baph_password_change'),
    url(r'^password/complete/$',
       'baph.contrib.auth.registration.views.direct_to_template',
       {'template_name': 'registration/password_complete.html'},
       name='baph_password_change_complete'),

    # Password reset
    url(r'^password/reset/$',
       'baph.contrib.auth.views.password_reset',
       {'template_name': 'registration/password_reset_form.html',
        'email_template_name': 'registration/emails/password_reset_message.txt'},
       name='baph_password_reset'),
    url(r'^password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
       'baph.contrib.auth.views.password_reset_confirm',
       {'template_name': 'registration/password_reset_confirm_form.html',
        'post_reset_redirect': 'baph_password_reset_complete',
       },
       name='baph_password_reset_confirm'),
    url(r'^password/reset/done/$',
       'baph.contrib.auth.views.password_reset_done',
       {'template_name': 'registration/password_reset_done.html'},
       name='baph_password_reset_done'),
    url(r'^password/reset/confirm/complete/$',
       'baph.contrib.auth.views.password_reset_complete',
       {'template_name': 'registration/password_reset_complete.html'},
        name='baph_password_reset_complete'),

    # Disabled account
    url(r'^disabled/$',
       'baph.contrib.auth.registration.views.direct_to_template',
       {'template_name': 'registration/disabled.html'},
       name='baph_disabled'),

    # Change email and confirm it
    url(r'^email/$',
       'baph.contrib.auth.registration.views.email_change',
       name='baph_email_change'),
    url(r'^confirm-email/complete/$',
       'baph.contrib.auth.registration.views.direct_to_template',
       {'template_name': 'registration/email_confirm_complete.html'},
       name='baph_email_confirm_complete'),
    url(r'^confirm-email/(?P<confirmation_key>\w+)/$',
       'baph.contrib.auth.registration.views.email_confirm',
       name='baph_email_confirm'),
    url(r'^email/complete/$',
       'baph.contrib.auth.registration.views.direct_to_user_template',
       {'template_name': 'registration/email_change_complete.html'},
       name='baph_email_change_complete'),


   )
