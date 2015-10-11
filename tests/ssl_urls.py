from django.conf.urls import patterns

urlpatterns = patterns('test_ssl',
    (r'^secure/$', 'secure_view', {'SSL': True}),
)
