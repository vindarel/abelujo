# Copyright 2014 - 2016 The Abelujo Developers
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

angular.module "abelujo" .controller 'CommandsOngoingController', ['$http', '$scope', '$window', 'utils', ($http, $scope, $window, utils) !->

    {Obj, join, reject, sum, map, filter, lines} = require 'prelude-ls'

    $scope.commands = []
    $scope.alerts = []

    $scope.language = utils.url_language($window.location.pathname)
    $scope.commands_url = "/" + $scope.language + "/commands/"

    $http.get("/api/commands/")
    .then (response) ->
        $scope.commands = response.data


]