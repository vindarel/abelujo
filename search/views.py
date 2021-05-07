# -*- coding: utf-8 -*-
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

import datetime
import io  # write to file in utf8
import json
import os
import time
import traceback
import urllib

import pendulum
import toolz
import unicodecsv
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.template.loader import get_template
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.views.generic import DetailView
from weasyprint import HTML

from abelujo import settings
from search import forms as viewforms
#
# The datasources imports must have the name as their self.SOURCE_NAME
# Also add the search engine in the client side controller (searchResultsController).
#
from search.datasources.bookshops.all.discogs import discogsScraper as discogs  # noqa: F401
from search.datasources.bookshops.all.momox import momox  # noqa: F401
from search.datasources.bookshops.deDE.buchlentner import buchlentnerScraper as buchlentner  # noqa: F401
from search.datasources.bookshops.esES.casadellibro import casadellibroScraper as casadellibro  # noqa: F401
from search.datasources.bookshops.frFR.lelivre import lelivreScraper as lelivre  # noqa: F401
from search.datasources.bookshops.frFR.librairiedeparis import librairiedeparisScraper as librairiedeparis  # noqa: F401
from search.datasources.bookshops.frFR.filigranes import filigranesScraper as filigranes  # noqa: F401

from search import models
from search.models import Barcode64
from search.models import Basket
from search.models import Bill
from search.models import Card
from search.models import Client
from search.models import Command
from search.models import Deposit
from search.models import Distributor
from search.models import Entry
from search.models import EntryCopies
from search.models import Inventory
from search.models import InventoryCommand
from search.models import Place
from search.models import Preferences
from search.models import Publisher
from search.models import Restocking
from search.models import Sell
from search.models import Shelf
from search.models import Stats
from search.models import history
from search.models import users
from search.models.api import _get_command_or_return
from search.models.common import get_payment_abbr
from search.models.utils import _is_truthy
from search.models.utils import get_logger
from search.models.utils import is_isbn
from search.models.utils import ppcard
from search.models.utils import price_fmt
from search.models.utils import truncate
from views_utils import Echo
from views_utils import cards2csv
from views_utils import dilicom_enabled
from views_utils import update_from_dilicom

log = get_logger()

DEFAULT_NB_COPIES = 1         # default nb of copies to add.

PENDULUM_YMD = '%Y-%m-%d'  # caution, %m is a bit different than datetime's %M.

EXTENSION_TO_CONTENT_TYPE = {
    'csv': 'text/csv',
    'txt': 'text/raw',
    'pdf': 'application/pdf',
}

def filename_content_type(filename):
    extension = filename.split('.')[-1]
    return EXTENSION_TO_CONTENT_TYPE[extension]


def get_reverse_url(cleaned_data, url_name="card_search"):
    """Get the reverse url with the query parameters taken from the
    form's cleaned data.

    query parameters:
    - source
    - q

    type cleaned_data: dict
    return: the complete url with query params

    >>> get_reverse_url({"source": "chapitre", "q": "emma goldman"})
    /search?q=emma+goldman&source=chapitre

    """

    qparam = {}
    qparam['source'] = cleaned_data.get("source")
    if "q" in list(cleaned_data.keys()):
        qparam['q'] = cleaned_data["q"]
    # construct the query parameters of the form
    # q=query+param&source=discogs
    params = urllib.urlencode(qparam)
    rev_url = reverse(url_name) + "?" + params
    return rev_url


@login_required
def preferences(request):
    """
    """
    template = "search/preferences.jade"
    if request.method == 'GET':
        form = viewforms.PrefsForm()
        bs_model = users.Bookshop.objects.first()
        # note: we handle its POST on preferences_bookshop url.
        if bs_model:
            bookshopform = viewforms.BookshopForm(instance=bs_model)
        else:
            bookshopform = viewforms.BookshopForm()

        return render(request, template, {
            'form': form,
            'bookshopform': bookshopform,
        })

    elif request.method == 'POST':
        bookshopform = viewforms.BookshopForm()  # we handle it on preferences_bookshop
        form = viewforms.PrefsForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            prefs = Preferences.prefs()
            discounts = viewforms.validate_and_get_discounts(data['sell_discounts'])
            data['sell_discounts'] = discounts
            prefs.others = json.dumps(data)
            prefs.auto_command_after_sell = data['auto_command_after_sell']
            prefs.save()
            messages.add_message(
                request, messages.SUCCESS, _("Preferences saved."))
            form = viewforms.PrefsForm()
            return HttpResponseRedirect(reverse('preferences'))

        return render(request, template, {
            'form': form,
            'bookshopform': bookshopform,
        })

def preferences_bookshop(request):
    # If we POST to preferences/, the currency&discount form is submitted as well,
    # hence its data is null, but valid, and we don't want to erase it.
    # It's simple to use another url. We could use hidden form fields.
    template = "search/preferences.jade"
    if request.method == 'POST':
        form = viewforms.BookshopForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                existing = users.Bookshop.objects.first()
                bookshop_model = users.Bookshop(**data)
                if existing:
                    bookshop_model.pk = existing.pk
                bookshop_model.save()
                messages.add_message(
                    request, messages.SUCCESS, _("Preferences saved."))
                return HttpResponseRedirect(reverse('preferences'))
            except Exception as e:
                log.error('Error saving the bookshop form: {}\n{}'.
                          format(e, traceback.format_exc))
                messages.add_message(
                    request, messages.ERROR, _("Preferences NOT saved."))

    form = viewforms.PrefsForm()
    bookshopform = viewforms.BookshopForm()
    return render(request, template, {
        'form': form,
        'bookshopform': bookshopform,
    })

def postSearch(data_source, details_url):
    """Call the postSearch function of the module imported with the name
    of data_source.

    data_source: a scraper name, containing a function postSearch
    details_url: url of the card's details.

    return: a dict of results (for books, must have the isbn/ean).
    """
    try:
        # Allow a scraper not to have the postSearch method.
        res = getattr(globals()[data_source], "postSearch")(details_url)
    except Exception as e:
        log.warning(e)
        res = {}
    return res

def _session_result_set(request, key, val):
    """Set request.session['search_result'][key] to val.

    Needed to mock for unit tests. Otherwise, during a test, the
    session remains a void list and we have a key error in the code below.
    """
    request.session['search_result'][key] = val

@login_required
def search(request):
    template = "search/searchresults.jade"
    return render(request, template)

def cards_without_eans(request):
    """
    Show all cards without INBS, or where it is "".
    """
    template = "search/cards_without_eans.jade"
    cards = Card.cards_without_eans()
    return render(request, template, {
        "cards": cards,
    })

@login_required
def card_create_manually(request):
    template = 'search/card_create.jade'
    if request.method == 'GET':
        card_form = viewforms.CardCreateForm()
        add_places_form = viewforms.CardPlacesAddForm()
        return render(request, template, {'form': card_form,
                                          'add_places_form': add_places_form})
    elif request.method == 'POST':
        card_form = viewforms.CardCreateForm(request.POST)
        add_places_form = viewforms.CardPlacesAddForm(request.POST)
        card = None

        if card_form.is_valid():
            card_dict = card_form.cleaned_data
            card, msgs = viewforms.CardCreateForm.create_card(card_dict)

            if not card:
                log.warning("create card manually: card not created? {}, {}"
                            .format(card_dict, msgs))
                messages.add_message(request, messages.SUCCESS, _('Warn: the card was not created.'))

        else:
            return render(request, template, {'form': card_form,
                                              'add_places_form': viewforms.CardPlacesAddForm()})

        if card and add_places_form.is_valid():
            places_qties = add_places_form.cleaned_data
            for name_id, qty in places_qties.items():
                if not qty:
                    continue
                place_id = name_id.split('_')[1]
                if place_id:
                    place_id = int(place_id)
                    place = Place.objects.get(id=place_id)
                    place.add_copy(card, nb=qty)
                    log.info("Card added to place {} x{}".format(place_id, qty))

            messages.add_message(request, messages.SUCCESS, _('The card was created successfully.'))

        else:
            return render(request, template, {'form': card_form,
                                              'add_places_form': add_places_form})

        # Return to… new void form?
        card_form = viewforms.CardCreateForm()
        add_places_form = viewforms.CardPlacesAddForm()
        return render(request, template, {'form': card_form,
                                          'add_places_form': add_places_form})

