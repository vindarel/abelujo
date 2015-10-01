# -*- coding: utf-8 -*-
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

import logging
import traceback
import urllib
import urlparse

from django import forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms.widgets import TextInput
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from djangular.forms import NgModelFormMixin
from unidecode import unidecode

from models import Basket
from models import Card
from models import CardType
from models import Deposit
from models import DepositState
from models import Distributor
from models import Inventory
from models import Place
from models import Publisher
from models import Sell
from search.models.utils import ppcard
from models import EntryCopies

log = logging.getLogger(__name__)

def entry_details(request, pk):
    """
    """
    pass
