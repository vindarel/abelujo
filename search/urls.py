# Copyright 2014 - 2016 The Abelujo Developers
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
from search.admin import admin_site

js_info_dict = { 'packages': ('search', '',), }

# i18n_patterns is taken care of in the root url conf.
urlpatterns = patterns('',
    # Access to the translations in javascript code:
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict,),

    # url(r'^$', RedirectView.as_view(url='search/')),
    url(r'^$', 'search.views.dashboard', name="dashboard"),
    url(r'^database/?', admin_site.urls),
    url(r'^search/?$', 'search.views.search', name="card_search"),

    url(r'^stats/', 'search.views.dashboard', name="stats"),

    url(r'^stock/card/(?P<pk>\d+)/?$', 'search.views.card_show',
        name="card_show"),
    # works to edit a card with /edit/\d+. JS will fetch the existing info.
    # url(r'^stock/card/edit/', login_required(TemplateView.as_view(template_name="search/card_edit.jade")),
    url(r'^stock/card/create/(?P<pk>\d+)',
        login_required(TemplateView.as_view(template_name="search/card_add.jade")),
        name="card_create"),
    url(r'^stock/card/edit/(?P<pk>\d+)?', login_required(TemplateView.as_view(template_name="search/card_edit.jade")),
        name="card_edit"),
    url(r'^stock/card/(?P<pk>\d+)/move', 'search.views.card_move',
        name="card_move"),
    url(r'^stock/card/(?P<pk>\d+)/buy', 'search.views.card_buy',
        name="card_buy"),

    url(r'^sell/$', 'search.views.sell',
        name="card_sell"),
    url(r'^sell/(?P<pk>\d+)', 'search.views.sell_details',
        name="sell_details"),

    url(r'^collection/', 'search.views.collection',
        name="card_collection"),

    url(r'^deposits/$', login_required(DepositsListView.as_view()),
        name="deposits"),
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

    url(r'^commands/', 'search.views.basket_auto_command',
        name="basket_auto_command"),

    url(r'^baskets/(?P<pk>\d+)/export/$', 'search.views.basket_export', name="basket_export"),
    url(r'^baskets/(?P<pk>\d+)/receive/$',
        login_required(TemplateView.as_view(template_name="search/inventory_view.jade"))),
    url(r'^baskets/$', 'search.views.baskets',
        name="baskets"),

    url(r'^history/', login_required(TemplateView.as_view(template_name="search/history.jade")),
        name="search_history"),

    url(r'^alerts/', login_required(TemplateView.as_view(template_name="search/alerts.jade")),
        name="search_alerts"),

    url(r'^history/entries/(?P<pk>\d+)', 'search.history_views.entry_details',
        name="history_entry"),

    url(r'^inventories/$', login_required(InventoriesListView.as_view()),
        name="inventories"),
    url(r'^inventories/new$', login_required(TemplateView.as_view(template_name="search/inventory_view.jade")),
        name="inventory_new"),
    url(r'^inventories/(?P<pk>\d+)/?$', 'search.views.inventories',
        name="inventory_view"),
    url(r'^inventories/(?P<pk>\d+)/delete', 'search.views.inventory_delete',
        name="inventory_delete"),
    url(r'^inventories/(?P<pk>\d+)/terminate', 'search.views.inventory_terminate',
        name="inventory_terminate"),
    url(r'^inventories/(?P<pk>\d+)/export', 'search.views.inventory_export',
        name="inventory_export"),
)
