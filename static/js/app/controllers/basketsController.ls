angular.module "abelujo" .controller 'basketsController', ['$http', '$scope', '$timeout', '$filter', '$window', '$uibModal', '$log', ($http, $scope, $timeout, $filter, $window, $uibModal, $log) !->

    $scope.baskets = []
    $scope.copies = []

    $http.get "/api/baskets"
    .then (response) ->
        response.data.data.map (item) !->
            $scope.baskets.push item
            if $scope.baskets[0].id
                $scope.showBasket 0

    $scope.showBasket = (item) !->
        cur = $scope.baskets[item]
        if not cur.copies
            $http.get "/api/baskets/#{cur.id}/copies"
            .then (response) !->
                $scope.baskets[item].copies = response.data.data
                $scope.copies = response.data.data

        else
            $scope.copies = cur.copies

    $window.document.title = "Abelujo - " + gettext("Baskets")

    $scope.open = (size) !->
        modalInstance = $uibModal.open do
            animation: $scope.animationsEnabled
            templateUrl: 'commandModal.html'
            controller: 'CommandModalControllerInstance'
            ## backdrop: 'static'
            size: size,
            resolve: do
                cards: ->
                    $scope.copies
                utils: ->
                    utils

        modalInstance.result.then (selectedItem) !->
            $scope.selected = selectedItem
        , !->
              $log.info "modal dismissed"
]

angular.module "abelujo" .controller "CommandModalControllerInstance", ($http, $scope, $uibModalInstance, $window, $log, cards, utils) ->

    {group-by} = require 'prelude-ls'

    $scope.cards = cards
    $scope.sorted_cards = group-by (.distributor.id), $scope.cards

    $scope.ok = ->
        $modalInstance.close()
        $log.info "post new inventory !"

          #  This is needed for Django to process the params to its
          #  request.POST dictionnary:
        $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

          #  We need not to pass the parameters encoded as json to Django.
          #  Encode them like url parameters.
        $http.defaults.transformRequest = utils.transformRequestAsFormPost # don't transfrom params to json.
        config = do
              headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

        params = do
            "place_id": $scope.place.id
        $http.post "/api/inventories/create", params
        .then (response) !->
            $scope.inventory = response.data.data.inventory_id

            if $scope.inventory
                #XXX localization: en, fr,...
                $window.location.href = "/en/inventories/#{$scope.inventory}/"
            #else: display error.

    $scope.cancel = !->
        $modalInstance.dismiss('cancel')
