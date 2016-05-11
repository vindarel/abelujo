angular.module "abelujo" .controller 'cardCreateController', ['$http', '$scope', '$window', 'utils', '$filter', ($http, $scope, $window, utils, $filter) !->
    # utils: in services.js

    # set the xsrf token via cookies.
    # $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;

    {sum, map, filter, lines} = require 'prelude-ls'

    $scope.authors_selected = []
    $scope.author_input = ""
    $scope.price = 0
    $scope.pub_input = ""
    $scope.pubs_selected = []
    $scope.distributor = null
    $scope.distributor_list = []
    $scope.distributors_selected = []
    $scope.has_isbn = false
    $scope.isbn = null
    $scope.year_published = undefined
    $scope.details_url = undefined

    $scope.type = ""
    $scope.card = {}
    $scope.card_types = []

    $scope.shelf = {"fields": {"pk": 0}}
    $scope.shelfs = []

    $scope.alerts = []
    $scope.card_created_id = undefined

    $scope.ready = false

    card_id = utils.url_id($window.location.pathname) # can be null
    if card_id
        $http.get "/api/card/#{card_id}"
        .then (response) ->
            $scope.card = response.data.data
            $scope.title = $scope.card.title
            $scope.price = $scope.card.price
            $scope.authors_selected = $scope.card.authors
            $scope.distributor_list = [$scope.card.distributor]
            $scope.distributor = $scope.card.distributor
            $scope.isbn = $scope.card.isbn
            $scope.details_url = $scope.card.details_url
            $scope.pubs_selected = $scope.card.publishers

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

    $scope.refreshDistributors = (search, select) ->
        getDistributors()
        console.log "refreshed distributor_list"
        select.refreshItems()

    # Post the form
    $scope.validate = (next_view) ->

        # all params are optional except the title
        params = do
            title: $scope.title
            price: $scope.price
            shelf: $scope.shelf.pk
            authors: map (.pk), $scope.authors_selected # list of ids
            publishers: map (.pk), $scope.pubs_selected
            year_published: $scope.year_published
            details_url: $scope.details_url
            has_isbn: $scope.has_isbn
            isbn: $scope.isbn

        type = $scope.type
        if type and type.fields.name is not undefined
            params.type = type.fields.name

        distributor = $scope.distributor
        if distributor and distributor.selected is not undefined
            params.distributor = distributor.id

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
            url = "/stock/card/#{$scope.card_created_id}/"
            if next_view == "view"
               $window.location.href = url
            else if next_view == "buy"
                $window.location.href = url + buy

    $scope.closeAlert = (index) ->
        $scope.alerts.splice index, 1


    # Set focus:
    angular.element('#default-input').trigger('focus')

    $window.document.title = "Abelujo - " + gettext("new card")

]
