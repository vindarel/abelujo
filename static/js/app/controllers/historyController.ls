angular.module "abelujo" .controller 'historyController', ['$http', '$scope', '$timeout', '$filter', '$window', 'utils', '$log', 'hotkeys', ($http, $scope, $timeout, $filter, $window, utils, $log, hotkeys) !->

    {Obj, join, sum, map, filter, lines} = require 'prelude-ls'

    $scope.history = []
    $scope.to_show = []
    $scope.filterModel = 'All'
    $scope.alerts = []
    $scope.show_images = true

    params = do
        query: ""
    $http.get "/api/history", do
        params: params
    .then (response) ->
        response.data.data.map (item) !->
            repr = "item n° " + item.id
            $scope.history.push do
                id: item.id
                repr: repr
                item: item
            $scope.to_show = $scope.history
            |> filter (.item.model == 'Entry')

            return do
                repr: repr
                id: item.id

    $scope.filterHistory = (model) !->
        $log.info model
        $scope.to_show = $scope.history
        |> filter (.item.model == model)

    $scope.sellUndo = (index) !->
        sell = $scope.to_show[index]
        $log.info "undo sell #{sell.item.id}"

        sure = confirm gettext "Are you sure to undo this sell ?"
        if sure
            $http.get "/api/sell/#{sell.item.id}/undo"
            .then (response) !->
                $scope.alerts.push response.data.alerts

    $scope.closeAlert = (index) !->
        $scope.alerts.splice index, 1

    $scope.toggle_images = !->
        $scope.show_images = not $scope.show_images

    # Keyboard shortcuts (hotkeys)
    hotkeys.bindTo($scope)
    .add do
        combo: "d"
        description: gettext "show or hide the book details in tables."
        callback: !->
            $scope.toggle_images!

    $window.document.title = "Abelujo - " + gettext("History")

]