@login_required
def card_show(request, pk):
    template = "search/card_show.jade"
    card = None
    sells = []
    places = Place.objects.order_by("id").all()
    places_quantities = []
    total_sold = "0"
    if request.method == 'GET':
        card = get_object_or_404(Card, id=pk)

        # Update critical data from Dilicom, if possible.
        if dilicom_enabled():
            try:
                card, msgs = update_from_dilicom(card)
            except Exception:  # for ConnectionError
                pass

        # Ongoing commands.
        pending_commands = card.commands_pending()

        # Last time we entered this item
        last_entry = EntryCopies.last_entry(card)

        # Quantity per place.
        for place in places:
            places_quantities.append((place.name,
                                      place.quantity_of(card),
                                      place.name.replace(" ", "_").lower(),  # html id.
            ))

        # Quantity per box.
        quantity_boxes = card.quantity_boxes()

        # Sells since the last entry
        if last_entry:
            res = Sell.search(card.id, date_min=last_entry.created)
            total_sold = res['nb_cards_sold']

        # List of clients (for modale)
        clients = [it.to_dict() for it in Client.objects.order_by("name").all()]

        # Client reservations
        reservations = users.Reservation.get_card_reservations(pk)

    return render(request, template, {
        "object": card,
        "sells": sells,
        "clients": clients,
        # "shelves": Shelf.objects.order_by("name").all(),
        "places_quantities": places_quantities,
        "has_many_places": len(places) > 1,
        "quantity_boxes": quantity_boxes,
        "last_entry": last_entry,
        "total_sold": total_sold,
        "pending_commands": pending_commands,
        "page_title": "Abelujo - " + card.title[:50],
        "reservations": reservations,

        # Feature flags.
        "feature_show_reservation_button": settings.FEATURE_SHOW_RESERVATION_BUTTON
    })

def card_history(request, pk):
    """Show the card's sells, entries and commands history."""
    MAX = 100
    card = None
    template = "search/card_history.jade"

    if request.method == 'GET':
        card = get_object_or_404(Card, pk=pk)

        # Sells
        sells_data = Sell.search(card_id=card.id)

        # OutMovements
        # TODO: get all out movements
        # outmovement_set: direct link
        # outmovementcopies_set: linked from baskets
        outs = card.outmovementcopies_set.order_by("-created").all()[:MAX]

        # Commands
        pending_commands = card.commands_pending()
        commands = card.commands_received()

        # Other entries
        entries = card.entrycopies_set.order_by('-created').all()[:MAX]

    return render(request, template, {
        "card": card,
        "sells_data": sells_data,
        "entries": entries,
        "outs": outs,
        "pending_commands": pending_commands,
        "commands": commands,
        "page_title": "Abelujo - {} - {}".format(_("History"), card.title),
    })


@login_required
def card_buy(request, pk=None):
    form = viewforms.BuyForm()
    template = "search/card_buy.jade"
    card = Card.objects.get(id=pk)
    form = viewforms.BuyForm(initial={"quantity": 1})
    if request.method == 'GET':
        try:
            buying_price = card.price - (card.price * card.distributor.discount / 100)
        except Exception as e:
            buying_price = card.price

        return render(request, template, {
            "form": form,
            "card": card,
            "buying_price": buying_price,
        })

    if request.method == 'POST':
        # buying the card
        form = viewforms.BuyForm(request.POST)
        if form.is_valid():
            place = form.cleaned_data['place']
            nb = form.cleaned_data['quantity']
            bill = form.cleaned_data['bill']
            payment = form.cleaned_data['payment']
            place_obj = Place.objects.get(id=place)
            if bill and bill != "0":
                bill_obj = Bill.objects.get(id=bill)
                # Link to the bill:
                try:
                    bill_obj.add_copy(card, nb=nb)
                except Exception as e:
                    log.error(e)

            # Add to the place
            try:
                place_obj.add_copy(card, nb=nb)
            except Exception as e:
                log.error("couldn't add copies to {}: {}".format(place, e))

            # Log in History:
            try:
                entry, created = Entry.new([card], payment=payment)
            except Exception as e:
                log.error("couldn't add Entry in history: {}".format(e))

            return HttpResponseRedirect(reverse("card_search"))

    return render(request, template, {
        "form": form,
        "card": card,
        "buying_price": buying_price,
    })

@login_required
def card_places_add(request, pk=None):
    """
    Add the given card to Places.
    """
    template = "search/card_places_add.jade"
    params = request.GET

    if request.method == 'GET':
        form = viewforms.CardPlacesAddForm()
        return render(request, template, {
            "form": form,
            "pk": pk,
            "type": params.get('type'),
        })

    else:
        back_to = reverse("card_show", args=(pk,))
        form = viewforms.CardPlacesAddForm(request.POST)
        if form.is_valid():
            # When the field name was an int (the place id),
            # the form was valid but cleaned_data had None values.
            for (label_id, nb) in form.cleaned_data.items():
                if nb:
                    # the form field name is
                    # place_<id>
                    id = int(label_id.split('_')[1])
                    place = Place.objects.get(id=id)
                    if place:
                        card = Card.objects.get(id=pk)
                        try:
                            place.add_copy(card, nb=int(nb))
                        except Exception as e:
                            log.error("Adding Card {} to Place {}: if this happens, that's because of lacking form validation ! {}".format(pk, id, e))

        return HttpResponseRedirect(back_to)


@login_required
def card_move(request, pk=None):
    template = "search/card_move.jade"
    BasketsForm = viewforms.CardMove2BasketForm()
    internalForm = viewforms.MoveInternalForm()
    params = request.GET

    if request.method == 'POST':
        placeForm = viewforms.MoveInternalForm(request.POST)
        basketForm = viewforms.CardMove2BasketForm(request.POST)

        if placeForm.is_valid() and basketForm.is_valid():
            card_obj = Card.objects.get(pk=pk)
            data = placeForm.cleaned_data
            if data['nb']:
                orig_obj = Place.objects.get(id=data['origin'])
                dest_obj = Place.objects.get(id=data['destination'])
                try:
                    orig_obj.move(dest_obj, card_obj, data['nb'])
                except Exception as e:
                    log.error("couldn't move copies from {} to {}: {}".format(data['origin'], data['destination'], e))

            for (basket, nb) in basketForm.cleaned_data.items():
                if nb:
                    basket_obj = Basket.objects.get(name=basket)
                    try:
                        basket_obj.add_copy(card_obj, nb=nb)
                    except Exception as e:
                        log.error("couldn't add copies to {}: {}".format(basket, e))

            messages.add_message(request, messages.SUCCESS, _('The card "{}" was added successfully.'.format(card_obj.title)))
            # We can also retrieve the query parameters from the url:
            # url = request.META['HTTP_REFERER']
            # qparams = dict(urlparse.parse_qsl(urlparse.urlsplit(url).query))
            qparams = {'q': request.POST.get('q')}
            back_to = request.session.get("back_to")
            if not back_to:
                back_to = reverse("card_show", args=(pk,))
            # back_to += "?" + urlparse.urlsplit(url).query
            back_to += "?" + urllib.urlencode(qparams)
            # XXX back_to should be set more than once, per-search.
            if request.session.get("back_to"):
                del request.session["back_to"]
            return HttpResponseRedirect(back_to)

        else:
            # form not valid
            internalForm = viewforms.MoveInternalForm(request.POST)

    # method: GET
    return render(request, template, {
        "BasketsForm": BasketsForm,
        "internalForm": internalForm,
        "pk": pk,
        "q": request.GET.get('q'),
        "type": params.get('type'),
    })


