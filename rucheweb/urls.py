from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^search/$', 'search.views.index'),
                       url(r'^add/', 'search.views.add'),
                       # url(r'^search/', 'search.views.fire_query'),
    # Examples:
    # url(r'^$', 'rucheweb.views.home', name='home'),
    # url(r'^rucheweb/', include('rucheweb.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
