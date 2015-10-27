angular.module "abelujo" .controller 'inventoryNewController', ['$http', '$scope', '$timeout', 'utils', '$filter', '$window', ($http, $scope, $timeout, utils, $filter, $window) !->
    # utils: in services.js

    # set the xsrf token via cookies.
    # $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;

    {sum, map, filter, lines} = require 'prelude-ls'

    $scope.copy_selected = undefined
    $scope.history = []
    $scope.cards_selected = []
    $scope.cards_fetched = []
    $scope.tmpcard = undefined
    $scope.selected_ids = []
    existing_card = undefined

    #XXX use angular routing
    re = /inventories\/(\d+)/
    res = $window.location.pathname.match(re)
    if res and res.length == 2
        id = res[1]

        $http.get "/api/inventories/#{id}/"
        .then (response) ->
            response.data.data
            $scope.state = response.data.data
            $scope.cards_fetched = $scope.state.copies
            $scope.selected_ids = map (.id), $scope.state.copies
            $scope.total_missing = $scope.state.total_missing
            $scope.progress_current = $scope.state.total_copies / ($scope.total_missing + $scope.state.total_copies) * 100
            return

    $scope.getCards = (val) ->
        $http.get "/api/cards", do
            params: do
                "query": val
                "card_type_id": null
        .then (response) ->
            response.data.map (item) ->
                repr = "#{item.title}, #{item.authors_repr}, éd #{item.pubs_repr}"
                item.quantity = 1
                $scope.cards_fetched.push do
                    "repr": repr
                    "id": item.id
                    "item": item
                do
                    "repr": repr
                    "id": item.id

    $scope.add_selected_card = (card_repr) ->
        $scope.tmpcard = _.filter $scope.cards_fetched, (it) ->
            it.repr == card_repr.repr
        $scope.tmpcard = $scope.tmpcard[0].item

        if not _.contains $scope.selected_ids, $scope.tmpcard.id
            $scope.cards_selected.push $scope.tmpcard
            $scope.selected_ids.push $scope.tmpcard.id

        else
            existing_card = _.filter $scope.cards_selected, (it) ->
                it.id == $scope.tmpcard.id
            existing_card = existing_card[0]
            existing_card.quantity += 1

        $scope.copy_selected = undefined

    $scope.remove_from_selection = (index_to_rm) ->
        $scope.selected_ids.splice(index_to_rm, 1)
        $scope.cards_selected.splice(index_to_rm, 1)
        $scope.updateTotalPrice()

    $scope.getTotalCopies = ->
        map (.quantity), $scope.cards_selected
        |> sum

    ## $scope.save = ->
        ## ids_qties = map (.id),

    # Set focus:
    angular.element('#default-input').trigger('focus');

]