@login_required
def cards_set_supplier(request, **kwargs):
    template = 'search/set_supplier.jade'
    form = viewforms.SetSupplierForm()
    newsupplier_form = viewforms.NewSupplierForm()
    cards_ids = request.session.get('set_supplier_cards_ids')
    if not cards_ids:
        return HttpResponseRedirect(reverse('card_collection'))
    cards_ids = cards_ids.split(',')
    response_dict = {
        'form': form,
        'newsupplier_form': newsupplier_form,
        'nb_cards': len(cards_ids),
    }

    if request.method == 'GET':
        return render(request, template, response_dict)

    elif request.method == 'POST':
        dist_id = None
        dist_obj = None
        req = request.POST.copy()

        # The user chose an existing distributor.
        if 'supplier' in list(req.keys()):
            form = viewforms.SetSupplierForm(req)
            if form.is_valid():
                dist_id = form.cleaned_data['supplier']
                dist_obj = Distributor.objects.get(id=dist_id)

        # Create distributor.
        elif 'discount' in list(req.keys()):
            form = viewforms.NewSupplierForm(req)
            if form.is_valid():
                data = form.cleaned_data

                # Check existing name.
                existing = Distributor.objects.filter(name=data['name'])
                if existing:
                    messages.add_message(request, messages.ERROR, _("A supplier with the same name already exists."))
                    response_dict['messages'] = messages.get_messages(request)
                    return render(request, template, response_dict)

                try:
                    dist_obj = Distributor(name=data['name'], discount=data['discount'])
                    dist_obj.save()
                except Exception as e:
                    log.error("Could not create new distributor: {}".format(e))
                    messages.add_message(request, messages.ERROR, _("An internal error occured, we have been notified."))
                    response_dict['messages'] = messages.get_messages(request)
                    return render(request, template, response_dict)

            else:
                messages.add_message(request, messages.ERROR, _("The form is invalid."))
                return render(request, template, response_dict)

        else:
            log.error("Error in the form setting the supplier for many cards. We didn't recognize any of the two forms.")
            return render(request, template, response_dict)

        # Set supplier for all cards.
        for id in cards_ids:
            try:
                card = Card.objects.get(id=id)
                card.distributor = dist_obj
                card.save()
            except Exception as e:
                log.error("Error batch-setting the distributor: {}".format(e))
                messages.add_message(request, messages.ERROR, _("Internal error :("))
                response_dict['messages'] = messages.get_messages(request)
                return render(request, template, response_dict)

        messages.add_message(request, messages.SUCCESS, _("The supplier was correctly set for those {} cards.".format(len(cards_ids))))

        return HttpResponseRedirect(reverse('card_collection'))

@login_required
def cards_set_shelf(request, **kwargs):
    template = 'search/set_shelf.jade'
    form = viewforms.SetShelfForm()
    newshelf_form = viewforms.NewShelfForm()
    cards_ids = request.session.get('set_shelf_cards_ids')
    if not cards_ids:
        return HttpResponseRedirect(reverse('card_collection'))
    cards_ids = cards_ids.split(',')
    response_dict = {
        'form': form,
        'newshelf_form': newshelf_form,
        'nb_cards': len(cards_ids),
    }

    if request.method == 'GET':
        return render(request, template, response_dict)

    elif request.method == 'POST':
        new_id = None
        new_obj = None
        req = request.POST.copy()

        # The user chose an existing shelf.
        if 'shelf' in list(req.keys()):
            form = viewforms.SetShelfForm(req)
            if form.is_valid():
                new_id = form.cleaned_data['shelf']
                new_obj = Shelf.objects.get(id=new_id)

        # Create new shelf.
        elif 'name' in list(req.keys()):
            form = viewforms.NewShelfForm(req)
            if form.is_valid():
                data = form.cleaned_data

                # Check existing name.
                existing = Shelf.objects.filter(name=data['name'])
                if existing:
                    messages.add_message(request, messages.ERROR, _("A shelf with the same name already exists."))
                    response_dict['messages'] = messages.get_messages(request)
                    return render(request, template, response_dict)

                try:
                    new_obj = Shelf(name=data['name'])
                    new_obj.save()
                except Exception as e:
                    log.error("Could not create new shelf: {}".format(e))
                    messages.add_message(request, messages.ERROR, _("An internal error occured, we have been notified."))
                    response_dict['messages'] = messages.get_messages(request)
                    return render(request, template, response_dict)

            else:
                messages.add_message(request, messages.ERROR, _("The form is invalid."))
                return render(request, template, response_dict)

        else:
            log.error("Error in the form setting the shelf for many cards. We didn't recognize any of the two forms.")
            return render(request, template, response_dict)

        # Set shelf for all cards.
        cards = Card.objects.filter(id__in=cards_ids)
        cards.update(shelf=new_obj)
        messages.add_message(request, messages.SUCCESS, _("The shelf was correctly set for those {} cards.".format(len(cards_ids))))

        return HttpResponseRedirect(reverse('card_collection'))


@login_required
def collection_export(request, **kwargs):
    """Export a search of our stock or all of it.

    - format: text, csv.
    - select: all, selection.
    """

    now = datetime.date.strftime(timezone.now(), '%Y-%m-%d %H:%M')

    if request.method == 'GET':
        formatt = request.GET.get('format')
        select = request.GET.get('select')
        query = request.GET.get('query')
        distributor = request.GET.get("distributor")
        distributor_id = request.GET.get("distributor_id")
        card_type_id = request.GET.get("card_type_id")
        publisher_id = request.GET.get("publisher_id")
        place_id = request.GET.get("place_id")
        shelf_id = request.GET.get("shelf_id")
        order_by = request.GET.get("order_by")
        quantity_choice = request.GET.get("quantity_choice")
        # bought = request.GET.get("in_stock")

        # Export all the stock or a custom search ?
        # would rather validate request.GET and **
        # or call api's cards search and get the json.
        if select == "selection":
            query_list = query.split(" ")
            res, meta = Card.search(query_list, to_list=True,
                                    distributor=distributor,
                                    distributor_id=distributor_id,
                                    publisher_id=publisher_id,
                                    card_type_id=card_type_id,
                                    place_id=place_id,
                                    shelf_id=shelf_id,
                                    quantity_choice=quantity_choice,
                                    order_by=order_by,
                                    in_deposits=True)

        elif select == "all":
            # res = Card.objects.filter(in_stock=True).all()
            res = Card.cards_in_stock()

        if not os.path.exists(settings.EXPORTS_ROOT):
            os.makedirs(settings.EXPORTS_ROOT)

        # Which format ?
        if formatt == 'txt':
            content_type = "text/raw"
            content = ppcard(res)

        elif formatt == "csv":
            content_type = "text/csv"
            # Be careful. With to_list=True above, this should not be needed.
            if not isinstance(res[0], dict):
                res = [it.to_list() for it in res]
            content = cards2csv(res)

        else:
            content = "This format isn't supported."

        # Save the file.
        filename = "abelujo-stock-{}.{}".format(now, formatt)
        filepath = os.path.join(settings.EXPORTS_ROOT, filename)
        if formatt == 'csv':
            with open(filename, 'w') as f:
                f.write(content)
        else:
            with io.open(filepath, 'w', encoding='utf8') as f:
                f.write(content)

        # Build the response.
        response = HttpResponse(content, content_type=content_type)
        filename = "Abelujo stock search"
        if query:
            filename += " - {}".format(query)

        response['Content-Disposition'] = 'attachment; filename="{}.{}"'.format(filename, formatt)
        return response

    else:
        content = "no search query"

    return HttpResponse(content, content_type=content_type)

