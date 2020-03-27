# Copyright 2014 - 2020 The Abelujo Developers
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
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.conf.urls import url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib import auth

from search.models import api
from search.models import api_users

js_info_dict = {
    'packages': ('search', '',),
}

urlpatterns = i18n_patterns(url("^", include("search.urls", namespace=None)))

apipatterns = [
    # pylint: disable=bad-continuation
    # Exclude /api/ from i18n so than we
    # don't bother of the language prefix in
    # js code.
    # XXX: the strings returned by the api (called from JS) are not translated. See issue #14.
    url(r'^api/datasource/search/', api.datasource_search, name="api_search_datasource"),

    # Meta info:
    url(r'^api/userinfo?$', api.get_user_info, name="api_user_info"),
    url(r'^api/preferences?$', api.preferences, name="api_preferences"),

    # Card
    url(r'^api/cards/create/?$', api.card_create, name="api_card_create"),
    url(r'^api/cards/?$', api.cards, name="api_cards"),
    url(r'^api/card/(?P<pk>\d+)/add/?$', api.card_add,
        name="api_card_add"),
    url(r'^api/card/(?P<pk>\d+)/reviews/?$', api.card_reviews,
        name="api_card_reviews"),
    url(r'^api/card/(?P<pk>\d+)', api.card, name="api_card"),
    url(r'^api/cardtype$', api.cardtype, name="api_cardtype"),
    # Bulk manipulation.
    url(r'^api/cards/set_supplier$', api.cards_set_supplier, name="api_cards_set_supplier"),

    # Shelves
    url(r'^api/shelfs', api.shelfs, name="api_shelfs"),

    # Authors
    url(r'^api/authors$', api.authors, name="api_authors"),

    # Baskets
    url(r'^api/baskets/auto_command/open$', api.auto_command_total, name="api_auto_command_total"),
    url(r'^api/baskets/create', api.baskets_create, name="api_baskets_create"),
    url(r'^api/baskets/(?P<pk>\d+)/copies', api.basket, name="api_basket_copies"),
    url(r'^api/baskets/(?P<pk>\d+)/update/?', api.baskets_update, name="api_basket_update"),
    url(r'^api/v2/baskets/(?P<pk>\d+)/add/?', api.baskets_add_card, name="api_basket_add_card"),
    url(r'^api/baskets/(?P<pk>\d+)/return/?', api.baskets_return, name="api_basket_return"),
    url(r'^api/baskets/(?P<pk>\d+)/add_to_shelf/?', api.baskets_add_to_shelf, name="api_basket_add_to_shelf"),
    url(r'^api/baskets/(?P<pk>\d+)/archive/?', api.baskets_archive, name="api_basket_archive"),
    url(r'^api/baskets/(?P<pk>\d+)/delete/?', api.baskets_delete, name="api_basket_delete"),
    url(r'^api/baskets/?$', api.baskets, name="api_baskets"),
    # Inventories of baskets
    url(r'^api/baskets/(?P<pk>\d+)/inventories/?$',
        api.baskets_inventory_get_or_create, name="api_baskets_inventories"),
    # Add or remove card(s)
    url(r'^api/baskets/(?P<pk>\d+)/(?P<action>[a-z_]+)/(?P<card_id>\d+)?/?', api.basket, name="api_basket_act"),  # action: add, remove, update
    # Simple info
    url(r'^api/baskets/(?P<pk>\d+)/?$', api.basket, name="api_basket"),

    url(r'^api/distributors/(?P<pk>\d+)/?$', api.get_distributor, name="api_get_distributor"),
    url(r'^api/distributors', api.distributors, name="api_distributors"),
    url(r'^api/publishers/?$', api.publishers, name="api_publishers"),
    url(r'^api/deposits/?$', api.deposits, name="api_deposits"),

    # Commands
    url(r'^api/commands/ongoing/?$', api.commands_ongoing, name="api_commands_ongoing"),
    url(r'^api/commands/ongoing', api.commands_ongoing, name="api_commands_ongoing"),
    url(r'^api/commands/nb_ongoing/?$', api.nb_commands_ongoing, name="api_commands_nb_ongoing"),
    url(r'^api/commands/create', api.commands_create, name="api_commands_create"),
    url(r'^api/commands/(?P<pk>\d+)/update/?$', api.commands_update, name="api_commands_update"),
    url(r'^api/commands/supplier/(?P<pk>\d+)/copies/?$', api.commands_supplier, name="api_commands_supplier"),
    # A command inventory (receive a parcel)
    url(r'^api/commands/(?P<pk>\d+)/receive/?$', api.command_receive, name="api_command_receive"),
    url(r'^api/commands/(?P<pk>\d+)/receive/remove/?$', api.command_receive_remove, name="api_command_receive_remove"),
    url(r'^api/commands/(?P<pk>\d+)/receive/update/?$', api.command_receive_update, name="api_command_receive_update"),
    url(r'^api/commands/(?P<pk>\d+)/receive/diff/?$', api.command_receive_diff, name="api_command_receive_diff"),
    url(r'^api/commands/(?P<pk>\d+)/receive/apply/?$', api.command_receive_apply, name="api_command_receive_apply"),


    # Sell
    url(r'^api/sell/(?P<pk>\d+)/undo$', api.sell_undo, name="api_sell_undo"),
    url(r'^api/sell$', api.sell, name="api_sell"),

    # Restocking
    url(r'^api/restocking/nb_ongoing/?$', api.nb_restocking_ongoing, name="api_restocking_nb_ongoing"),
    url(r'^api/restocking/validate/?$', api.restocking_validate, name="api_restocking_validate"),
    url(r'^api/restocking/remove/(?P<pk>\d+)', api.restocking_remove, name="api_restocking_remove"),

    # Sells history
    url(r'^api/history/sells/?$', api.history_sells, name="api_history_sells"),
    url(r'^api/history/entries/?$', api.history_entries, name="api_history_entries"),
    url(r'^api/alerts$', api.alerts, name="api_alerts"),
    url(r'^api/alerts/open$', api.alerts_open, name="api_alerts_open"),
    url(r'^api/places/?$', api.places, name="api_places"),

    # Inventories
    url(r'^api/inventories/create/?$', api.inventories, name="api_inventories"),
    url(r'^api/inventories/(?P<pk>\d+)/update/', api.inventories_update, name="api_inventories_update"),
    url(r'^api/inventories/(?P<pk>\d+)/remove/', api.inventories_remove, name="api_inventories_remove"),
    url(r'^api/inventories/(?P<pk>\d+)/diff/', api.inventory_diff, name="api_inventories_diff"),
    url(r'^api/inventories/(?P<pk>\d+)/apply/?', api.inventory_apply, name="api_inventories_apply"),
    url(r'^api/inventories/(?P<pk>\d+)/copies/?', api.inventories_copies, name="api_inventories_copies"),
    url(r'^api/inventories/(?P<pk>\d+)/?$', api.inventories, name="api_inventories"),
    url(r'^api/inventories/?', api.inventories, name="api_inventories"),

    # Stats
    url(r'^api/stats/sells/month', api.stats_sells_month, name='api_stats_sells_month'),
    url(r'^api/stats/', api.stats, name='api_stats'),

    # Clients
    url(r'^api/clients/?', api_users.clients, name='api_clients'),

    # Bills
    url(r'^api/bill/?', api_users.bill, name='api_bill'),


    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
]  # pylint: disable=bad-continuation

urlpatterns += apipatterns
# urlpatterns = apipatterns

from django.contrib.auth import views as auth_views

# Authentication
urlpatterns += [
    url(
        '^login/?$',
        auth_views.LoginView.as_view(
            template_name='registration/login.pug'),
    ),
    url(
        '^logout/?$',
        auth_views.LogoutView.as_view(
            template_name='registration/logout.pug'),
    ),
]

# the following does include a login/ too, but the first one will match.
urlpatterns += [url('^', include('django.contrib.auth.urls'))]

# Serve media (images).
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
