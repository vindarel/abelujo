angular.module "abelujo" .controller "InventoryModalController", ($http, $scope, $uibModal, $log, utils) !->

    $scope.animationsEnabled = true

    $scope.items = ["item1", "two"]
    $scope.place = "rst"
    $http.get "/api/places"
                    .then (response) !->
                        $scope.items = response.data
                        $scope.place = response.data[0]

    $scope.open = (size) !->
        modalInstance = $uibModal.open do
            animation: $scope.animationsEnabled
            templateUrl: 'modalContent.html'
            controller: 'ModalInstanceCtrl'
            ## backdrop: 'static'
            size: size,
            resolve: do
                items: ->
                    $scope.items
                place: ->
                    $scope.place
                utils: ->
                    utils

        modalInstance.result.then (selectedItem) !->
            $scope.selected = selectedItem
        , !->
              $log.info "modal dismissed"


angular.module "abelujo" .controller "ModalInstanceCtrl", ($http, $scope, $uibModalInstance, places, $window, $log, place, shelf, utils) ->

    $scope.items = items
    $scope.place = place
    $scope.ok = ->
        $uibModalInstance.close()
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
        $uibModalInstance.dismiss('cancel')
