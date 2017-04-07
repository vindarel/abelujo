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

angular.module "abelujo" .controller 'inventoryTerminateController', ['$http', '$scope', '$timeout', 'utils', '$filter', '$window', '$log', ($http, $scope, $timeout, utils, $filter, $window, $log) !->
    # utils: in services.js

    # set the xsrf token via cookies.
    # $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;

    {sum, map, filter, lines, join, Obj} = require 'prelude-ls'

    # ##############################################################################
    # This controller is used as well for USUAL INVENTORIES as for COMMANDS.
    # ##############################################################################
    is_default_inventory = false
    is_command_receive = false
    pathname = $window.location.pathname

    $scope.inv_or_cmd_id = utils.url_id($window.location.pathname) # the regexp could include "inventories"

    String.prototype.contains = (it) -> this.indexOf(it) != -1
    if pathname.contains "inventories"
        is_default_inventory = true
        $log.info "found default inventory"
        api_inventory_id = "/api/inventories/{inv_or_cmd_id}/"
    else if pathname.contains "commands"
        is_command_receive = true
        $log.info "found a command inventory."
        api_inventory_id = "/api/commands/{inv_or_cmd_id}/receive/"

    else
        $log.error "What are we doing the inventory of ??"
        ...

    # Common url end points:
    api_inventory_id_diff = api_inventory_id + "diff/"
    api_inventory_id_apply = api_inventory_id + "apply/"

    # Disambiguate url for inventory or commands' parcels.
    get_api = (api) ->
        api.replace "{inv_or_cmd_id}", $scope.inv_or_cmd_id


    ##################### inventory controller #####################################
    # The cards fetched from the autocomplete.
    $scope.cards_fetched = []
    # The autocomplete choice.
    $scope.copy_selected = undefined
    $scope.history = []
    # The cards "inventoried" of the current session: the ones
    # displayed. They must be saved in DB.
    $scope.cards_selected = []
    # All the cards inventoried, even the ones we don't want to show anymore.
    $scope.all = []
    # Boolean to show or hide all the cards (hide by default)
    $scope.showAll = false  # toggled by the checkbox itself.
    $scope.cards_to_show = []
    $scope.name #name of place or basket
    $scope.alerts = []

    $scope.tmpcard = undefined
    # A list of already selected cards' ids
    $scope.selected_ids = []
    existing_card = undefined

    $scope.more_in_inv = {}
    $scope.less_in_inv = {}
    $scope.missing     = {}
    $scope.is_more_in_inv = false
    $scope.is_less_in_inv = false
    $scope.is_missing     = false

    # If we're on page /../inventories/XX/, get info of inventory XX.
    #XXX use angular routing
    $scope.inv_id = utils.url_id($window.location.pathname) # the regexp could include "inventories"
    $scope.language = utils.url_language($window.location.pathname)

    $http.get get_api api_inventory_id_diff
    .then (response) !->
        # $scope.alerts = response.data.msgs
        $scope.diff = response.data.cards
        $scope.name = response.data.name
        $scope.total_copies_in_inv = response.data.total_copies_in_inv
        $scope.total_copies_in_stock = response.data.total_copies_in_stock

        # Cards that are too much in the inventory
        $scope.more_in_inv = $scope.diff
        |> Obj.filter (.diff < 0)
        $scope.is_more_in_inv = ! Obj.empty $scope.more_in_inv
        # Cards that are present in less qty in the inventory
        $scope.less_in_inv = $scope.diff
        |> Obj.filter (.diff > 0)
        $scope.is_less_in_inv = ! Obj.empty $scope.less_in_inv
        # Cards that are missing in the inventory
        # (not a list but an object: id-> card)
        $scope.missing = $scope.diff
        |> Obj.filter (.inv == 0)

        $scope.missing_cost = 0
        for k, v of $scope.missing
            $scope.missing_cost += v.card.price * v.diff
        $scope.missing_cost = $scope.missing_cost.toFixed 2 # round a float

        $scope.is_missing = ! Obj.empty $scope.missing
        # Cards not present initially
        $scope.no_origin = $scope.diff
        |> Obj.filter (.stock == 0)
        $scope.is_no_origin = ! Obj.empty $scope.no_origin

    $scope.obj_length = (obj) ->
        Obj.keys obj .length

    $scope.validate = !->
        sure = confirm "Are you sure to apply this inventory to your stock ?"
        if sure
            $http.post "/api/inventories/#{$scope.inv_id}/apply"
            .then (response) !->
                status = response.data.status
                $scope.alerts = response.data

    $scope.closeAlert = (index) !->
        $scope.alerts.splice index, 1

    # Set focus:
    focus = !->
        angular.element('#default-input').trigger('focus');
    focus()

    $window.document.title = "Abelujo - " + gettext("Terminate inventory") + "-" + $scope.name

]