@login_required
def collection_exports(request):
    """
    View the stock export files.
    """
    template = "search/collection_exports.html"
    files = os.listdir(settings.EXPORTS_ROOT)
    files = list(reversed(sorted(files)))
    return render(request, template, {"files": files})

@login_required
def collection_view_file_export(request, filename):
    if filename:
        filepath = os.path.join(settings.EXPORTS_ROOT, filename)
        content = None
        with open(filepath, "r") as f:
            content = f.read()
        content_type = filename_content_type(filename)
        response = HttpResponse(content, content_type=content_type)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return response

@login_required
def collection(request):
    """Search our own collection and take actions.

    - return: a list (of card dicts)
    """
    currency = Preferences.get_default_currency() or "€"
    return render(request, "search/collection.jade", {
        'currency': currency,
    })

@login_required
def sell(request):
    show_selling_places = False
    if Place.objects.count() > 1:
        show_selling_places = True
    return render(request, "search/sell_create.jade",
                  {
                      "show_selling_places": show_selling_places
                  })

@login_required
def sell_details(request, pk):
    template = "search/sell_details.jade"
    sell = None
    soldcards = []
    total_sell = None
    total_price_init = None

    if request.method == 'GET':
        try:
            sell = Sell.objects.get(id=pk)
        except Exception as e:
            log.error(e)
            #XXX return a 404

        if sell:
            soldcards = sell.soldcards_set.all()
            total_sell = sum([it.price_sold for it in soldcards])
            total_price_init = sum([it.price_init for it in soldcards])

    return render(request, template, {
        "sell": sell,
        "soldcards": soldcards,
        "total_sell": total_sell,
        "total_price_init": total_price_init,
    })

def restocking(request):
    template = "search/restocking.html"
    cards = Restocking.cards()
    return render(request, template, {
                  'cards': cards,
        })


def deposits(request):
    """
    Return the deposits accepted by the bookshop (brought there by someone).
    """
    # We currently (2020/01) don't return anymore the deposits that are sent by us to someone else (pubtype in old code).
    PAGE_SIZE = 50
    fixtype = Deposit.objects.filter(deposit_type="fix")
    paginator = Paginator(fixtype, PAGE_SIZE)
    page = request.GET.get('page', 1)
    num_pages = paginator.num_pages,
    if page > num_pages or page < 1:
        return redirect("deposits")
    deposit_page = paginator.page(page)
    total_price_fix = sum([it.total_init_price if it.total_init_price else 0 for it in fixtype])

    nb_results = fixtype.count()
    meta = {
        'nb_results': nb_results,
        'page': page,
        'page_size': PAGE_SIZE,
        'num_pages': paginator.num_pages,
    }

    return render(request, "search/deposits.jade", {
        'depo_fix': deposit_page,
        'total_price_fix': total_price_fix,
        'meta': meta,
    })

@login_required
def deposits_new(request):
    return render(request, "search/deposits_create.jade", {
        "DepositForm": viewforms.DepositForm(),
    })

@login_required
def deposits_create(request):
    # results = 200
    if request.method == "POST":
        req = request.POST.copy()
        form = viewforms.DepositForm(req)
        if form.is_valid():
            deposit = form.cleaned_data
            try:
                msgs = Deposit.from_dict(deposit)
                for msg in msgs:
                    messages.add_message(request, msg["level"],
                                         msg["message"])
            except Exception as e:
                log.error("Error when creating the deposit: %s" % e)
                messages.add_message(request, messages.ERROR,
                                     _("Error when adding the deposit"))

        else:
            return render(request, "search/deposits_create.jade", {
                "DepositForm": form,
            })

    return redirect("/deposits/")  # should make status follow

@login_required
def deposits_add_card(request):
    """Add the given card (post) to the given deposit (in the form).
    """
    resp_status = 200
    req = request.POST.copy()
    form = viewforms.AddToDepositForm(req)
    if request.method == "POST":
        if not form.is_valid():
            log.debug("deposits_add_card: form is not valid")
            resp_status = 500
        else:
            card_isbn = req["isbn"]
            if not card_isbn:
                log.debug("deposits_add_card: the isbn is null. That should not happen !")
                resp_status = 400
                messages.add_message(request, messages.ERROR,
                                     _("We could not add the card to the deposit: the given isbn is null."))
            else:
                deposit_id = form.cleaned_data["deposit"]  # noqa: F841
                # TODO: do the logic !
                messages.add_message(request, messages.SUCCESS,
                                     _('The card were successfully added to the deposit.'))

    retlist = request.session.get("collection_search")  # noqa: F841
    redirect_to = req.get('redirect_to')
    return redirect(redirect_to, status=resp_status)


@login_required
def deposits_view(request, pk):
    """Display the given deposit."""
    deposit = None
    template = "search/deposits_view.jade"
    try:
        deposit = Deposit.objects.get(pk=pk)
        cards_balance = deposit.checkout_balance()

    except Deposit.DoesNotExist as e:
        messages.add_message(request, messages.ERROR, _("This deposit doesn't exist !"))
        log.error("le depot demande (%s) n'existe pas: %s" % (pk, e))
        return HttpResponseRedirect(reverse("deposits"))

    return render(request, template, {
        "page_title": "Abelujo - " + deposit.name,
        "deposit": deposit,
        "cards_balance": cards_balance,
    })

@login_required
def deposits_checkout(request, pk):
    """
    """
    # template = "search/deposits_view.jade"
    deposit = Deposit.objects.get(pk=pk)
    msgs = []
    try:
        status, msgs = deposit.checkout_close()
        for msg in msgs:
            messages.add_message(request, messages.INFO, msg)
    except Exception as e:
        log.error("Error while closing deposing state: {}".format(e))
        messages.add_message(request, messages.ERROR,
                             _("Woops, there was an error :S we can't close this deposit state."))
        return HttpResponseRedirect(reverse("deposits_view", args=(pk,)))

    return HttpResponseRedirect(reverse("deposits_view", args=(pk,)))

@login_required
def deposit_delete(request, pk):
    """
    """
    pass

@login_required
def deposit_add_copies(request, pk):
    """Add copies to this deposit. (only ones that already exist)
    """
    template = "search/deposit_add_copies.jade"
    form = viewforms.DepositAddCopiesForm(pk=pk)
    if request.method == "GET":
        pass

    if request.method == "POST":
        form = viewforms.DepositAddCopiesForm(request.POST, pk=pk)
        if form.is_valid():
            data = form.cleaned_data
            dep = Deposit.objects.get(id=pk)
            for id, qty in data.items():
                dep.add_copies([id], quantities=[qty])

            return HttpResponseRedirect(reverse("deposits_view", args=(pk,)))

    return render(request, template, {
        "form": form,
        "pk": pk,
    })


@login_required
def basket_auto_command(request):
    template = "search/to_command_index.jade"

    basket = Basket.auto_command_basket()
    # We get all cards, and group them by distributor.
    copies = basket.copies.all()
    total_copies = len(copies)
    copies_by_dist = toolz.groupby(lambda it: it.distributor_id, copies)
    dists = []
    no_dist = []
    for (dist_id, copies) in list(copies_by_dist.items()):
        if dist_id is not None:
            dists.append((Distributor.objects.get(id=dist_id), len(copies)))
        else:
            no_dist = ((_("NO SUPPLIER"), len(copies)))

    # bof
    dists = sorted(dists, cmp=lambda it, that: it[0].name.lower() < that[0].name.lower())
    if request.method == "GET":
        return render(request, template, {
            'dists': dists,
            'no_dist': no_dist,
            'total_copies': total_copies,
        })

@login_required
def basket_auto_command_empty(request):
    if request.method == "POST":
        basket = Basket.auto_command_basket()
        basket.basketcopies_set.all().delete()
        # messages.add_message(request, messages.SUCCESS, _("List of commands emptied successfully."))
        return HttpResponseRedirect(reverse('basket_auto_command'))
    return HttpResponseRedirect(reverse('basket_auto_command'))

