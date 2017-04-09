# Copyright 2014 - 2017 The Abelujo Developers
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

from search.drfviews import CommandViewSet

from rest_framework.routers import DefaultRouter

js_info_dict = {
    'packages': ('search', '',),
}

urlpatterns = i18n_patterns("", url("^", include("search.urls")))

router = DefaultRouter()
router.register(r'commands', CommandViewSet)

apipatterns = patterns("",
    # pylint: disable=bad-continuation
    # Exclude /api/ from i18n so than we
    # don't bother of the language prefix in
    # js code.
    # XXX: the strings returned by the api (called from JS) are not translated. See issue #14.
    url(r'^api/datasource/search/', 'search.models.api.datasource_search', name="api_search_datasource"),

    # Meta info:
    url(r'^api/userinfo?$', 'search.models.api.get_user_info', name="api_user_info"),
    url(r'^api/preferences?$', 'search.models.api.preferences', name="api_preferences"),

    # Card
    url(r'^api/cards/create$', 'search.models.api.card_create', name="api_card_create"),
    url(r'^api/cards/?$', 'search.models.api.cards', name="api_cards"),
    url(r'^api/card/(?P<pk>\d+)/add/?$', 'search.models.api.card_add',
        name="api_card_add"),
    url(r'^api/card/(?P<pk>\d+)/reviews/?$', 'search.models.api.card_reviews',
        name="api_card_reviews"),
    url(r'^api/card/(?P<pk>\d+)', 'search.models.api.card', name="api_card"),
    url(r'^api/cardtype$', 'search.models.api.cardtype', name="api_cardtype"),

    url(r'^api/shelfs', 'search.models.api.shelfs', name="api_shelfs"),

    url(r'^api/authors$', 'search.models.api.authors', name="api_authors"),

    # Baskets
    url(r'^api/baskets/auto_command/open$', 'search.models.api.auto_command_total', name="api_auto_command_total"),
    url(r'^api/baskets/create', 'search.models.api.baskets_create', name="api_baskets_create"),
    url(r'^api/baskets/(?P<pk>\d+)/copies', 'search.models.api.basket', name="api_basket_copies"),
    url(r'^api/baskets/(?P<pk>\d+)/update/?', 'search.models.api.baskets_update', name="api_basket_update"),
    url(r'^api/baskets/(?P<pk>\d+)/delete/?', 'search.models.api.baskets_delete', name="api_basket_delete"),
    url(r'^api/baskets/?$', 'search.models.api.baskets', name="api_baskets"),
    # Inventories of baskets
    url(r'^api/baskets/(?P<pk>\d+)/inventories/?$',
        'search.models.api.baskets_inventory_get_or_create', name="api_baskets_inventories"),
    # Add or remove card(s)
    url(r'^api/baskets/(?P<pk>\d+)/(?P<action>[a-z_]+)/(?P<card_id>\d+)?/?', 'search.models.api.basket', name="api_basket_act"),  # action: add, remove, update
    # Simple info
    url(r'^api/baskets/(?P<pk>\d+)/?$', 'search.models.api.basket', name="api_basket"),

    url(r'^api/distributors', 'search.models.api.distributors', name="api_distributors"),
    url(r'^api/publishers/?$', 'search.models.api.publishers', name="api_publishers"),
    url(r'^api/deposits/due_dates/$', 'search.models.api.deposits_due_dates', name="api_deposits_due_dates"),
    url(r'^api/deposits/?$', 'search.models.api.deposits', name="api_deposits"),

    # Commands
    url(r'^api/commands/nb_ongoing', 'search.models.api.commands_ongoing', name="api_commands_ongoing"),
    url(r'^api/commands/create', 'search.models.api.commands_create', name="api_commands_create"),
    url(r'^api/commands/(?P<pk>\d+)/update/?$', 'search.models.api.commands_update', name="api_commands_update"),
    # from DRF's router:
    url(r'^api/', include(router.urls)),
    # A command inventory (receive a parcel)
    url(r'^api/commands/(?P<pk>\d+)/receive/?$', 'search.models.api.command_receive', name="api_command_receive"),
    url(r'^api/commands/(?P<pk>\d+)/receive/remove/?$', 'search.models.api.command_receive_remove', name="api_command_receive_remove"),
    url(r'^api/commands/(?P<pk>\d+)/receive/update/?$', 'search.models.api.command_receive_update', name="api_command_receive_update"),
    url(r'^api/commands/(?P<pk>\d+)/receive/diff/?$', 'search.models.api.command_receive_diff', name="api_command_receive_diff"),
    url(r'^api/commands/(?P<pk>\d+)/receive/apply/?$', 'search.models.api.command_receive_apply', name="api_command_receive_apply"),


    # Sell
    url(r'^api/sell/(?P<pk>\d+)/undo$', 'search.models.api.sell_undo', name="api_sell_undo"),
    url(r'^api/sell$', 'search.models.api.sell', name="api_sell"),

    # Sells history
    url(r'^api/history/sells/?$', 'search.models.api.history_sells', name="api_history_sells"),
    url(r'^api/history/entries/?$', 'search.models.api.history_entries', name="api_history_entries"),
    url(r'^api/alerts$', 'search.models.api.alerts', name="api_alerts"),
    url(r'^api/alerts/open$', 'search.models.api.alerts_open', name="api_alerts_open"),
    url(r'^api/places/?$', 'search.models.api.places', name="api_places"),

    # Inventories
    url(r'^api/inventories/create/?$', 'search.models.api.inventories', name="api_inventories"),
    url(r'^api/inventories/(?P<pk>\d+)/update/', 'search.models.api.inventories_update', name="api_inventories_update"),
    url(r'^api/inventories/(?P<pk>\d+)/remove/', 'search.models.api.inventories_remove', name="api_inventories_remove"),
    url(r'^api/inventories/(?P<pk>\d+)/diff/', 'search.models.api.inventory_diff', name="api_inventories_diff"),
    url(r'^api/inventories/(?P<pk>\d+)/apply/?', 'search.models.api.inventory_apply', name="api_inventories_apply"),
    url(r'^api/inventories/(?P<pk>\d+)/?$', 'search.models.api.inventories', name="api_inventories"),
    url(r'^api/inventories/?', 'search.models.api.inventories', name="api_inventories"),

    # Stats
    url(r'^api/stats/sells/month', 'search.models.api.stats_sells_month', name='api_stats_sells_month'),
    url(r'^api/stats/entries/month', 'search.models.api.stats_entries_month', name='api_stats_entries_month'),
    url(r'^api/stats/static', 'search.models.api.stats_static', name='api_stats_static'),
    url(r'^api/stats/stock_age/?', 'search.models.api.stats_stock_age', name='api_stats_stock_age'),
    url(r'^api/stats/', 'search.models.api.stats', name='api_stats'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)  # pylint: disable=bad-continuation

urlpatterns += apipatterns

# Authentication
urlpatterns += [
    url("^login/", "django.contrib.auth.views.login",
        {"template_name": "registration/login.jade"},
        name="login"),
    url("^logout/", "django.contrib.auth.views.logout",
        {"template_name": "registration/logout.jade", },
        name="logout"),
]

# the following does include a login/ too, but the first one will match.
urlpatterns += [url('^', include('django.contrib.auth.urls'))]
