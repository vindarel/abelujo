angular.module "abelujo" .controller 'inventoryTerminateController', ['$http', '$scope', '$timeout', 'utils', '$filter', '$window', ($http, $scope, $timeout, utils, $filter, $window) !->
    # utils: in services.js

    # set the xsrf token via cookies.
    # $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;

    {sum, map, filter, lines, join, Obj} = require 'prelude-ls'

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

    $http.get "/api/inventories/#{$scope.inv_id}/diff/"
    .then (response) !->
        # $scope.alerts = response.data.msgs
        $scope.diff = response.data.cards
        $scope.name = response.data.name

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
        alert gettext "Coming soon !"

    $scope.export_list = (arg) !->
        # The filtering logic of what to pay should be done on the server !
        doc_title = ""
        if arg == 'bill'
            # Cards we sold, that didn't come back.
            sold_obj = $scope.diff
            |> Obj.filter (.diff < 0 ) # gives a new object: id -> value
            ids_qties = []
            Obj.map ->
                diff = 0 - it.diff
                ids_qties.push "#{it.card.id}, #{diff}"
            , sold_obj
            doc_title = gettext "bill"

        if arg == 'inv'
            # Cards of the inventory, that we received.
            obj_list = $scope.diff
            |> Obj.filter (.inv != null)
            ids_qties = []
            Obj.map ->
                ids_qties.push "#{it.card.id}, #{it.inv}"
            , obj_list

        ids_qties = join ",", ids_qties

        # Do the export.
        alerts = utils.export_to ids_qties, "pdf-nobarcode", $scope.name + "-" + doc_title, $scope.language
        if alerts
            $scope.alerts.concat alerts

    # Set focus:
    focus = !->
        angular.element('#default-input').trigger('focus');
    focus()

    $window.document.title = "Abelujo - " + gettext("Terminate inventory") + "-" + $scope.name

]
