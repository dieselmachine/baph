from django.conf.urls import url, patterns
from django.contrib.auth import views


urlpatterns = patterns('baph.contrib.auth.views',
    (r'^login/$', 'login', {'SSL': True}),
    (r'^logout/$', 'logout'),
    #(r'^password_reset/$', 'password_reset'),
    #(r'^password_reset/done/$', 'password_reset_done'),
    #(r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
    # 'password_reset_confirm', {'SSL': True}),
    #(r'^reset/done/$', 'password_reset_complete'),
)
urlpatterns += [
    url(r'^password_change/$', views.password_change,
        name='password_change'),
    url(r'^password_change/done/$', views.password_change_done,
        name='password_change_done'),
    url(r'^password_reset/$', views.password_reset,
        name='password_reset'),
    url(r'^password_reset/done/$', views.password_reset_done,
        name='password_reset_done'),

    ]