# Copyright 2014 The Abelujo Developers
# See the COPYRIGHT file at the top-level directory of this distribution

# Abelujo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.
from django.conf.urls import include
from django.conf.urls import patterns
from django.conf.urls import url
from django.contrib import admin
from django.views.generic.base import RedirectView

from search.views import depositsListView

#TODO: move to the right app
urlpatterns = patterns('',
                       url(r'^$', RedirectView.as_view(url='search/')),
                       url(r'^search/$', 'search.views.index', name="card_index"),
                       url(r'^search$', 'search.views.search', name="card_search"),
                       url(r'^search', 'search.views.search'),
                       url(r'^add/', 'search.views.add', name="card_add"),
                       # url(r'^collection/sell', 'search.views.sell',
                           # name="card_sell"),
                       url(r'^sell', 'search.views.sell',
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
                       url(r'^commands/', 'search.views.basket_auto_command',
                           name="basket_auto_command"),

                       url(r'^api/cards$', 'search.models.api.cards', name="api_cards"),
                       url(r'^api/distributors$', 'search.models.api.distributors', name="api_distributors"),
                       url(r'^api/deposits$', 'search.models.api.deposits', name="api_deposits"),
                       url(r'^api/sell$', 'search.models.api.sell', name="api_sell"),

    # Examples:
    # url(r'^$', 'abelujo.views.home', name='home'),
    # url(r'^abelujo/', include('abelujo.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
