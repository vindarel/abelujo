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
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls import url
from django.contrib import admin
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from search.views import DepositsListView
from search.views import InventoriesListView

js_info_dict = { 'packages': ('search', '',), }

#XXX: include the url patterns from the app.
urlpatterns = i18n_patterns('',
    # Access to the translations in javascript code:
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict,),

    url(r'^$', RedirectView.as_view(url='search/')),
    url(r'^search/$', 'search.views.index', name="card_index"),
    url(r'^search$', 'search.views.search', name="card_search"),
    url(r'^search', 'search.views.search'),
    url(r'^stock/card/(?P<pk>\d+)/$', 'search.views.card_show',
        name="card_show"),
    url(r'^stock/card/create/$', TemplateView.as_view(template_name="search/card_create.jade"),
        name="card_create"),
    url(r'^stock/card/(?P<pk>\d+)/move', 'search.views.card_move',
        name="card_move"),
    url(r'^add/', 'search.views.add', name="card_add"),

    url(r'^sell$', 'search.views.sell',
        name="card_sell"),
    url(r'^sell/(?P<pk>\d+)', 'search.views.sell_details',
        name="sell_details"),

    url(r'^collection/', 'search.views.collection',
        name="card_collection"),

    url(r'^deposits/$', DepositsListView.as_view(),
        name="deposits"),
    url(r'^deposits/addcard', "search.views.deposits_add_card",
        name="deposits_add_card"),
    url(r'^deposits/new', 'search.views.deposits_new',
        name="deposits_new"),
    url(r'^deposits/create', 'search.views.deposits_create',
        name="deposits_create"),
    url(r'^deposits/(?P<pk>\d+)/checkout', 'search.views.deposits_checkout',
        name="deposit_checkout"),
    url(r'^deposits/(\d)', 'search.views.deposits_view',
        name="deposits_view"),

    url(r'^commands/', 'search.views.basket_auto_command',
        name="basket_auto_command"),

    url(r'^history/', TemplateView.as_view(template_name="search/history.jade"),
        name="search_history"),

    url(r'^alerts/', TemplateView.as_view(template_name="search/alerts.jade"),
        name="search_alerts"),

    url(r'^inventories/$', InventoriesListView.as_view(),
        name="inventories"),
    url(r'^inventories/new$', TemplateView.as_view(template_name="search/inventory_new.jade"),
        name="inventory_new"),

                    )

urlpatterns += patterns("",
    # Exclude /api/ from i18n so than we
    # don't bother of the language prefix in
    # js code.
    # XXX: the strings returned by the api (called from JS) are not translated. See issue #14.

    url(r'^api/baskets/auto_command/open$', 'search.models.api.auto_command_total', name="api_auto_command_total"),
    url(r'^api/cards/create$', 'search.models.api.card_create', name="api_card_create"),
    url(r'^api/cards$', 'search.models.api.cards', name="api_cards"),
    url(r'^api/cardtype$', 'search.models.api.cardtype', name="api_cardtype"),
    url(r'^api/authors$', 'search.models.api.authors', name="api_authors"),
    url(r'^api/distributors$', 'search.models.api.distributors', name="api_distributors"),
    url(r'^api/publishers$', 'search.models.api.publishers', name="api_publishers"),
    url(r'^api/deposits$', 'search.models.api.deposits', name="api_deposits"),
    url(r'^api/sell$', 'search.models.api.sell', name="api_sell"),
    url(r'^api/history$', 'search.models.api.history', name="api_history"),
    url(r'^api/alerts$', 'search.models.api.alerts', name="api_alerts"),
    url(r'^api/alerts/open$', 'search.models.api.alerts_open', name="api_alerts_open"),
    url(r'^api/places$', 'search.models.api.places', name="api_places"),
    # url(r'^api/inventory$', 'search.models.api.inventory', name="api_alerts_open"),

    # Examples:
    # url(r'^$', 'abelujo.views.home', name='home'),
    # url(r'^abelujo/', include('abelujo.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
