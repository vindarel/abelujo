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

angular.module('abelujo').controller('DepositCreateController', ['$http', '$scope', 'utils', '$window', function ($http, $scope, utils, $window) {
    // set the xsrf token via cookies.
    // $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;
    $scope.dist_list = [];
    $scope.distributor = undefined;
    $scope.copy_selected = undefined;
    $scope.cards_selected = [];
    // Remember the pairs card representation / object from the model.
    $scope.cards_fetched = [];
    $scope.due_date = undefined;

    $scope.deposit_types = [
        {
            name: gettext("fix deposit"),
            target: gettext("deposit of bookshops"),
            type: "fix"
        },
        {
            name: gettext("external deposit (for publisher)"),
            target: gettext("publisher deposit"),
            type: "publisher"
        }
    ];

    $scope.deposit_type = $scope.deposit_types[0];
    $scope.deposit_name = undefined;
    $scope.minimal_nb_copies = 1;
    $scope.auto_command = undefined;

    // messages for ui feedback: list of couple level/message
    $scope.messages = undefined;

    $scope.isDistributorDeposit = function(dep_name) {
        return dep_name === $scope.deposit_types[1].name;
    };

    $http.get("/api/distributors")
        .then(function(response){ // "then", not "success"
            return response.data.map(function(item){
                // give a string representation for each object (result)
                $scope.dist_list.push(item.name);
            });

        });

    $scope.getCards = function(val){
        return $http.get("/api/cards", {
            params: {
                "query": val,
                "distributor": $scope.distributor
            }})
            .then(function(response){ // "then", not "success"
                return response.data.cards.map(function(item){
                    // give a string representation for each object (result)
                    // xxx: take the repr from django
                    // return item.title + ", " + item.authors + ", éd. " + item.publishers;
                    var repr = item.title + ", " + item.authors_repr + ", éd. " + item.pubs_repr;
                    $scope.cards_fetched.push({"repr": repr,
                                               "id": item.id,
                                               "quantity": 1});
                    return {"repr": repr,
                            "id": item.id,
                            "quantity": 1};
                });
            });
    };

    $scope.getPlaces = function() {
        return $http.get("/api/places")
            .then(function(response) {
                $scope.places = response.data;
                $scope.dest_place = $scope.places[0];
                return response.data;
            });
    };

    $scope.getPlaces();

    $scope.addDeposit = function() {

        if (! $scope.depositForm.$valid) {
            return;
        }

        var cards_id = [];
        var cards_qty = [];

        if ($scope.cards_selected.length > 0) {
            // Get the selected card's id,
            cards_id = _.map($scope.cards_selected, function(card) {
                return card.id;
            });
            // and their respective quantities in another array.
            cards_qty = _.map($scope.cards_selected, function(card) {
                return card.quantity;
            });
        }
        var due_date;
        if ($scope.due_date) {
            due_date = $scope.due_date.toString($scope.format);
        }
        var params = {
            "name"              : $scope.deposit_name,
            "distributor"       : $scope.distributor,
            "cards_id"          : cards_id,
            "cards_qty"         : cards_qty,
            "deposit_type"      : $scope.deposit_type.type, //xxx: use sthg else than the name
            "minimal_nb_copies" : $scope.minimal_nb_copies,
            "auto_command"      : $scope.auto_command,
            "dest_place"        : $scope.dest_place.id,
            "due_date"          : due_date

        };
        // needed for Django to process the params to its request.POST dict.
        $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8';

        // We need not to pass the parameters encoded as json to Django.
        // Encode them like url parameters.
        // xxx: put in service
        $http.defaults.transformRequest = utils.transformRequestAsFormPost; // don't transfrom params to json.
        // var config = {
        //     headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        // };

        return $http.post("/api/deposits", params)
            .then(function(response){
                $scope.messages = response.data.messages;
                if (response.data.status == "success") {
                    $scope.cancelCurrentData();
                    $window.location.href = "/deposits/";
                }
                return response.data;
            });
    };

    $scope.cancelCurrentData = function(){
        $scope.deposit_name = "";
        $scope.cards_selected = [];
        $scope.distributor = "";
    };

    $scope.add_selected_card = function(card_repr){
        $scope.cards_selected.unshift(card_repr);
        $scope.cards_fetched = [];
        $scope.copy_selected = undefined;
    };

    $scope.remove_from_selection = function(index_to_rm){
        $scope.cards_selected.splice(index_to_rm, 1);
    };

    /*jshint unused:false */
    $scope.reset_card_list_following_dist = function(dist_name){
        // rather on-select ?
        //TODO: don't rm card if good dist.
        $scope.cards_selected = [];
    };

    $scope.closeAlert = function(index) {
        $scope.messages.splice(index, 1);
    };

    // Watch the change of distributor: we would like to filter out
    // the cards that don't have the right dist.
    $scope.$watch("distributor", function(){
        $scope.cards_selected = _.map($scope.cards_selected, function(card){
            // But we don't have access to the card's details (distributor.name).
            return card;
        });
        // So let's just erase the card list.
        $scope.cards_selected = [];
    });

    //// TODO: refacto with Sell controller and view.
    $scope.formats = ['yyyy-MM-dd', 'yyyy-MM-dd HH:mm:ss', 'dd.MM.yyyy', 'dd-MMMM-yyyy', 'yyyy/MM/dd', 'shortDate'];
    $scope.format = $scope.formats[0];
    $scope.dateOptions = {
        formatYear: 'yy',
        startingDay: 1
    };
   // The date picker:

    $scope.today = function() {
        $scope.date = new Date();
    };
    $scope.today();

    $scope.clear = function () {
        $scope.due_date = null;
    };

    $scope.open = function($event) {
        $event.preventDefault();
        $event.stopPropagation();

        $scope.opened = true;
    };

    // Focus:
    angular.element('#default-input').trigger('focus');

    $window.document.title = "Abelujo - " + gettext("Deposits");

}]);
