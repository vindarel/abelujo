from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^$', RedirectView.as_view(url='search/')),
                       url(r'^search/$', 'search.views.index', name="card_index"),
                       url(r'^search$', 'search.views.search', name="card_search"),
                       url(r'^search', 'search.views.search'),
                       url(r'^add/', 'search.views.add', name="card_add"),
                       url(r'^collection/sell', 'search.views.sell', name="card_sell"),
                       url(r'^collection/', 'search.views.collection', name="card_collection"),
                       (r'^grappelli/', include('grappelli.urls')), # grappelli URLS

    # Examples:
    # url(r'^$', 'abelujo.views.home', name='home'),
    # url(r'^abelujo/', include('abelujo.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
