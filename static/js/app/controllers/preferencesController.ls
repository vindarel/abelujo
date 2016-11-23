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

angular.module "abelujo" .controller 'preferencesController', ['$http', '$scope', '$log', 'utils', '$resource', 'hotkeys', ($http, $scope, $log, utils, $resource, hotkeys) !->

    {sum, map, filter, find} = require 'prelude-ls'

    $scope.preferences = {}
    $scope.username = undefined
    $scope.places = []
    $scope.place = undefined
    $scope.vat_book = undefined

    $scope.language_choices =
        * id: "en"
          name: gettext "English"
        * id: "fr"
          name: gettext "French"
        * id: "es"
          name: gettext "Spanish"
        * id: "de"
          name: gettext "German"
    $scope.user_language = $scope.language_choices[0]

    Places = $resource("/api/places/:id")

    Places.query (places) !->
        $scope.places = places

        $http.get "/api/preferences"
        .then (response) !->
            $scope.preferences = response.data.data
            $scope.place = $scope.places
            |> find ( -> it.id == $scope.preferences.default_place.id)
            $scope.place_orig = $scope.place

            $scope.vat_book = $scope.preferences.vat_book

            $scope.user_language = $scope.language_choices
            |> find (.id == $scope.preferences.language)

    $scope.save = (userForm) !->
        if userForm.$valid
            params = do
                place_id: $scope.place.id
                vat_book: $scope.vat_book
                language: $scope.user_language.id
            $http.post "/api/preferences", params
            .then (response) !->
                if response.data.status == "success"
                    $scope.alerts = [{'level': 'success', 'message': gettext "Preferences updated"}]

                else
                    $scope.alerts = [{'level': 'warning', 'message': gettext "There seems to be a problem to save preferences."}]


        else
            $log.info "form is not valid"

    $scope.closeAlert = (index) ->
        $scope.alerts.splice index, 1


]
