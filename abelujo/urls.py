from django.conf.urls import include
from django.conf.urls import patterns
from django.conf.urls import url
from django.contrib import admin
from django.views.generic.base import RedirectView

import autocomplete_light
from search.views import depositsListView

autocomplete_light.autodiscover()  # before importing the admin.

admin.autodiscover()

#TODO: move to the right app
urlpatterns = patterns('',
                       url(r'^autocomplete/', include('autocomplete_light.urls')),
                       url(r'^$', RedirectView.as_view(url='search/')),
                       url(r'^search/$', 'search.views.index', name="card_index"),
                       url(r'^search$', 'search.views.search', name="card_search"),
                       url(r'^search', 'search.views.search'),
                       url(r'^add/', 'search.views.add', name="card_add"),
                       url(r'^collection/sell', 'search.views.sell',
                           name="card_sell"),
                       url(r'^collection/', 'search.views.collection',
                           name="card_collection"),
                       url(r'^deposits/$', depositsListView.as_view(),
                           name="deposits"),
                       url(r'^deposits/addcard', "search.views.deposits_add_card",
                           name="deposits_add_card"),
                       url(r'^deposits/new', 'search.views.deposits_new',
                           name="deposits_new"),
                       url(r'^deposits/create', 'search.views.deposits_create',
                           name="deposits_create"),
                       url(r'^deposits/(.+)', 'search.views.deposits_view',
                           name="deposits_view"),

    # Examples:
    # url(r'^$', 'abelujo.views.home', name='home'),
    # url(r'^abelujo/', include('abelujo.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
