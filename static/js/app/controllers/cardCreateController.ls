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

# Was used for creation and edition.
# Still used for edition. Creation re-done with Django forms.

angular.module "abelujo" .controller 'cardCreateController', ['$http', '$scope', '$window', 'utils', '$filter', '$log', ($http, $scope, $window, utils, $filter, $log) !->
    # utils: in services.js

    # set the xsrf token via cookies.
    # $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;

    {sum, map, filter, lines, find} = require 'prelude-ls'

    $scope.language = utils.url_language($window.location.pathname)

    $scope.authors_selected = []
    $scope.author_input = ""
    $scope.price = 0
    $scope.publishers = []
    $scope.pub_input = ""
    $scope.pubs_selected = []
    $scope.distributor = {}
    $scope.distributor_list = []
    $scope.distributor_selected = undefined
    $scope.has_isbn = false
    $scope.isbn = ""
    $scope.year_published = undefined
    $scope.details_url = undefined
    $scope.title = null
    $scope.threshold = 1

    $scope.type = ""
    $scope.card = {}
    $scope.card_types = []

    $scope.shelf = {"fields": {"pk": 0}}
    $scope.shelfs = []
    $scope.shelf_id = ""

    $scope.alerts = []

    $scope.ready = false

    card_id = utils.url_id($window.location.pathname) # can be null
    $scope.card_created_id = card_id

    if card_id
        $http.get "/api/card/#{card_id}"
        .then (response) ->
            $scope.card = response.data.data
            $scope.title = $scope.card.title
            $scope.price = $scope.card.price
            $scope.authors_selected = $scope.card.authors
            $scope.distributor = $scope.card.distributor
            $scope.isbn = $scope.card.isbn
            $scope.details_url = $scope.card.details_url
            $scope.pubs_selected = $scope.card.publishers
            $scope.shelf = $scope.shelfs
            |> find ( -> it.fields.name == $scope.card.shelf)
            $scope.threshold = $scope.card.threshold

            $scope.alerts = response.data.alerts
            $scope.ready = true # don't load the form if not ready

    else
        $scope.ready = true

    $scope.getItemsApi = (api_url, query, model_selected) ->
        # Fetch the api to api_url with query, store results in model_selected
        $http.get api_url, do
            query: query
        .then (response) ->
            response.data.map (item) ->
                item

    # Get publishers.
    $http.get "/api/publishers"
    .then (response) ->
        $scope.publishers = response.data

    # Get card types
    $http.get "/api/cardtype"
    .then (response) ->
        $scope.card_types = response.data
        $scope.type = $scope.card_types[0]
        response.data

    # Get shelfs
    $http.get "/api/shelfs",
    .then (response) !->
        $scope.shelfs = response.data

    # Distributors
    getDistributors = ->
      utils.distributors!
      .then (response) ->
          $scope.distributor_list = response.data
    getDistributors()

    $scope.add_selected_item = (item, model_input, model_list) ->
        $scope[model_input] = ""
        $scope[model_list].push item

    $scope.remove_from_selection = (index_to_rm, model_list) ->
        $scope[model_list].splice index_to_rm, 1

    # Post the form
    $scope.validate = (next_view) ->

        # all params are optional except the title
        if $scope.shelf
            shelf_id = $scope.shelf.pk

        params = do
            authors: map (.pk), $scope.authors_selected # list of ids
            publishers: [$scope.pubs_selected.pk] # not a list anymore...
            threshold: $scope.threshold

        if card_id
            params.card_id = card_id

        for it in ["title", "year_published", "has_isbn", "price", "isbn", "details_url"]
            if $scope[it]
                params[it] = $scope[it]

        if shelf_id
            params.shelf_id = shelf_id

        type = $scope.type
        if type and type.fields.name is not undefined
            params.type = type.fields.name

        if $scope.distributor_selected != undefined
            params.distributor_id = $scope.distributor_selected.id

        # This is needed for Django to process the params to its
        # request.POST dictionnary:
        $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded charset=UTF-8'

        # We need not to pass the parameters encoded as json to Django.
        # Encode them like url parameters.
        $http.defaults.transformRequest = utils.transformRequestAsFormPost # don't transfrom params to json.
        config = do
            headers: { 'Content-Type': 'application/x-www-form-urlencoded charset=UTF-8'}

        $http.post "/api/cards/create", params
        .then (response) ->
            $scope.alerts = response.data.alerts
            $scope.card_created_id = response.data.card_id
            url = "/#{$scope.language}/stock/card/#{$scope.card_created_id}/"
            if next_view == "view"
               $window.location.href = url

    $scope.closeAlert = (index) ->
        $scope.alerts.splice index, 1


    # Set focus:
    angular.element('#default-input').trigger('focus')

    $window.document.title = "Abelujo - " + gettext("new card")

]
