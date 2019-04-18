# Copyright 2014 - 2019 The Abelujo Developers
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

angular.module "abelujo" .controller 'cardCommandController', ['$http', '$scope', '$window', 'utils', '$filter', '$log', ($http, $scope, $window, utils, $filter, $log) !->

    {sum, map, filter, lines, find} = require 'prelude-ls'

    $scope.language = utils.url_language($window.location.pathname)

    $scope.card = null
    $scope.clients = []
    $scope.client = null

    $scope.alerts = []

    card_id = utils.url_id($window.location.pathname) # can be null

    $log.info "----------go http"

    $http.get "/api/clients"
    .then (response) !->
          $log.info "clients: ", $scope.clients
          $scope.clients = response.data.data
          $log.info "clients: ", $scope.clients

    $scope.validate = !->
      $log.info "go"

]
