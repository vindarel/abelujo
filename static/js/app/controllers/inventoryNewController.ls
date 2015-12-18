angular.module "abelujo" .controller 'inventoryNewController', ['$http', '$scope', '$timeout', 'utils', '$filter', '$window', ($http, $scope, $timeout, utils, $filter, $window) !->
    # utils: in services.js

    # set the xsrf token via cookies.
    # $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;

    {sum, map, filter, lines} = require 'prelude-ls'

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


    $scope.tmpcard = undefined
    # A list of already selected cards' ids
    $scope.selected_ids = []
    existing_card = undefined

    $scope.setCardsToShow = !->
        " Show all the cards inventoried, or the current ones. "
        if $scope.showAll
            $scope.cards_to_show = $scope.all
        else
            $scope.cards_to_show = $scope.cards_selected

    # If we're on page /../inventories/XX/, get info of inventory XX.
    #XXX use angular routing
    re = /inventories\/(\d+)/
    res = $window.location.pathname.match(re)
    if res and res.length == 2
        $scope.inv_id = res[1]

        $http.get "/api/inventories/#{$scope.inv_id}/"
        .then (response) ->
            response.data.data
            $scope.state = response.data.data
            $scope.cards_fetched = $scope.state.copies
            # To show every single card:
            map ->
                # it: has card and quantity properties only.
                $scope.all.push it.card
                $scope.all[* - 1].quantity = it.quantity
            , $scope.state.copies

            $scope.selected_ids = map (.card.id), $scope.state.copies
            $scope.total_missing = $scope.state.total_missing
            #XXX update the progress bar on the fly
            $scope.total_copies = $scope.state.total_copies
            $scope.total_missing = $scope.state.total_missing
            $scope.progress_current = $scope.state.total_copies / ($scope.total_missing + $scope.state.total_copies) * 100
            $scope.updateProgress($scope.total_copies, $scope.total_missing)
            $scope.progressStyle = do
                min-width: 4em
                width: $scope.progress_current + "%"
            return

    $scope.updateProgress = (current, missing) !->
        $scope.progress_current = current / (current + missing) * 100
        $scope.progress_current = $scope.progress_current.toFixed(1)

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

    # Add the choice of the autocomplete.
    # card_repr: the string representation.
    $scope.add_selected_card = (card_repr) !->
        $scope.tmpcard = _.filter $scope.cards_fetched, (it) ->
            it.repr == card_repr.repr
        $scope.tmpcard = $scope.tmpcard[0].item

        if not _.contains $scope.selected_ids, $scope.tmpcard.id
            $scope.cards_selected.push $scope.tmpcard
            $scope.all.push $scope.tmpcard
            $scope.selected_ids.push $scope.tmpcard.id

        else
            # existing_card = _.filter $scope.cards_selected, (it) ->
            existing_card = _.filter $scope.all, (it) ->
                it.id == $scope.tmpcard.id
            existing_card = existing_card[0]
            existing_card.quantity += 1

            # update the cards to display
            if not _.contains $scope.cards_selected, existing_card
                $scope.cards_selected.push existing_card

        $scope.copy_selected = undefined
        $scope.setCardsToShow() # needed for init

    $scope.remove_from_selection = (index_to_rm) !->
        $scope.selected_ids.splice(index_to_rm, 1)
        $scope.cards_selected.splice(index_to_rm, 1)
        $scope.all.splice(index_to_rm, 1)
        focus()

    $scope.getTotalCopies = ->
        map (.quantity), $scope.cards_selected
        |> sum

    $scope.save = ->
        # Send the new copies and quantities to be saved.
        ids_qties = [] # a list of simple types, not list of dicts (see utils service)
        map  ->
            ids_qties.push "#{it.id}, #{it.quantity};"
        , $scope.cards_selected

        #  This is needed for Django to process the params to its
        #  request.POST dictionnary:
        $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

        #  We need not to pass the parameters encoded as json to Django.
        #  Encode them like url parameters.
        $http.defaults.transformRequest = utils.transformRequestAsFormPost # don't transfrom params to json.
        config = do
              headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

        params = do
            "ids_qties": ids_qties
        $http.post "/api/inventories/#{$scope.inv_id}/update/", params
        .then (response) !->
            $scope.alerts = response.data.msgs
            # Update the progress bar.
            $scope.total_missing -= $scope.cards_selected.length
            $scope.total_copies += $scope.cards_selected.length
            $scope.updateProgress($scope.total_copies, $scope.total_missing)
            # Reset the cards to display
            $scope.cards_selected = []
            return response.data.status

    # Set focus:
    focus = !->
        angular.element('#default-input').trigger('focus');
    focus()
]
