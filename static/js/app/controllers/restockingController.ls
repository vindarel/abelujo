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

angular.module "abelujo" .controller 'restockingController', ['$http', '$scope', '$timeout', '$filter', '$window', 'utils', '$log', 'hotkeys', '$resource', ($http, $scope, $timeout, $filter, $window, utils, $log, hotkeys, $resource) !->

    {Obj, join, reject, sum, map, filter, find, lines, sort-by, find-index, reverse, take, group-by, unique-by} = require 'prelude-ls'

    $scope.ignored_cards = {}  # card id => ignored? (bool)
    $scope.cards_ok = {}
    $scope.alerts = []

    $scope.not_implemented = !->
        alert "Not implemented."

    $http.get "/api/restocking/"
    .then (response) !->
        $log.info response
        $scope.cards = response.data

    $scope.ignore_card = (id) ->
        $log.info id
        $scope.ignored_cards[id] = true
        card = document.getElementById(id)
        card.setAttribute('data-card-ok', 'no')
        $log.info "card ok? ", card.getAttribute('data-card-ok')

    $scope.mark_ready = (id) ->
        if $scope.ignored_cards[id]
           $scope.ignored_cards[id] = false
        $scope.cards_ok[id] = true
        card = document.getElementById(id)
        card.setAttribute('data-card-ok', 'yes')
        $log.info "card ok? ", card.getAttribute('data-card-ok')

        $log.info "cards ok: ", $scope.cards_ok

    $scope.remove_card = (id) ->
        $log.info id
        answer = confirm "Are you sure to remove this card from the restocking list, until next time? This action cannot be undone."
        if answer
            $http.post "/api/restocking/remove/#{id}"
            .then (response) !->
                $log.info response
                $scope.alerts = response.data.alerts

    $scope.is_ready = (id) ->
        # Would be as easy with the web api, looking at data-card-ok.
        if $scope.ignored_cards[id] == true
           return false
        return $scope.cards_ok[id]

    $scope.card_ignored = (id) ->
        if $scope.ignored_cards[id]
           $log.info "id int is ignored"
           return true
        sid = id.toString()
        if $scope.ignored_cards[sid]
           $log.info "this id (type string) is ignored"
           return true
        return false

    $scope.validate = !->
        $log.info "validating cards ok: ", $scope.cards_ok
        inputs = document.getElementsByClassName('my-number-input')
        ids = []
        qties = []
        # Select only cards ready.
        for input in inputs
            if input.getAttribute('data-card-ok') == 'yes'
               ids.push(input.getAttribute('data-card-id'))
               qties.push(input.value)
        $log.info "sending: ", ids, qties

        config = do
            headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        params = do
            ids: ids
            qties: qties

        $http.post "/api/restocking/validate", params
        .then (response) !->
            $log.info response
            $scope.alerts = response.data.alerts
            setTimeout( !-> $window.location.pathname = "/restocking"
            , 4000)

    $window.document.title = "Abelujo - " + gettext("Restocking")

]
