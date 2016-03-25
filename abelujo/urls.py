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
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from search.views import DepositsListView
from search.views import InventoriesListView

js_info_dict = { 'packages': ('search', '',), }

urlpatterns = i18n_patterns("",
    url("^", include("search.urls")),
)

apipatterns = patterns("",
    # Exclude /api/ from i18n so than we
    # don't bother of the language prefix in
    # js code.
    # XXX: the strings returned by the api (called from JS) are not translated. See issue #14.
    url(r'^api/datasource/search/', 'search.models.api.datasource_search', name="api_search_datasource"),

    url(r'^api/cards/create$', 'search.models.api.card_create', name="api_card_create"),
    url(r'^api/cards/?$', 'search.models.api.cards', name="api_cards"),
    url(r'^api/card/(?P<pk>\d+)/add/?$', 'search.models.api.card_add',
        name="api_card_add"),
    url(r'^api/card/(?P<pk>\d+)', 'search.models.api.card', name="api_card"),
    url(r'^api/cardtype$', 'search.models.api.cardtype', name="api_cardtype"),

    url(r'^api/categories', 'search.models.api.categories', name="api_categories"),

    url(r'^api/authors$', 'search.models.api.authors', name="api_authors"),

    url(r'^api/baskets/auto_command/open$', 'search.models.api.auto_command_total', name="api_auto_command_total"),
    url(r'^api/baskets/create', 'search.models.api.baskets_create', name="api_baskets_create"),
    url(r'^api/baskets/(?P<pk>\d+)/copies', 'search.models.api.baskets', name="api_basket_copies"),
    url(r'^api/baskets/?$', 'search.models.api.baskets', name="api_baskets"),
    # Inventories of baskets
    url(r'^api/baskets/(?P<pk>\d+)/inventories/?$',
        'search.models.api.baskets_inventory_get_or_create', name="api_baskets_inventories"),
    # Add or remove card(s)
    url(r'^api/baskets/(?P<pk>\d+)/(?P<action>[a-z]+)/(?P<card_id>\d+)?/?', 'search.models.api.basket', name="api_basket_act"), #action: add, remove
    # Simple info
    url(r'^api/baskets/(?P<pk>\d+)/?$', 'search.models.api.basket', name="api_basket"),

    url(r'^api/distributors', 'search.models.api.distributors', name="api_distributors"),
    url(r'^api/publishers/?$', 'search.models.api.publishers', name="api_publishers"),
    url(r'^api/deposits/due_dates/$', 'search.models.api.deposits_due_dates', name="api_deposits_due_dates"),
    url(r'^api/deposits/?$', 'search.models.api.deposits', name="api_deposits"),

    url(r'^api/sell/(?P<pk>\d+)/undo$', 'search.models.api.sell_undo', name="api_sell_undo"),
    url(r'^api/sell$', 'search.models.api.sell', name="api_sell"),

    url(r'^api/history$', 'search.models.api.history', name="api_history"),
    url(r'^api/alerts$', 'search.models.api.alerts', name="api_alerts"),
    url(r'^api/alerts/open$', 'search.models.api.alerts_open', name="api_alerts_open"),
    url(r'^api/places/?$', 'search.models.api.places', name="api_places"),
    url(r'^api/inventories/create/?$', 'search.models.api.inventories', name="api_inventories"),
    url(r'^api/inventories/(?P<pk>\d+)/update/', 'search.models.api.inventories_update', name="api_inventories_update"),
    url(r'^api/inventories/(?P<pk>\d+)/diff/', 'search.models.api.inventory_diff', name="api_inventories_diff"),
    url(r'^api/inventories/(?P<pk>\d+)/?$', 'search.models.api.inventories', name="api_inventories"),

    url(r'^api/stats/sells/month', 'search.models.api.stats_sells_month', name='api_stats_sells_month'),
    url(r'^api/stats/', 'search.models.api.stats', name='api_stats'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += apipatterns

# Authentication
urlpatterns += [
    url("^login/", "django.contrib.auth.views.login",
        {"template_name": "registration/login.jade"},
        name="login"),
    url("^logout/", "django.contrib.auth.views.logout",
        {"template_name": "registration/logout.jade",},
        name="logout"),
    ]

# the following does include a login/ too, but the first one will match.
urlpatterns += [ url('^', include('django.contrib.auth.urls'))]
