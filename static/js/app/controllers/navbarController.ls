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

angular.module "abelujo" .controller 'navbarController', ['$http', '$scope', '$log', 'utils', '$window', ($http, $scope, $log, utils, $window) !->

    {sum, map, filter, find} = require 'prelude-ls'

    $scope.username = undefined
    $scope.cards_fetched = [] # fetched from the autocomplete
    $scope.copy_selected = undefined
    $scope.language = utils.url_language($window.location.pathname)

    $http.get "/api/userinfo"
    .then (response) !->
        $scope.username = response.data.data.username

    $scope.getCards = (query) ->
        args = do
            query: query
            language: $scope.language
            with_quantity: false

        promise = utils.getCards args
        promise.then (res) ->
            $scope.cards_fetched = res
            if utils.is_isbn(query) and res.length == 1
               $scope.go_to_card res[0]
            return res

    $scope.go_to_card = (item) !->
        $log.info item
        card = $scope.cards_fetched
        |> find (.id == item.id)
        card = card.item
        $log.info card
        $window.location.href = card.get_absolute_url

]
