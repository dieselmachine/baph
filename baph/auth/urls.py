from coffin.conf.urls import patterns, url

urlpatterns = patterns('baph.auth.views',
    url(r'^login/$', 'login', {'SSL': True}, name='login'),
    url(r'^logout/$', 'logout', {'next_page': '/'}, name='logout'),
    (r'^password_reset/$', 'password_reset'),
    (r'^password_reset/done/$', 'password_reset_done'),
    (r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
     'password_reset_confirm', {'SSL': True}),
    (r'^reset/done/$', 'password_reset_complete'),
)
