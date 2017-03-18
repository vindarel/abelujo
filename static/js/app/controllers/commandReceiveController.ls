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

angular.module "abelujo" .controller 'CommandReceiveController', ['$http', '$scope', '$timeout', 'utils', '$filter', '$window', 'hotkeys', '$log', ($http, $scope, $timeout, utils, $filter, $window, hotkeys, $log) !->
    # utils: in services.js

    # set the xsrf token via cookies.
    # $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;

    {sum, map, filter, lines, reverse, join, reject, round} = require 'prelude-ls'

    # The cards fetched from the autocomplete.
    $scope.cards_fetched = []
    # The autocomplete choice.
    $scope.copy_selected = undefined
    $scope.history = []
    # The cards "inventoried" of the current session: the ones
    # displayed. They are saved in the db instantly.
    $scope.cards_selected = []
    # All the cards inventoried, even the ones we don't want to show anymore.
    $scope.all = []
    # Boolean to show or hide all the cards (hide by default)
    $scope.showAll = false  # toggled by the checkbox itself.
    $scope.cards_to_show = []
    # Total value
    $scope.total_value = 0
    # Nb of cards and copies
    $scope.nb_cards = 0
    $scope.nb_copies = 0

    $scope.tmpcard = undefined
    # A list of already selected cards' ids
    $scope.selected_ids = []
    existing_card = undefined

    # If we're on page /../inventories/XX/, get info of inventory XX.
    #XXX use angular routing
    $scope.inv_id = utils.url_id($window.location.pathname) # the regexp could include "inventories"
    $scope.cur_inv = "the parcel of a command !"  #XXX
    $scope.progress_current = 0

    $scope.language = utils.url_language($window.location.pathname)

    ######################
    # keyboard shortcuts
    # ####################
    hotkeys.bindTo($scope)
    .add do
        combo: "a"
        description: gettext "show all cards inventoried"
        callback: !->
            $scope.toggleCardsToShow!

    .add do
        combo: "s"
        description: gettext "go to the search box"
        callback: !->
           utils.set_focus!

    # Set focus:
    utils.set_focus!

    $window.document.title = "Abelujo - " + gettext("Inventory")

]
