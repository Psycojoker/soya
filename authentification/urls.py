from django.conf.urls import patterns, url, include


urlpatterns = patterns('authentification.views',
    url(r'^login/', 'login', name='login'),
    url(r'^', include('django.contrib.auth.urls')),
)
