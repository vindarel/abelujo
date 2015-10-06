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
    .controller('cardCreateController', ['$http', '$scope', 'utils', '$window', function ($http, $scope, utils, $window) {

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
        $scope.card_created_id = undefined;

        // If url ends with an id, we must fetch this card and prefill the "form".
        $scope.ready = false;
        var path = $window.location.pathname;
        // XXX: warning, manual reverse url
        var re = /edit\/(\d+)/;
        var match = path.match(re);

        if (match && match.length == 2) {
            // get the card, populate the form.
            var card_id = match[1];
            $http.get("/api/card/" + card_id, {
                params: {}
            }).then(function(response){
                $scope.card = response.data.data;
                $scope.title = $scope.card.title;
                $scope.price = $scope.card.price;
                $scope.authors_selected = $scope.card.authors;
                $scope.distributor_list = [$scope.card.distributor];
                $scope.distributor = $scope.distributor_list[0];
                $scope.isbn = $scope.card.isbn;
                $scope.details_url = $scope.card.details_url;
                $scope.pubs_selected = $scope.card.publishers;

                $scope.alerts = response.data.alerts;
                $scope.ready = true; // don't load the form if not ready
            });

        } else {

            $scope.ready = true;
        }

        $scope.getItemsApi = function(api_url, query, model_selected){
            // fetch the api to api_url with query, store results in
            // model_selected
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

        $scope.validate = function(next_view){
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
                    $scope.card_created_id = response.data.card_id;
                    // $window.location.href = "/stock/card/"+$scope.card_created_id + "/" + $scope.next_view;
                    if (next_view == "view"){
                        $window.location.href = "/stock/card/" + $scope.card_created_id;
                    }else if (next_view == "buy") {
                        $window.location.href = "/stock/card/" + $scope.card_created_id + "/buy";
                    }
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