@login_required
def command_supplier(request, pk):
    template = "search/to_command.jade"
    return render(request, template)

@login_required
def baskets(request):
    template = "search/baskets.jade"
    if request.method == "GET":
        return render(request, template)

@login_required
def basket_list(request):
    """
    Simple list of baskets. Vue stuff only on a basket page.
    """
    template = 'search/basket_list.html'
    if request.method == "GET":
        baskets = Basket.objects.all()[1:]  # not the auto_command
        return render(request, template, {
            'baskets': baskets,
        })

@login_required
def boxes(request):
    template = "search/baskets.jade"
    if request.method == "GET":
        return render(request, template, {
        })

@login_required
def basket_view(request, pk):
    template = 'search/basket_view.html'
    if request.method == "GET":
        basket = Basket.objects.get(pk=pk)
        return render(request, template, {
            'basket': basket,
        })

@login_required
def basket_export(request, pk):
    """Export the given basket to txt, csv or pdf, with or without barcodes.

    Possible GET parameters:
    - report: bill, listing, simplelisting
    - format: txt, pdf, csv
    - distributor_id: a distributor id (see To Command basket)

    Return: an HttpResponse with the right content type.
    """
    response = HttpResponse()

    try:
        basket = Basket.objects.get(id=pk)
    except Exception as e:
        log.error("Error trying to export basket{}: {}".format(pk, e))
        return response

    # copies_set = basket.basketcopies_set.all()

    report = request.GET.get('report')
    format = request.GET.get('format')
    distributor_id = request.GET.get('distributor_id')
    # Export of all cards: distributor_id is None.
    # Export of cards with no distributor_id:
    if distributor_id == 'undefined' or distributor_id in [""]:
        distributor_id = -1
    elif distributor_id in ["all", u"all"]:
        pass
    elif distributor_id:
        distributor_id = int(distributor_id)
        # TODO: filter the copies by distributor, or absence thereof.

    # see also auto_command_copies (that returns a list instead of a QS)
    copies_set = Basket.search(pk, distributor_id=distributor_id)

    barcodes = _is_truthy(request.GET.get('barcodes'))
    covers = _is_truthy(request.GET.get('covers'))

    distributor = basket.distributor
    list_name = _("Liste")
    if distributor:
        list_name = list_name + " {}".format(distributor.name)
    elif basket:
        list_name = list_name + " {}".format(basket.name)

    if copies_set and report and format:
        response = _export_response(copies_set, report=report, format=format,
                                    distributor_id=distributor_id,
                                    barcodes=barcodes,
                                    covers=covers,
                                    name=list_name)
        # exporting response for dist 9 took 0:00:04.128225
        # filtering dist by query
        # basket search distributor_id 9 took 0:00:00.000333
        # exporting response for dist 9 took 0:00:04.598553 = same csv generation time.
        # with rows generated by values_list: see below
        # --
        # exporting response for dist 2 (sodis, 300 cards) took 0:00:00.444018

    return response

def _export_response(copies_set, report="", format="", inv=None, name="", distributor_id=None,
                     discount=0,
                     covers=False,
                     barcodes=False,
                     total=None,
                     total_with_discount=None):
    """Build the response with the right data (a bill ? just a list ?).

    - copies_set: list of objects, like basketcopies_set: has attributes card and quantity.
    - inv: inventory object (necessary to get the diff and the sold cards).

    Return: formatted HttpResponse
    """
    response = HttpResponse()
    quantity_header = _("Quantity")
    rows = None

    if report == 'bill':
        # The cards of the inventory alongside their quantities.
        if inv:
            header = (_("Title"), _("Quantity sold"))
            diff = inv.diff()[0]  # that should be cached XXX. A json row in the db ?
            rows = []
            for k in diff.values():
                if k.get('diff', 0) < 0:
                    qtysold = - k.get('diff')
                else:
                    qtysold = 0
                rows.append((k['card'], qtysold))

            # Sort quantities first, then by title.
            rows = sorted(rows)
            rows = sorted(rows, key = lambda it: it[1] > 0, reverse=True)  # with quantities first

        else:
            log.eror("Implementation error: if you want a bill, that's certainely from an inventory, but we don't have the 'inv' object.")

    elif report == 'listing':
        # inv_cards = inv.inventorycopies_set.all()
        header = ("ISBN", _("Title"), _("Authors"), _("Publishers"), _("Supplier"),
                  _("Shelf"),
                  _("Price"),
                  _("with discount"),
                  _("Quantity"))
        rows = [
            (ic.card.isbn if ic.card.isbn else "",
             ic.card.title,
             ic.card.authors_repr,
             ic.card.pubs_repr,
             ic.card.distributor_repr,
             ic.card.shelf.name if ic.card.shelf else "",
             ic.card.price,
             ic.card.price_discounted,
             ic.quantity)
            for ic in copies_set]
        rows = sorted(rows)

    elif report == 'simplelisting':
        header = None
        rows = copies_set
        # List of ISBN / quantity to command (BasketCopy.nb)
        rows = copies_set.values_list('card__isbn', 'nb')
        # rows = [
        # (ic.card.isbn,
        # ic.quantity)
        # for ic in rows]
        # generating simplelisting rows took 0:00:02.602288
        # with values_list:
        # generating simplelisting rows took 0:00:00.000188  \o/
        rows = sorted(rows)

    # From here we have rows: list of tuples with the card obj and the quantity.
    if rows is None:
        log.error("No rows when exporting to file. Shouldn't happen !")

    if format in ['csv']:
        pseudo_buffer = Echo()
        writer = unicodecsv.writer(pseudo_buffer, delimiter=b';')
        content = writer.writerow(b"")

        if report in ['bill']:
            rows = [(it[0].title, it[1]) for it in rows]
        if header:
            rows.insert(0, header)
        start = timezone.now()
        content = b"".join([writer.writerow(row) for row in rows])
        end = timezone.now()
        print("writing rows to csv took {}".format(end - start))

        response = StreamingHttpResponse(content, content_type="text/csv")
        response['Content-Disposition'] = 'attachment; filename="{}.csv"'.format(name)

    elif format in ['txt']:
        # 63 = MAX_CELL + 3 because of trailing "..."
        rows = ["{:63} {:20} {}".format(truncate(it.card.title),
                                         it.card.pubs_repr,
                                         it.quantity) for it in copies_set]
        rows = sorted(rows)
        content = "\n".join(rows)
        response = HttpResponse(content, content_type="text/raw")

    elif format in ['pdf']:
        date = datetime.date.today()
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="{}.pdf"'.format(name)

        template = get_template('pdftemplates/pdf-barcode.jade')
        if report == "listing":
            cards_qties = [(it.card, it.quantity) for it in copies_set]
        elif report == "bill":
            quantity_header = _("Quantity sold")
            for it in rows:
                if not is_isbn(it[0].isbn):
                    it[0].isbn = "0000000000000"

            cards_qties = rows

        if total is None:
            total = sum([it[1] * it[0].price if it[0].price else 0 for it in cards_qties])
        if discount:
            total = total - total / 100 * discount
        if total_with_discount is None:
            total_with_discount = -1  # unemplemented. Inventories should compute it before.
        total_qty = sum([it[1] for it in cards_qties])

        # barcode
        start = time.time()
        if barcodes:
            for card, _noop in cards_qties:
                # Find or create the base64 barcode.
                search = Barcode64.objects.filter(ean=card.ean)
                if not search:
                    eanbase64 = Barcode64.ean2barcode(card.ean)
                    try:
                        if eanbase64:
                            log.info("---- saving a base64 for ean {}".format(card.ean))
                            Barcode64(ean=card.ean, barcodebase64=eanbase64).save()
                    except Exception as e:
                        log.error('Error saving barcode of ean {}: {}'.format(card.ean, e))
                else:
                    eanbase64 = search[0].barcodebase64

                card.eanbase64 = eanbase64

        sourceHtml = template.render({'cards_qties': cards_qties,
                                      'name': name,
                                      'total': total,
                                      'total_with_discount': total_with_discount,
                                      'total_qty': total_qty,
                                      'barcode': barcodes,
                                      'covers': covers,
                                      'quantity_header': quantity_header,
                                      'date': date})

        genstart = time.time()
        outhtml = HTML(string=sourceHtml).write_pdf()
        genend = time.time()
        log.info("------ html generation is taking {}".format(genend - genstart))

        response = HttpResponse(outhtml, content_type='application/pdf')
        end = time.time()
        log.info("-------- generating barcodes for {} cards took {}".format(len(cards_qties), end - start))
        response['Content-Disposition'] = 'attachment; filename="{}.pdf"'.format(name)

    return response

