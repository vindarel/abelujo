// Copyright 2014 The Abelujo Developers
// See the COPYRIGHT file at the top-level directory of this distribution

// Abelujo is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// Abelujo is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.

angular.module('abelujo.controllers', [])
    .controller('cardCreateController', ['$http', '$scope', 'utils', function ($http, $scope, utils) {

        $scope.authors_selected = [];
        $scope.author_input = "";
        $scope.price = 0;
        $scope.pub_input = "";
        $scope.pubs_selected = [];
        $scope.distributor = null;
        $scope.distributor_list = [];
        $scope.distributors_selected = [];
        $scope.has_isbn = false;
        $scope.isbn = null;
        $scope.year_published = undefined;
        $scope.details_url = undefined;

        $scope.type = "";
        $scope.card_types = [];

        $scope.alerts = [];

        $scope.getItemsApi = function(api_url, query, model_selected){
            return $http.get(api_url, {
                params: {
                    "query": query
                }})
                .then(function(response){
                    return response.data.map(function(item){
                        // give a string representation for each object (result)
                        // $scope.searched_authors.push(item);
                        // $scope[model_selected].push(item);
                        return item;
                    });
                });
        };

        // simply get the list of types: use templating ?
        $http.get("/api/cardtype", {
                params: {
                    "query": ""}
            }).then(function(response){
                $scope.card_types = response.data;
                $scope.type = $scope.card_types[0];
                return response.data;
            });

        $http.get("/api/distributors", {
                params: {
                    "query": ""}
            }).then(function(response){
                $scope.distributor_list = response.data;
                $scope.distributor = $scope.distributor_list[0];
                return response.data;
            });

        $scope.add_selected_item = function(item, model_input, model_list){
            // item: object selected
            // model: name of the input field, to initialize.
            $scope[model_input] = "";
            $scope[model_list].push(item);
      };

        $scope.remove_from_selection = function(index_to_rm, model_list){
            $scope[model_list].splice(index_to_rm, 1);
      };

        $scope.validate = function(){
            console.log("validate clicked");
            var params = {
                "title": $scope.title,
                "price": $scope.price,
                "type": $scope.type.fields.name,
                "authors": _.map($scope.authors_selected, function(it){ return it.pk;}),
                "publishers": _.map($scope.pubs_selected, function(it){ return it.pk;}),
                "distributor": $scope.distributor.id,
                "year_published": $scope.year_published,
                "details_url": $scope.details_url,
                "has_isbn": $scope.has_isbn,
                "isbn": $scope.isbn,
            };
          // This is needed for Django to process the params to its
          // request.POST dictionnary:
          $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8';

          // We need not to pass the parameters encoded as json to Django.
          // Encode them like url parameters.
          $http.defaults.transformRequest = utils.transformRequestAsFormPost; // don't transfrom params to json.
          var config = {
              headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
          };

            return $http.post("/api/cards/create", params)
                .then(function(response){
                    $scope.alerts = response.data.alerts;
                    return response.data;
                });
        };

      //TODO: refactor (sellController)
      $scope.closeAlert = function(index) {
          $scope.alerts.splice(index, 1);
      };

        // Set focus:
        angular.element('#input-title').trigger('focus');
    }]);
