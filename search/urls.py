# Copyright 2014 - 2020 The Abelujo Developers
# See the COPYRIGHT file at the top-level directory of this distribution

# Abelujo is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import unicode_literals

from django.conf.urls import include
from django.conf.urls import patterns
from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
# from django.views.generic.base import RedirectView
from search import views
from search.admin import admin_site

js_info_dict = {'packages': ('search', '',), }

# i18n_patterns is taken care of in the root url conf.
urlpatterns = patterns('',
    #pylint: disable=bad-continuation
    # Access to the translations in javascript code:
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict,),
    # Django Rest Framework browsable api
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # url(r'^$', RedirectView.as_view(url='search/')),
    url(r'^$', 'search.views.dashboard', name="dashboard"),
    url(r'^database/?', admin_site.urls),

    url(r'^preferences/bookshop/?$', 'search.views.preferences_bookshop', name="preferences_bookshop"),
    url(r'^preferences/?$', 'search.views.preferences', name="preferences"),

    url(r'^search/?$', 'search.views.search', name="card_search"),

    url(r'^stats/', 'search.views.dashboard', name="stats"),

    # view exported files:
    url(r'^stock/exports/download/(?P<filename>.+)', 'search.views.collection_view_file_export', name="collection_view_file_export"),
    url(r'^stock/exports/?', 'search.views.collection_exports', name="collection_exports"),
    url(r'^stock/export', 'search.views.collection_export', name="collection_export"),

    url(r'^stock/card/(?P<pk>\d+)/?$', 'search.views.card_show',
        name="card_show"),
    # works to edit a card with /edit/\d+. JS will fetch the existing info.
    # url(r'^stock/card/edit/', login_required(TemplateView.as_view(template_name="search/card_edit.jade")),

    url(r'^stock/card/create/(?P<pk>\d+)',
        login_required(TemplateView.as_view(template_name="search/card_add.jade")),
        name="card_create"),
    url(r'^stock/card/create/?', 'search.views.card_create_manually', name='card_create_manually'),
    # Add exemplaries to Places, from the Card view.
    url(r'^stock/card/add/(?P<pk>\d+)', 'search.views.card_places_add',
        name="card_places_add"),
    url(r'^stock/card/edit/(?P<pk>\d+)?',
        login_required(TemplateView.as_view(template_name="search/card_edit.jade")),
        name="card_edit"),
    url(r'^stock/card/(?P<pk>\d+)/move', 'search.views.card_move',
        name="card_move"),
    url(r'^stock/card/(?P<pk>\d+)/history', 'search.views.card_history',
        name="card_history"),
    url(r'^stock/card/(?P<pk>\d+)/buy', 'search.views.card_buy',
        name="card_buy"),
    url(r'^stock/set_supplier/', 'search.views.cards_set_supplier',
        name="cards_set_supplier"),

    url(r'^sell/$', 'search.views.sell',
        name="card_sell"),
    url(r'^sell/(?P<pk>\d+)', 'search.views.sell_details',
        name="sell_details"),

    url(r'^restocking/$', 'search.views.restocking',
        name="card_restocking"),

    url(r'^collection/', 'search.views.collection',
        name="card_collection"),

    url(r'^deposits/$', 'search.views.deposits', name="deposits"),
    url(r'^deposits/addcard', "search.views.deposits_add_card",
        name="deposits_add_card"),
    url(r'^deposits/new', 'search.views.deposits_new',
        name="deposits_new"),
    url(r'^deposits/create', 'search.views.deposits_create',
        name="deposits_create"),
    url(r'^deposits/(?P<pk>\d+)/checkout', 'search.views.deposits_checkout',
        name="deposit_checkout"),
    url(r'^deposits/(\d+)/?$', 'search.views.deposits_view',
        name="deposits_view"),
    # url(r'^deposits/(?P<pk>\d+)/delete', 'search.views.deposit_delete',
    # name="deposit_delete"),
    url(r'^deposits/(?P<pk>\d+)/add', 'search.views.deposit_add_copies',
        name="deposit_add_copies"),

    # Commands:
    url(r'^commands/ongoing/?',
            login_required(TemplateView.as_view(template_name="search/commands_ongoing.jade"))),
    url(r'^commands/(?P<pk>\d+)/receive/terminate/export/?$', views.command_receive_export, name="commands_receive_export"),
    url(r'^commands/(?P<pk>\d+)/receive/terminate/?$', views.command_receive_terminate, name="commands_receive_terminate"),
    url(r'^commands/(?P<pk>\d+)/receive?$', views.command_receive, name="commands_receive"),
    url(r'^commands/(?P<pk>\d+)/?$', login_required(views.CommandDetailView.as_view()), name="commands_view"),
    url(r'^commands/supplier/(?P<pk>\d+)/?$', 'search.views.command_supplier',
        name="command_supplier"),
    url(r'^commands/?$', 'search.views.basket_auto_command',
        name="basket_auto_command"),

    url(r'^command/(?P<pk>\d+)/?', login_required(views.command_card)),

    # Baskets:
    url(r'^baskets/(?P<pk>\d+)/export/$', 'search.views.basket_export', name="basket_export"),
    url(r'^baskets/(?P<pk>\d+)/receive/$',
        login_required(TemplateView.as_view(template_name="search/inventory_view.jade"))),
    url(r'^baskets/$', 'search.views.baskets',
        name="baskets"),
    # Endpoints for vue, to replace the previous ones.
    # Simple presentation:
    url(r'^lists/?$', 'search.views.basket_list', name="basket_list"),
    # Vue app
    url(r'^lists/(?P<pk>\d+)/?$', login_required(views.basket_view), name="basket_view"),

    # Sells history
    url(r'^history/sells/month/(?P<date>.*)/export/?', 'search.views.history_sells_month_export', name="history_sells_month_export"),
    url(r'^history/sells/month/(?P<date>.*)/?', 'search.views.history_sells_month', name="history_sells_month"),
    url(r'^history/sells/day/(?P<date>.*)/?', 'search.views.history_sells_day', name="history_sells_day"),
    url(r'^history/sells/export/?', 'search.views.history_sells_exports',
        name="history_sells_exports"),

    # Entries history
    url(r'^history/entries/month/(?P<date>.*)/?', 'search.views.history_entries_month', name="history_entries_month"),
    url(r'^history/entries/day/(?P<date>.*)/?', 'search.views.history_entries_day', name="history_entries_day"),

    url(r'^history/?', 'search.views.history_sells', name="history_sells"),
    # url(r'^history/', login_required(TemplateView.as_view(template_name="search/history.jade")),
    # name="search_history"),

    # Suppliers: sells of suppliers by month.
    url(r'^suppliers/sells/month/(?P<date>.*)/?', 'search.views.suppliers_sells_month', name="suppliers_sells_month"),
    url(r'^publishers/(?P<pk>\d+)/sells/month/(?P<date>.*)/?', 'search.views.publisher_sells_month_list', name="publisher_sells_month_list"),
    url(r'^distributors/(?P<pk>\d+)/sells/month/(?P<date>.*)/?', 'search.views.distributors_sells_month_list', name="distributors_sells_month_list"),
    url(r'^suppliers/?', 'search.views.suppliers_sells', name="suppliers_sells"),

    url(r'^alerts/', login_required(TemplateView.as_view(template_name="search/alerts.jade")),
        name="search_alerts"),

    url(r'^inventories/$', 'search.views.inventories',
        name="inventories"),
    url(r'^inventories/new$', login_required(TemplateView.as_view(template_name="search/inventory_view.jade")),
        name="inventory_new"),
    url(r'^inventories/(?P<pk>\d+)/?$', 'search.views.inventory',
        name="inventory_view"),
    url(r'^inventories/(?P<pk>\d+)/archive', 'search.views.inventory_archive',
        name="inventory_archive"),
    url(r'^inventories/(?P<pk>\d+)/delete', 'search.views.inventory_delete',
        name="inventory_delete"),
    url(r'^inventories/(?P<pk>\d+)/terminate', 'search.views.inventory_terminate',
        name="inventory_terminate"),
    url(r'^inventories/(?P<pk>\d+)/export', 'search.views.inventory_export',
        name="inventory_export"),
)
