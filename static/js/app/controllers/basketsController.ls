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

    {Obj, join, reject, sum, map, filter, lines} = require 'prelude-ls'

    $scope.baskets = []
    $scope.copies = []
    $scope.alerts = []
    $scope.show_buttons = {}
    $scope.new_name = null
    $scope.cur_basket = 0

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
                $scope.copies = response.data.data

        else
            $scope.copies = $scope.cur_basket.copies

    $window.document.title = "Abelujo - " + gettext("Baskets")

    $scope.closeAlert = (index) ->
        $scope.alerts.splice index, 1

    $scope.command = !->
        """Add the copies of the current basket to the Command basket. Api call.
        """
        if not $scope.cur_basket.copies.length
            alert gettext "This basket has no copies to command !"
            return

        sure = confirm gettext("Do you want to mark the cards of the basket '#{$scope.cur_basket.name}' to command ?")
        if sure
            to_add = $scope.cur_basket.copies
            |> map (.id)

            coma_sep = join ",", to_add
            alert to_add

            #  This is needed for Django to process the params to its
            #  request.POST dictionnary:
            $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

            #  We need not to pass the parameters encoded as json to Django.
            #  Encode them like url parameters.
            $http.defaults.transformRequest = utils.transformRequestAsFormPost # don't transfrom params to json.
            config = do
                headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

            params = do
                card_ids = coma_sep
            $http.post "/api/baskets/#{$scope.cur_basket.id}/add/", params
            .then (response) !->
                $scope.alerts = response.data.msgs
                alert "KO"


    $scope.remove_from_selection = (index_to_rm) !->
        "Remove the card from the list. Server call to the api."
        sure = confirm(gettext("Are you sure to remove the card '{}' from the basket ?").replace("{}", $scope.copies[index_to_rm].title))
        if sure
            card_id = $scope.copies[index_to_rm].id
            $http.post "/api/baskets/#{$scope.cur_basket.id}/remove/#{card_id}/",
            .then (response) !->
                $scope.copies.splice(index_to_rm, 1)
                $scope.alerts = response.data.msgs

            .catch (resp) !->
                $log.info "Error when trying to remove the card " + card_id

    $scope.get_data = ->
        # coma-sep list of ids:
        $scope.cur_basket.copies
        |> map (.id)
        |> join ","

    $scope.export_csv = (layout) !->
        """Export the selected cards of the current list to csv.
        Server call to generate it.
        """
        ids_qties = []
        map ->
            ids_qties.push "#{it.id}, 1" #XXX: here we'll need custom quantities
        , $scope.copies

        ###### This is needed for Django to process the params to its
        #  request.POST dictionnary:
        $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

        #  We need not to pass the parameters encoded as json to Django.
        #  Encode them like url parameters.
        $http.defaults.transformRequest = utils.transformRequestAsFormPost # don't transfrom params to json.

        config = do
              headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        ######

        params = do
            # ids and quantities separated by comas
            "ids_qties": join ",", ids_qties
            "format": "csv"
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