def history_sells(request, **kwargs):
    now = pendulum.now()
    url = reverse('history_sells_month',
                  args=(now.strftime('%Y-%m'),))
    return HttpResponseRedirect(url)

def history_sells_month(request, date, **kwargs):
    template = 'search/history_sells.jade'
    try:
        day = pendulum.datetime.strptime(date, '%Y-%m')
    except Exception:
        return HttpResponseRedirect(reverse('history_sells'))  # xxx: loop?

    now = pendulum.datetime.now()
    year = day.year
    month = day.month
    previous_month = day.subtract(months=1).replace(day=1)
    next_month = day.add(months=1).replace(day=1)

    data = Sell.stat_days_of_month(month=month, year=year)

    return render(request, template, {'sells_data': data,
                                      'day': day,
                                      'now': now,
                                      'previous_month_obj': previous_month,
                                      'previous_month': previous_month.strftime('%Y-%m'),
                                      'next_month_obj': next_month,
                                      'next_month': next_month.strftime('%Y-%m'),
                                      'year': year})

def _csv_response_from_rows(rows, headers=None, filename=''):
    pseudo_buffer = Echo()
    writer = unicodecsv.writer(pseudo_buffer, delimiter=b';')
    content = writer.writerow(b"")

    if headers:
        rows.insert(0, headers)
    start = timezone.now()
    content = b"".join([writer.writerow(row) for row in rows])
    end = timezone.now()
    print("writing rows to csv took {}".format(end - start))

    response = StreamingHttpResponse(content, content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="{}.csv"'.format(filename)
    return response

def _txt_response_from_rows(rows, filename=""):
    # 63 = MAX_CELL + 3 because of trailing "..."
    # Not ideal, but for compliance with the csv method we get a list of data, not a dict:
    # (sell.card.title,         # 0
    #      sell.card.isbn,      # 1
    #      sell.card.authors_repr,
    #      sell.card.pubs_repr,
    #      sell.card.distributor_repr, # 4
    #      sell.card.shelf.name if sell.card.shelf else "",
    #      sell.card.price,      # 6
    #      sell.card.price_discounted, # 7
    #      sell.quantity)        # 8

    format_str = "{:63} {} {:23} {:20} {:5} {:5} {:3}"
    rows = [format_str.
            format(truncate(it[0]),
                   it[1],
                   truncate(it[3], max_length=20),
                   it[4],
                   it[6],
                   it[7],
                   it[8].decode('utf8'),
            ) for it in rows]
    rows = sorted(rows)
    content = "\n".join(rows)
    response = HttpResponse(content, content_type="text/raw")
    response['Content-Disposition'] = 'attachment; filename={}.txt'.format(filename)
    return response

def history_sells_month_export(request, date, **response_kwargs):
    try:
        day = pendulum.datetime.strptime(date, '%Y-%m')
    except Exception:
        return HttpResponseRedirect(reverse('history_sells'))  # xxx: loop?

    data = Sell.search(year=day.year, month=day.month,
                       with_total_price_sold=False)

    fileformat = request.GET.get('fileformat')
    filename = _("Sells_{}-{}".format(day.year, day.month))

    headers = (_("Title"), "ISBN", _("Authors"), _("Publishers"), _("Supplier"),
               _("Shelf"),
               _("Price"),
               _("with discount"),
               _("Payment"),
               _("Quantity"))
    rows = [
        (soldcard.card.title,
         soldcard.card.isbn,
         soldcard.card.authors_repr,
         soldcard.card.pubs_repr,
         soldcard.card.distributor_repr,
         soldcard.card.shelf.name if soldcard.card.shelf else "",
         soldcard.card.price,
         soldcard.card.price_discounted,
         soldcard.sell.payments_repr(),
         soldcard.quantity)
        for soldcard in data['data']]
    rows = sorted(rows)

    if fileformat in ['csv']:
        response = _csv_response_from_rows(rows, headers=headers, filename=filename)
        return response

    if fileformat in ['txt']:
        response = _txt_response_from_rows(rows, filename=filename)
        return response


def history_entries_month(request, date, **kwargs):
    template = 'search/history_entries.jade'
    try:
        day = pendulum.datetime.strptime(date, '%Y-%m')
    except Exception:
        return HttpResponseRedirect(reverse('history_sells'))

    now = pendulum.datetime.now()
    year = day.year
    month = day.month
    previous_month = day.subtract(months=1).replace(day=1)
    next_month = day.add(months=1).replace(day=1)

    data = history.Entry.history(year=year, month=month)
    return render(request, template, {'data': data,
                                      'now': now,
                                      'day': day,
                                      'previous_month': previous_month,
                                      'next_month': next_month,
                                      'year': year})

def history_sells_day(request, date, **kwargs):
    """
    Return the list of sells of this day.

    - date: string (format %Y-%M-%d)
    """
    template = 'search/history_sells_day.html'
    # XXX: view called twice?? as well as history_sells
    try:
        day = pendulum.datetime.strptime(date, PENDULUM_YMD)
    except Exception as e:
        log.error('History per days: could not parse {}: {}'.format(date, e))
        return HttpResponseRedirect(reverse('history_sells'))

    sells_data = Sell.search(day=day.day, month=day.month, year=day.year,
                             with_total_price_sold=True,
                             sortorder=1)  # ascending

    # Best sells per card type.
    best_sells = models.get_best_sells(sells_data['data'])

    # Stats by card_type
    # grouped_sells = toolz.groupby(lambda (it): it.card.card_type, sells_data['data'])
    grouped_sells = toolz.groupby(lambda (it): it[2], sells_data['not_books'])
    # data for the template.
    data_grouped_sells = []
    for card_type, soldcards in grouped_sells.iteritems():
        # solcards: tuple quantity, price_sold, card_type.pk, isbn, type name
        if card_type is None:
            type_name = _("undefined")
        else:
            if soldcards:
                type_name = soldcards[0][4]
            else:
                type_name = ""
        datadict = [type_name, {}]
        datadict[1]['data'] = soldcards
        datadict[1]['total_sells'] = sum([it[0] for it in soldcards])
        datadict[1]['nb_sells'] = len(soldcards)
        totalsold = sum([it[0] * it[1] for it in soldcards])
        datadict[1]['total_sold'] = totalsold
        datadict[1]['sell_mean'] = totalsold / len(soldcards) if soldcards else 0
        data_grouped_sells.append(datadict)

    now = pendulum.datetime.today()
    previous_day = day.subtract(days=1)  # yes, not subStract.
    previous_day_fmt = previous_day.strftime(PENDULUM_YMD)
    next_day = None
    next_day_fmt = None
    if day < now:
        next_day = day.add(days=1)
        next_day_fmt = next_day.strftime(PENDULUM_YMD)

    # Visually show the same sells with the same background color.
    bg_colors = []
    white = ""
    # grey = "#d3d3d3"
    grey = "#eee9e9"  # snow2
    grey2 = "#cdc9c9"
    previous_sell_id = -1
    cur_color = grey2

    # In the template, we want to know the first soldcard of a sell
    # transaction.
    # Yes, we should have iterated over sells and then over soldcards.
    sell_transaction_markers = []
    sells_ids = []

    def flip_color(color):
        if color == white:
            return grey
        elif color == grey:
            return grey2
        return white

    # Show payments (abbreviated).
    payments = []
    payments_2 = []
    for it in sells_data['data']:
        sells_ids.append("{}".format(it.sell_id))
        if it.sell_id == previous_sell_id:
            bg_colors.append(cur_color)
            previous_sell_id = it.sell_id
            payments.append("")
            payments_2.append("")
            sell_transaction_markers.append(False)
        else:
            cur_color = flip_color(cur_color)
            bg_colors.append(cur_color)
            previous_sell_id = it.sell_id
            payments.append(get_payment_abbr(it.sell.payment))
            payments_2.append(get_payment_abbr(it.sell.payment_2) or "")
            sell_transaction_markers.append(True)

    data = list(zip(sells_data['data'], bg_colors, payments, payments_2, sell_transaction_markers, sells_ids))

    return render(request, template, {'sells_data': sells_data,
                                      'data': data,
                                      'best_sells': best_sells,
                                      'data_grouped_sells': data_grouped_sells,
                                      'previous_day': previous_day,
                                      'previous_day_fmt': previous_day_fmt,
                                      'next_day': next_day,
                                      'next_day_fmt': next_day_fmt,
                                      'month_fmt': '{}-{}'.format(day.year,
                                                                  format(day.month, '0>2')),
                                      'now': now,
                                      'day': day})

def history_entries_day(request, date, **kwargs):
    """
    Return the list of entries of this day.

    - date: string (format %Y-%M-%d)
    """
    template = 'search/history_entries_day.jade'
    try:
        day = pendulum.datetime.strptime(date, PENDULUM_YMD)
    except Exception as e:
        log.error('Entries history per day: could not parse {}: {}'.format(date, e))
        return HttpResponseRedirect(reverse('history_entries_month'))

    data = history.Entry.history_day(year=day.year, month=day.month, day=day.day)

    now = pendulum.datetime.today()
    previous_day = day.subtract(days=1)  # yes, not subStract.
    previous_day_fmt = previous_day.strftime(PENDULUM_YMD)
    next_day = None
    next_day_fmt = None
    if day < now:
        next_day = day.add(days=1)
        next_day_fmt = next_day.strftime(PENDULUM_YMD)

    shelves = data['entries'].values_list('card__shelf__name', flat=True)
    # remove duplicates
    shelves = [it for it in shelves if it is not None]
    shelves = list(set(shelves))

    publishers = data['entries'].values_list('card__publishers__name', flat=True)
    publishers = list(set(publishers))
    publishers = [it for it in publishers if it is not None]

    return render(request, template, {'data': data,
                                      'shelves': shelves,
                                      'publishers': publishers,
                                      'previous_day': previous_day,
                                      'previous_day_fmt': previous_day_fmt,
                                      'next_day': next_day,
                                      'next_day_fmt': next_day_fmt,
                                      'month_fmt': '{}-{}'.format(day.year,
                                                                  format(day.month, '0>2')),
                                      'now': now,
                                      'day': day})

def history_sells_exports(request, **kwargs):
    """Export a list of Sells in csv or txt.
    If no date nor distributor is given, export the first 50 results.

    - month: int (starting at 1 for python, when it starts at 0 in js)
    - year: int
    - distributor_id: int

    Return: a StreamingHttpResponse with the right content_type.
    """
    params = request.GET.copy()
    outformat = params.get('format')
    params.pop('format')
    month = params.get('month', timezone.now().month)
    year = params.get('year', timezone.now().year)
    distributor_id = params.get('distributor_id')
    filename = _("Sells history")
    if year:
        filename += " - {}".format(year)
    if month:
        filename += "-{}".format(month)

    response = None
    res = Sell.search(to_list=True,
                      distributor_id=distributor_id,
                      month=month,
                      year=year)
    # total = res.get('total')
    res = res['data']

    if outformat in ['csv']:
        pseudo_buffer = Echo()
        writer = unicodecsv.writer(pseudo_buffer, delimiter=b';')
        content = writer.writerow(b"")

        rows = [(it['created'],
                 it['price_sold'],
                 it['card']['title'],
                 it['card']['distributor']['name'] if it['card']['distributor'] else "",
                )
                for it in res]
        header = (_("date sold"),
                  _("price sold"),
                  _("title"),
                  _("supplier"),
        )
        rows.insert(0, header)
        content = b"".join([writer.writerow(row) for row in rows])

        response = StreamingHttpResponse(content, content_type="text/csv")
        response['Content-Disposition'] = 'attachment; filename="{}.csv"'.format(filename)

    elif outformat in ['txt']:
        rows = ["{}-+-{}-+-{}-+-{}-+-{}".format(
            _("date sold"),
            _("price sold"),
            _("title"),
            _("supplier"),
        )]
        # format: {:min width.truncate}
        # https://pyformat.info/
        rows += sorted(["{:10.10} {} {:5} {:30} {}".format(
            it['created'],
            it.get('price_sold', 0),
            truncate(it['card']['title']),  # truncate long titles
            it['card']['distributor']['name'] if it['card']['distributor'] else "",
        )
                        for it in res])
        content = "\n".join(rows)
        response = HttpResponse(content, content_type="text/raw")
        response['Content-Disposition'] = 'attachment; filename="{}.txt"'.format(filename)

    return response

@login_required
def suppliers_sells(request, **kwargs):
    now = pendulum.now()
    url = reverse('suppliers_sells_month',
                  args=(now.strftime('%Y-%m'),))
    return HttpResponseRedirect(url)

@login_required
def suppliers_sells_month(request, date, **kwargs):
    """
    Total sells of the month for distributors and
    publishers (for books that were not counted for distributors first).
    """
    template = 'search/suppliers_sells_month.jade'
    try:
        day = pendulum.datetime.strptime(date, '%Y-%m')
    except Exception:
        return HttpResponseRedirect(reverse('history_sells'))  # xxx: loop?

    now = pendulum.now()
    year = day.year
    month = day.month
    previous_month = day.subtract(months=1).replace(day=1)
    next_month = day.add(months=1).replace(day=1)
    res = Sell.history_suppliers(year=year, month=month)

    return render(request, template, {'publishers_data': res['publishers_data'],
                                      'distributors_data': res['distributors_data'],
                                      'day': day,
                                      'now': now,
                                      'previous_month_obj': previous_month,
                                      'previous_month': previous_month.strftime('%Y-%m'),
                                      'next_month_obj': next_month,
                                      'next_month': next_month.strftime('%Y-%m'),
                                      'year': year,
                                      'default_currency': Preferences.get_default_currency(),
    })

@login_required
def publisher_sells_month_list(request, pk, date, **kwargs):
    template = 'search/supplier_sells_month_list.jade'
    default_currency = Preferences.get_default_currency()
    try:
        day = pendulum.datetime.strptime(date, '%Y-%m')
    except Exception:
        return HttpResponseRedirect(reverse('history_sells'))  # xxx: loop?

    try:
        publisher_obj = Publisher.objects.get(id=pk)
    except ObjectDoesNotExist:
        # XXX: add message.
        return HttpResponseRedirect(reverse('suppliers_sells_month'))

    now = pendulum.now()
    year = day.year
    month = day.month
    previous_month = day.subtract(months=1).replace(day=1)
    next_month = day.add(months=1).replace(day=1)

    sells = Sell.sells_of_month(year=year, month=month, publisher_id=pk)

    cards_sold = sells.values_list('quantity', flat=True)
    nb_cards_sold = sum(cards_sold)
    prices_sold = sells.values_list('price_sold', flat=True)
    public_prices = sells.values_list('price_init', flat=True)
    assert len(prices_sold) == len(cards_sold)
    total = sum([cards_sold[i] * prices_sold[i] for i in range(len(prices_sold))])
    total_public_price = sum([public_prices[i] * cards_sold[i] for i in range(len(cards_sold))])

    url_name = 'publisher_sells_month_list'
    previous_month_url = reverse(url_name, args=(pk, previous_month.strftime('%Y-%m')))
    next_month_url = reverse(url_name, args=(pk, next_month.strftime('%Y-%m')))

    return render(request, template, {'sells': sells,
                                      'cards_sold': cards_sold,
                                      'nb_cards_sold': nb_cards_sold,
                                      'total': total,
                                      'total_fmt': price_fmt(total, default_currency),
                                      'total_public_price': total_public_price,
                                      'total_public_price_fmt': price_fmt(total_public_price, default_currency),
                                      'obj': publisher_obj,
                                      'day': day,
                                      'now': now,
                                      'next_month_url': next_month_url,
                                      'previous_month_url': previous_month_url,
    })

@login_required
def distributors_sells_month_list(request, pk, date, **kwargs):
    template = 'search/supplier_sells_month_list.jade'
    default_currency = Preferences.get_default_currency()
    try:
        day = pendulum.datetime.strptime(date, '%Y-%m')
    except Exception:
        return HttpResponseRedirect(reverse('history_sells'))  # xxx: loop?

    try:
        obj = Distributor.objects.get(id=pk)
    except ObjectDoesNotExist:
        # XXX: add message.
        return HttpResponseRedirect(reverse('suppliers_sells_month'))

    now = pendulum.now()
    year = day.year
    month = day.month
    previous_month = day.subtract(months=1).replace(day=1)
    next_month = day.add(months=1).replace(day=1)

    sells = Sell.sells_of_month(year=year, month=month, distributor_id=pk)
    # copy pasted :S
    cards_sold = sells.values_list('quantity', flat=True)
    nb_cards_sold = sum(cards_sold)
    prices_sold = sells.values_list('price_sold', flat=True)
    public_prices = sells.values_list('price_init', flat=True)
    assert len(prices_sold) == len(cards_sold)
    total = sum([cards_sold[i] * prices_sold[i] for i in range(len(prices_sold))])
    total_public_price = sum([public_prices[i] * cards_sold[i] for i in range(len(cards_sold))])

    url_name = 'distributors_sells_month_list'
    previous_month_url = reverse(url_name, args=(pk, previous_month.strftime('%Y-%m')))
    next_month_url = reverse(url_name, args=(pk, next_month.strftime('%Y-%m')))

    return render(request, template, {'sells': sells,
                                      'cards_sold': cards_sold,
                                      'nb_cards_sold': nb_cards_sold,
                                      'total': total,
                                      'total_fmt': price_fmt(total, default_currency),
                                      'total_public_price': total_public_price,
                                      'total_public_price_fmt': price_fmt(total_public_price, default_currency),
                                      'obj': obj,
                                      'day': day,
                                      'now': now,
                                      'next_month_url': next_month_url,
                                      'previous_month_url': previous_month_url,
    })

@login_required
def inventory_export(request, pk):
    total = total_with_discount = 0
    try:
        inv = Inventory.objects.get(id=pk)
    except Exception as e:
        log.error("Error trying to export inventory of pk {}: {}".format(pk, e))

    copies_set = inv.inventorycopies_set.all()

    report = request.GET.get('report')
    format = request.GET.get('format')
    barcodes = _is_truthy(request.GET.get('barcodes'))
    covers = _is_truthy(request.GET.get('covers'))
    total = inv.value()
    total_with_discount = inv.value(discount=True)

    response = _export_response(copies_set, report=report, format=format,
                                inv=inv,
                                barcodes=barcodes,
                                covers=covers,
                                name=inv.name,
                                total=total,
                                total_with_discount=total_with_discount,)

    return response

@login_required
def inventories(request):
    """Get all inventories.
    """
    template = "search/inventories.jade"
    if request.method == 'GET':
        return render(request, template)

@login_required
def inventory(request, pk):
    template = "search/inventory_view.jade"
    if request.method == "GET":
        if pk:
            try:
                inv = Inventory.objects.get(id=pk)  # noqa: F841
            except Exception as e:
                log.error(e)
            # state = inv.state()
            return render(request, template)

@login_required
def inventory_archive(request, pk):
    # if request.method == "POST":
    if request.method == "GET":
        if pk:
            try:
                inv = Inventory.objects.get(id=pk)
                inv.archive()
                messages.add_message(
                    request, messages.SUCCESS, _("The inventory {} was closed and archived.").format(inv.id))
            except Exception as e:
                log.error(e)
                messages.add_message(
                    request, messages.ERROR,
                    _("There was an error when trying to archive the inventory {}: {}.").format(pk, e))

    return HttpResponseRedirect(reverse("inventories"))

@login_required
def inventory_delete(request, pk):
    #XXX should be a post
    if request.method == "GET":
        if pk:
            try:
                inv = Inventory.objects.get(id=pk)
                id = inv.id
                inv.delete()
                messages.add_message(
                    request, messages.SUCCESS, _("The inventory {} was deleted.").format(id))
            except Exception as e:
                log.error(e)
                messages.add_message(
                    request, messages.ERROR,
                    _("There was an error when trying to delete the inventory {}: {}.").format(pk, e))

    return HttpResponseRedirect(reverse("inventories"))

@login_required
def inventory_terminate(request, pk):
    """
    """
    template = "search/inventory_terminate.jade"
    return render(request, template)

@login_required
def dashboard(request):
    template = "search/dashboard.jade"
    stock = Stats.stock()
    return render(request, template, {
        "stats_stock": stock,
    })


class CommandDetailView(DetailView):
    model = Command
    template_name = "search/commands_view.jade"


@login_required
def command_receive(request, pk):
    """
    GET: get the inventory state for this command.
    POST: create a new one.
    """
    template = "search/command_receive.jade"
    cmd = None

    try:
        cmd = Command.objects.get(id=pk)
    except ObjectDoesNotExist as e:
        log.warning(e)
        messages.add_message(request, messages.ERROR,
                             "Internal erorr: the command you requested does not exist.")
        return HttpResponseRedirect(reverse("commands_view", args=(pk,)))

    if not cmd.inventory:
        inv = InventoryCommand()
        inv.save()
        cmd.inv = inv
        cmd.save()

    return render(request, template)


@login_required
def command_receive_terminate(request, pk):
    """
    """
    template = "search/inventory_terminate.jade"
    return render(request, template)


@login_required
def command_receive_export(request, pk):
    cmd = _get_command_or_return(pk)
    inv = cmd.get_inventory()
    copies_set = inv.copies_set.all()
    inv_name = inv.name or inv.command.title

    report = request.GET.get('report')
    format = request.GET.get('format')
    barcodes = _is_truthy(request.GET.get('barcodes'))
    covers = _is_truthy(request.GET.get('covers'))

    response = _export_response(copies_set, report=report, format=format,
                                inv=inv,
                                barcodes=barcodes,
                                covers=covers,
                                name=inv_name)

    return response

@login_required
def command_card(request, pk):
    """
    Command the card of the given id, choose a client (optional).
    """
    template = "search/card_command.jade"

    if request.method == 'GET':
        card = None
        try:
            card = Card.objects.get(id=int(pk))
        except ObjectDoesNotExist:
            pass
        if card:
            return render(request, template)

@login_required
def catalogue_selection(request):
    """
    Show the selected cards for the online catalogue (ABStock in our case, for those who installed it side by side with Abelujo).
    """
    template = "search/catalogue_selection.html"
    if request.method == 'GET':
        cards = Card.objects.filter(is_catalogue_selection=True)
        return render(request, template, {
            'cards': cards,
        })
