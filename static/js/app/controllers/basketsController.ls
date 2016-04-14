# Copyright 2014 The Abelujo Developers
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

angular.module "abelujo" .controller 'basketsController', ['$http', '$scope', '$timeout', '$filter', '$window', '$uibModal', '$log', 'utils', ($http, $scope, $timeout, $filter, $window, $uibModal, $log, utils) !->

    {Obj, join, reject, sum, map, filter, find, lines} = require 'prelude-ls'

    $scope.baskets = []
    $scope.copies = []
    $scope.alerts = []
    $scope.show_buttons = {}
    $scope.new_name = null
    $scope.cur_basket = 0
    $scope.cards_fetched = [] # fetched from the autocomplete
    $scope.copy_selected = undefined
    COMMAND_BASKET_ID = 1

    $scope.language = utils.url_language($window.location.pathname)

    $http.get "/api/baskets"
    .then (response) ->
        """Get the baskets, do not show the "to command" one, of id=1.
        """
        $scope.baskets = response.data.data
        |> reject (.id == 1)

        $scope.showBasket 0

    $scope.showBasket = (item) !->
        "Show the copies of the given basket."
        $scope.cur_basket = $scope.baskets[item]
        if not $scope.cur_basket.copies
            $http.get "/api/baskets/#{$scope.cur_basket.id}/copies"
            .then (response) !->
                $scope.baskets[item].copies = response.data.data
                $scope.copies = response.data

        else
            $scope.copies = $scope.cur_basket.copies

    $window.document.title = "Abelujo - " + gettext("Baskets")

    $scope.closeAlert = (index) ->
        $scope.alerts.splice index, 1

    $scope.getCards = (term) ->
        params = do
            query: term
            # card_type_id: book only ?
        $http.get "/api/cards/", do
            params: params
        .then (response) ->
            map !->
              repr = "#{it.title}, #{it.authors_repr}, " + gettext("éd.") + " " + it.pubs_repr
              it.basket_qty = 1
              $scope.cards_fetched.push do
                  repr: repr
                  id: it.id
                  item: it
              return do
                repr: repr
                id: it.id
            , response.data
            return $scope.cards_fetched # useful ?

    $scope.add_selected_card = (card_repr) !->
        """ Add the card selected from the autocomplete to the current list's copies.
        Save it.
        """
        tmpcard = $scope.cards_fetched
        |> find (.repr == card_repr.repr)
        tmpcard = tmpcard.item
        $scope.copies.push tmpcard
        $scope.copy_selected = undefined
        # TODO: save
        $scope.save_card_to_basket tmpcard.id, $scope.cur_basket.id

    $scope.save_card_to_basket = (card_id, basket_id) !->
        coma_sep = "#{card_id}"
        params = do
            card_ids: coma_sep
        $http.post "/api/baskets/#{basket_id}/add/", params
        .then (response) !->
            $scope.alerts = response.data.msgs
        , (response) !->
            ... # error

    $scope.save_quantity = (index) !->
        """Save the item quantity.
        """
        card = $scope.copies[index]
        params = do
            id_qty: "#{card.id},#{card.basket_qty}"
        $http.post "/api/baskets/#{$scope.cur_basket.id}/update/", params
        .then (response) !->
            $scope.alerts = response.data.msgs


    $scope.command = !->
        """Add the copies of the current basket to the Command basket. Api call.
        """
        if not $scope.cur_basket.copies.length
            alert gettext "This basket has no copies to command !"
            return

        sure = confirm gettext("Do you want to mark all the cards of this list to command ?")
        if sure
            to_add = $scope.cur_basket.copies
            |> map (.id)

            coma_sep = join ",", to_add # TODO custom quantities
            params = do
                card_ids: coma_sep
            $http.post "/api/baskets/#{COMMAND_BASKET_ID}/add/", params
            .then (response) !->
                $scope.alerts = response.data.msgs


    $scope.remove_from_selection = (index_to_rm) !->
        "Remove the card from the list. Server call to the api."
        sure = confirm(gettext("Are you sure to remove the card '{}' from the basket ?").replace("{}", $scope.copies[index_to_rm].title))
        if sure
            card_id = $scope.copies[index_to_rm].id
            $http.post "/api/baskets/#{$scope.cur_basket.id}/remove/#{card_id}/",
            .then (response) !->
                $scope.copies.splice(index_to_rm, 1)
                # $scope.alerts = response.data.msgs # useless

            .catch (resp) !->
                $log.info "Error when trying to remove the card " + card_id

    $scope.get_data = ->
        # coma-sep list of ids:
        $scope.cur_basket.copies
        |> map (.id)
        |> join ","

    $scope.get_total_price = ->
        sum(map ( -> it.price * it.basket_qty), $scope.copies).toFixed 2 # round a float

    $scope.get_total_copies = ->
        sum(map (.basket_qty), $scope.copies)

    $scope.export_csv = (layout) !->
        """Export the selected cards of the current list to csv.
        Server call to generate it.
        """
        ids_qties = []
        map ->
            ids_qties.push "#{it.id}, #{it.basket_qty}"
        , filter (.basket_qty > 0), $scope.copies

        params = do
            # ids and quantities separated by comas
            "ids_qties": join ",", ids_qties
            "layout": layout
            "list_name": $scope.cur_basket.name

        $http.post "/#{$scope.language}/baskets/export/", params
        .then (response) !->
            # We get raw data. We must open it as a file with JS.
            a = document.createElement('a')
            a.target      = '_blank'
            if layout == 'simple'
                a.href        = 'data:attachment/csv,' +  encodeURIComponent(response.data)
                a.download    = "liste-#{$scope.cur_basket.name}.csv"

            else if layout == 'pdf'
                a.href  = 'data:attachment/pdf,' +  encodeURIComponent(response.data)
                a.download    = "liste-#{$scope.cur_basket.name}.pdf"

            else if layout == 'txt'
                a.href = 'data:attachment/txt,' + encodeURIComponent(response.data)
                a.download    = "liste-#{$scope.cur_basket.name}.txt"

            document.body.appendChild(a)
            a.click()

        , (response) !->
            $scope.alerts = $scope.alerts.concat do
                level: "error"
                message: gettext "We couldn't produce the file, there were an internal error. Sorry !"

    $scope.receive_command = !->
        # Get or create the inventory, redirect to that inventory page
        $http.get "/api/baskets/#{$scope.cur_basket.id}/inventories/"
        .then (response) !->
            inv_id = response.data.data['inv_id']
            # What url scheme ? We want to include the inv id to re-use the inventory controller.
            # baskets/<basket_id>/inventory/<inv id>/, or
            #  /inventories/<inv id>
            # $window.location.href = "/#{$scope.language}/baskets/#{$scope.cur_basket.id}/receive/"
            $window.location.href = "/#{$scope.language}/inventories/#{inv_id}/"

    $scope.open = (size) !->
        modalInstance = $uibModal.open do
            animation: $scope.animationsEnabled
            templateUrl: 'basketModal.html'
            controller: 'BasketModalControllerInstance'
            ## backdrop: 'static'
            size: size,
            resolve: do
                utils: ->
                    utils

        modalInstance.result.then (basket) !->
            $scope.baskets.push basket
        , !->
              $log.info "modal dismissed"

    angular.element('#default-input').trigger('focus');

]

angular.module "abelujo" .controller "BasketModalControllerInstance", ($http, $scope, $uibModalInstance, $window, $log, utils) ->

    $scope.ok = !->
        $log.info "create new basket !"

        #  This is needed for Django to process the params to its
        #  request.POST dictionnary:
        $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

        #  We need not to pass the parameters encoded as json to Django.
        #  Encode them like url parameters.
        $http.defaults.transformRequest = utils.transformRequestAsFormPost # don't transfrom params to json.
        config = do
            headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

        params = do
            name: $scope.new_name

        $http.post "/api/baskets/create", params
        .then (response) !->
            basket = response.data.data
            $scope.alerts = response.data.alerts
            $uibModalInstance.close(basket)


    $scope.cancel = !->
        $uibModalInstance.dismiss('cancel')
