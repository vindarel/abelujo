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

    $scope.tmpcard = undefined
    # A list of already selected cards' ids
    $scope.selected_ids = []
    existing_card = undefined

    # If we're on page /../inventories/XX/, get info of inventory XX.
    #XXX use angular routing
    $scope.inv_id = utils.url_id($window.location.pathname) # the regexp could include "inventories"
    $scope.language = utils.url_language($window.location.pathname)

    $http.get "/api/inventories/#{$scope.inv_id}/diff/"
    .then (response) !->
        # $scope.alerts = response.data.msgs
        $scope.diff = response.data.cards
        $scope.name = response.data.name

    $scope.validate = !->
        alert gettext "Coming soon !"

    $scope.export_bill = !->
        # The filtering logic of what to pay should be done on the server !
        sold_obj = $scope.diff
        |> Obj.filter (.diff < 0 ) # gives a new object: id -> value
        ids_qties = []
        Obj.map ->
            diff = 0 - it.diff
            ids_qties.push "#{it.card.id}, #{diff}"
        , sold_obj
        ids_qties = join ",", ids_qties

        alerts = utils.export_to ids_qties, "pdf", $scope.name + "-" + gettext("bill"), $scope.language
        if alerts
            $scope.alerts.concat alerts

    # Set focus:
    focus = !->
        angular.element('#default-input').trigger('focus');
    focus()

    $window.document.title = "Abelujo - " + gettext("Terminate inventory") + "-" + $scope.name

]
