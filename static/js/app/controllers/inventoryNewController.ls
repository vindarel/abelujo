angular.module "abelujo" .controller 'inventoryNewController', ['$http', '$scope', '$timeout', 'utils', '$filter', ($http, $scope, $timeout, utils, $filter) !->
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

    # Set focus:
    angular.element('#default-input').trigger('focus');

]
