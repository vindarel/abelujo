# Copyright 2014 - 2019 The Abelujo Developers
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
from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.views import i18n
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import TemplateView
# from django.views.generic.base import RedirectView
from search import views
from search.admin import admin_site

js_info_dict = {'packages': ('search', '',), }

from django.views.i18n import JavaScriptCatalog

app_name = 'search'  # test

urlpatterns = [
    url(r'^jsi18n/$', JavaScriptCatalog.as_view(), name='javascript-catalog'),
]

# i18n_patterns is taken care of in the root url conf and in abelujo.urls.
urlpatterns += [
    #pylint: disable=bad-continuation
    # Access to the translations in javascript code:
    # url(r'^jsi18n/$', i18n.javascript_catalog, js_info_dict,),
    # Django Rest Framework browsable api
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # url(r'^$', RedirectView.as_view(url='search/')),
    url(r'^$', views.dashboard, name="dashboard"),
    url(r'^database/?', admin_site.urls),

    url(r'^preferences/?$', views.preferences, name="preferences"),

    url(r'^search/?$', views.search, name="card_search"),

    url(r'^stats/', views.dashboard, name="stats"),

    # view exported files:
    url(r'^stock/exports/download/(?P<filename>.+)', views.collection_view_file_export, name="collection_view_file_export"),
    url(r'^stock/exports/?', views.collection_exports, name="collection_exports"),
    url(r'^stock/export', views.collection_export, name="collection_export"),

    url(r'^stock/card/(?P<pk>\d+)/?$', views.card_show,
        name="card_show"),
    # works to edit a card with /edit/\d+. JS will fetch the existing info.
    # url(r'^stock/card/edit/', login_required(TemplateView.as_view(template_name="search/card_edit.jade")),
    url(r'^stock/card/create/(?P<pk>\d+)',
        login_required(TemplateView.as_view(template_name="search/card_add.jade")),
        name="card_create"),
    # Add exemplaries to Places, from the Card view.
    url(r'^stock/card/add/(?P<pk>\d+)', views.card_places_add,
        name="card_places_add"),
    url(r'^stock/card/edit/(?P<pk>\d+)?',
        login_required(TemplateView.as_view(template_name="search/card_edit.jade")),
        name="card_edit"),
    url(r'^stock/card/(?P<pk>\d+)/move', views.card_move,
        name="card_move"),
    url(r'^stock/card/(?P<pk>\d+)/history', views.card_history,
        name="card_history"),
    url(r'^stock/card/(?P<pk>\d+)/buy', views.card_buy,
        name="card_buy"),
    url(r'^stock/set_supplier/', views.cards_set_supplier,
        name="cards_set_supplier"),

    url(r'^sell/$', views.sell,
        name="card_sell"),
    url(r'^sell/(?P<pk>\d+)', views.sell_details,
        name="sell_details"),

    url(r'^restocking/$', views.restocking,
        name="card_restocking"),

    url(r'^collection/', views.collection,
        name="card_collection"),

    url(r'^deposits/$', login_required(views.DepositsListView.as_view()),
        name="deposits"),
    url(r'^deposits/addcard', views.deposits_add_card,
        name="deposits_add_card"),
    url(r'^deposits/new', views.deposits_new,
        name="deposits_new"),
    url(r'^deposits/create', views.deposits_create,
        name="deposits_create"),
    url(r'^deposits/(?P<pk>\d+)/checkout', views.deposits_checkout,
        name="deposit_checkout"),
    url(r'^deposits/(\d+)/?$', views.deposits_view,
        name="deposits_view"),
    # url(r'^deposits/(?P<pk>\d+)/delete', views.deposit_delete,
    # name="deposit_delete"),
    url(r'^deposits/(?P<pk>\d+)/add', views.deposit_add_copies,
        name="deposit_add_copies"),

    # Commands:
    url(r'^commands/ongoing/?',
            login_required(TemplateView.as_view(template_name="search/commands_ongoing.jade"))),
    url(r'^commands/(?P<pk>\d+)/receive/terminate/export/?$', views.command_receive_export, name="commands_receive_export"),
    url(r'^commands/(?P<pk>\d+)/receive/terminate/?$', views.command_receive_terminate, name="commands_receive_terminate"),
    url(r'^commands/(?P<pk>\d+)/receive?$', views.command_receive, name="commands_receive"),
    url(r'^commands/(?P<pk>\d+)/?$', login_required(views.CommandDetailView.as_view()), name="commands_view"),
    url(r'^commands/supplier/(?P<pk>\d+)/?$', views.command_supplier,
        name="command_supplier"),
    url(r'^commands/?$', views.basket_auto_command,
        name="basket_auto_command"),

    url(r'^command/(?P<pk>\d+)/?', login_required(views.command_card)),

    # Baskets:
    url(r'^baskets/(?P<pk>\d+)/export/$', views.basket_export, name="basket_export"),
    url(r'^baskets/(?P<pk>\d+)/receive/$',
        login_required(TemplateView.as_view(template_name="search/inventory_view.jade"))),
    url(r'^baskets/$', views.baskets,
        name="baskets"),
    # Endpoints for vue, to replace the previous ones.
    # Simple presentation:
    url(r'^lists/?$', views.basket_list, name="basket_list"),
    # Vue app
    url(r'^lists/(?P<pk>\d+)/?$', login_required(views.basket_view), name="basket_view"),

    # Sells history
    url(r'^history/sells/month/(?P<date>.*)/?', views.history_sells_month, name="history_sells_month"),
    url(r'^history/sells/day/(?P<date>.*)/?', views.history_sells_day, name="history_sells_day"),
    url(r'^history/sells/export/?', views.history_sells_exports,
        name="history_sells_exports"),

    # Entries history
    url(r'^history/entries/month/(?P<date>.*)/?', views.history_entries_month, name="history_entries_month"),
    url(r'^history/entries/day/(?P<date>.*)/?', views.history_entries_day, name="history_entries_day"),

    url(r'^history/?', views.history_sells, name="history_sells"),
    # url(r'^history/', login_required(TemplateView.as_view(template_name="search/history.jade")),
    # name="search_history"),

    # Suppliers: sells of suppliers by month.
    url(r'^suppliers/sells/month/(?P<date>.*)/?', views.suppliers_sells_month, name="suppliers_sells_month"),
    url(r'^publishers/(?P<pk>\d+)/sells/month/(?P<date>.*)/?', views.publisher_sells_month_list, name="publisher_sells_month_list"),
    url(r'^distributors/(?P<pk>\d+)/sells/month/(?P<date>.*)/?', views.distributors_sells_month_list, name="distributors_sells_month_list"),
    url(r'^suppliers/?', views.suppliers_sells, name="suppliers_sells"),

    url(r'^alerts/', login_required(TemplateView.as_view(template_name="search/alerts.jade")),
        name="search_alerts"),

    url(r'^inventories/$', views.inventories,
        name="inventories"),
    url(r'^inventories/new$', login_required(TemplateView.as_view(template_name="search/inventory_view.jade")),
        name="inventory_new"),
    url(r'^inventories/(?P<pk>\d+)/?$', views.inventory,
        name="inventory_view"),
    url(r'^inventories/(?P<pk>\d+)/archive', views.inventory_archive,
        name="inventory_archive"),
    url(r'^inventories/(?P<pk>\d+)/delete', views.inventory_delete,
        name="inventory_delete"),
    url(r'^inventories/(?P<pk>\d+)/terminate', views.inventory_terminate,
        name="inventory_terminate"),
    url(r'^inventories/(?P<pk>\d+)/export', views.inventory_export,
        name="inventory_export"),
]
