// Application's starting point.

'use strict';

// Declare app level module which depends on filters, and services
angular.module('abelujo', [
    'ngRoute',
    'ngCookies',
    'ngResource',
    'ngSanitize',
    'ngAnimate',
    'ngLocale',
    'tmh.dynamicLocale',
    'ui.router',
    'ui.select',
    'ui.bootstrap',
    'smart-table',
    'datatables',
    'angular-loading-bar',
    'cfp.hotkeys',

    // application level:
    'abelujo.filters',
    'abelujo.services',
    'abelujo.directives',
    'abelujo.controllers'
]);

// Tell the dynamic locale provider where to find translation files.
// (a bit later: for bootstrap datepicker I guess).
// angular.module('abelujo').config(function (tmhDynamicLocaleProvider) {
//     tmhDynamicLocaleProvider.localeLocationPattern('/static/bower_components/angular-i18n/angular-locale_{{locale}}.js');
//     tmhDynamicLocaleProvider.defaultLocale('fr'); // default locale
//     tmhDynamicLocaleProvider.useCookieStorage('NG_TRANSLATE_LANG_KEY');
// });

'use strict';

/* Directives */


angular.module('abelujo.directives', []).
  directive('appVersion', ['version', function(version) {
    return function(scope, elm, attrs) {
      elm.text(version);
    };
  }]);

'use strict';

/* Filters */

angular.module('abelujo.filters', []).
  filter('interpolate', ['version', function(version) {
    return function(text) {
      return String(text).replace(/\%VERSION\%/mg, version);
    };
  }]);

// Copyright 2014 - 2020 The Abelujo Developers
// See the COPYRIGHT file at the top-level directory of this distribution

// Abelujo is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// Abelujo is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.

// You should have received a copy of the GNU Affero General Public License
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
            name: gettext("deposit of bookshops"),
            type: "fix"
        },
        {
            name: gettext("publisher deposit"),
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
                    $window.location.href = "/deposits/" + response.data.data.deposit_id;
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

angular.module("abelujo").controller('alertsController', ['$http', '$scope', '$timeout', 'utils', '$filter', '$window', function ($http, $scope, $timeout, utils, $filter, $window) {
    // utils: in services.js

    $http.get("/api/alerts")
        .then(function(response){
            $scope.alerts = response.data.data;
            return response.data.data;
        });

    $scope.print_ambiguous = function(i) {
        if ($scope.alerts[i].card.ambiguous_sell === false) {
            return gettext("not any more");
        }
        return gettext("yes");
    };

    $window.document.title = "Abelujo - " + gettext("Alerts");

  }]);

angular.module("abelujo").controller('sellController', ['$http', '$scope', '$timeout', 'utils', '$filter', '$window', '$log', function ($http, $scope, $timeout, utils, $filter, $window, $log) {
    // utils: in services.js

      $scope.language = utils.url_language($window.location.pathname);

      // set the xsrf token via cookies.
      // $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;
      $scope.dist_list = [];

    // List of clients.
    $scope.clients = [];
    $scope.client = undefined;

    // List of places we can sell from.
    $scope.places = [];
    $scope.place = undefined;


      $scope.distributor = undefined;
      $scope.copy_selected = undefined;
    // List of the cards we're going to sell.
    // Objects augmented with price_orig, quick_discount
      $scope.cards_selected = [];
      // Remember the pairs card representation / object from the model.
      $scope.cards_fetched = [];

    // optional: bon de commande ID.
    $scope.show_bon_de_commande = false;
    $scope.bon_de_commande_id = "";

    // Show the ISBNs not found, and propose to create a new card.
    $scope.isbns_not_found = [];

      // Respect the backend ids.
      $scope.payment_means = [
          {name: gettext("ESPECES"), id:1},
           {name: gettext("CB"), id:3},
           {name: gettext("CHEQUE"), id:2},
           {name: gettext("transfert"), id:5},
           {name: gettext("autre"), id:6},
      ];
      $scope.payment = $scope.payment_means[0];
      $scope.payment_2 = 0;

      $http.get("/api/config/payment_choices")
        .then(function(response) {
            $scope.payment_means = response.data.data;
            $scope.payment = $scope.payment_means[0];
      });

    $scope.discounts = {choices: [],
                        global_discount: null};
    // and store the selected discount in this object.
    // For the first time had pbs with another variable.
    $scope.discounts.choices = [
        {discount: 0,
         name: "0%", // caution. a "" may introduce a bug
         id:1,
        },
        {discount: 5,
         name: "5%",
         id:2
        },
        {discount: 9,
         name: "9%",
         id:3
        },
        {discount: 20,
         name: "20%",
         id:4
        },
        {discount: 30,
         name: "30%",
         id:5}
    ];

      // $scope.tmpcard = undefined;
      $scope.tmpcard = [];
      $scope.selected_ids = [];
      $scope.total_price = 0;
      $scope.total_payment_1 = 0;
      $scope.show_payment_2 = false;
      $scope.total_payment_2 = 0;

      // messages for ui feedback: list of couple level/message
      $scope.alerts = undefined;

      // Other variables.
      $scope.all_digits_re = /^\d+$/;


      $http.get("/api/preferences")
        .then(function(response) {
            $scope.preferences = response.data.all_preferences;
      });

      $http.get("/api/distributors")
          .then(function(response){ // "then", not "success"
              return response.data.map(function(item){
                  // give a string representation for each object (result)
                  $scope.dist_list.push(item.name);
              });

          });

    $scope.getClients = function(val) {
        return $http.get("/api/clients", {
            params: {
                query: val,
                check_reservations: true
            }
        })
            .then(function(response) {
                // $scope.clients = [{"name": "", "id": 0}];
                // $scope.clients = $scope.clients.concat(response.data.data);
                return response.data.data;
            });
    };

    $scope.select_client = function(item) {
        $scope.client = item;
        $log.info("-- client: ", item);
        // If client has a default discount, apply it.
        if (item.discount > 0) {
            let discount = _.find($scope.discounts.choices, {'discount': item.discount});
            $log.info("-- found: ", discount);
            if (discount) {
                // TODO: apply the discount automatically.
                // $scope.discounts.global_discount = discount;
                // $scope.discount_global();
                // For now, just show an alert we should apply it:
                Notiflix.Notify.Info(gettext("Discount: ") + discount.name);
            } else {
                Notiflix.Notify.Warning("La remise de ce client n'est pas valable.");
            }
        }
    };

    $http.get("/api/places")
        .then(function(response) {
            $scope.places = [{"name": "", "id": 0}];
            $scope.places = $scope.places.concat(response.data);
        });

      // Fetch cards for the autocomplete.
      // Livescript version: see basketsController.ls
      $scope.getCards = function(val){

          // We want to wait for a complete ISBN input,
          // but we also want to search for "1984" when the user types it.
          // It's ok if we don't filter out everything, the important is everyday use.
          if ($scope.all_digits_re.test(val)) {
              if (!val.startsWith('97') |  // book
                  !val.startsWith('313'))  // game
              {
                  // this is not an ISBN
              }
              else if (val.length < 13) {
                  return;
              }
          };

          var place_id = 0;
          if ($scope.place) {
              place_id = $scope.place.id;
          }

          return $http.get("/api/cards", {
              params: {
                  "query": val,
                  "lang": $scope.language,
                  "language": $scope.language,
                  "place_id": place_id
              }})

              .then(function(response){ // "then", not "success"
                  // map over the results and return a list of card objects.
                  var resp = response.data.cards.map(function(item){
                      // give a string representation for each object (result)
                      // xxx: take the repr from django
                      // return item.title + ", " + item.authors + ", éd. " + item.publishers;
                      var repr = item.title + ", " + item.authors_repr + ", éd. " + item.pubs_repr;
                      item.quantity_sell = 1;
                      $scope.cards_fetched.push({"repr": repr,
                                                 "id": item.id,
                                                 "item": item});

                      return {"repr": repr, "id": item.id};
                  });

                  if (utils.is_isbn(val) && resp.length == 1) {
                      $scope.add_selected_card(resp[0]);
                      $window.document.getElementById("default-input").value = "";
                      return [];
                  }

                  if (utils.is_isbn(val) && resp.length == 0) {
                      Notiflix.Notify.Warning("ISBN not found: " + val);
                      $scope.isbns_not_found.push(val);
                      $window.document.getElementById('default-input').value = "";
                  }

                  return resp;
              });
      };

      $scope.add_selected_card = function(card){
          // Find the card.
          // $scope.cards_selected.push(card);
          $scope.tmpcard = _.filter($scope.cards_fetched, function(it){
              return it.repr === card.repr;
          }) ;
          $scope.tmpcard = $scope.tmpcard[0].item;
          $scope.tmpcard.price_orig = $scope.tmpcard.price_sold;
          if (!_.contains($scope.selected_ids, $scope.tmpcard.id)) {
              $scope.cards_selected.unshift($scope.tmpcard);
              $scope.total_price += $scope.tmpcard.price;
              $scope.selected_ids.push($scope.tmpcard.id);
          } else {
              var existing = _.find($scope.cards_selected, function(it){
                  return it.id === card.id;
              });
              existing.quantity_sell += 1;
          }
          $scope.copy_selected = undefined;
          $scope.updateTotalPrice();
          $scope.alerts = [];

          $scope.update_from_datasource($scope.tmpcard);

          // Prevent from quitting the page when sells are entered but not confirmed.
          $window.addEventListener('beforeunload', unloadlistener);
      };

    $scope.import_reservations = function(import_all) {
        /// Import this client's ongoing reservations into the sell.
        // $scope.cards_selected += [];
        let params = {
            "client_id": $scope.client.id,
            // "in_stock": true,  // only cards with quantity > 0
        };
        if (import_all == 0) {
            params['in_stock'] = true;
        }
        $http.get("/api/card/reserved/", {
            params: params})
            .then(function(response) {
                console.log(response);
                $scope.cards_selected = response.data.data;
                $scope.updateTotalPrice();
            });
        $scope.focus_input();
    };

    $scope.update_from_datasource = function(card) {
        // Check if the public price changed.
        return $http.get("/api/cards/update", {
            params: {
                "lang": $scope.language,
                "language": $scope.language,
                "card_id": card.id,
            }})
            .then(function(response){
                let price_alert = response.data.price_alert;
                var existing = _.find($scope.cards_selected, function(it) {
                    return it.id === card.id;
                });
                existing.price_alert = price_alert;
                if (price_alert.price_was_checked) {
                    if (price_alert.price_changed) {
                        existing.price = price_alert.updated_price;
                        existing.price_sold = price_alert.updated_price;
                        $scope.updateTotalPrice();
                        Notiflix.Notify.Success('Prix mis à jour pour ' + existing.title);
                    }
                }
            });
    };

      $scope.remove_from_selection = function(index_to_rm){
          $scope.selected_ids.splice(index_to_rm, 1);
          $scope.cards_selected.splice(index_to_rm, 1);
          $scope.updateTotalPrice();

          // If no sells anymore, don't protect leaving the page anymore.
          if ($scope.cards_selected.length == 0) {
              $window.removeEventListener('beforeunload', unloadlistener);
          }
      };

      $scope.remove_isbn_not_found = function(index) {
          $scope.isbns_not_found.splice(index, 1);
      };

      $scope.reset_card_list_following_dist = function(dist_name){
          // rather on-select ?
          //TODO: don't rm card if good dist.
          $scope.cards_selected = [];
      };

      $scope.closeAlert = function(index) {
          $scope.alerts.splice(index, 1);
      };


    $scope.updateTotalPrice = function() {
        $scope.total_price = _.reduce($scope.cards_selected,
                                      function(memo, it) {
                                          return memo + (it.price_sold * it.quantity_sell);},
                                      0);
        $scope.total_price = $scope.total_price.toFixed(2); // round the float
        $scope.total_payment_1 = parseFloat($scope.total_price);
        console.log("total_payment_1: ", $scope.total_payment_1, "type: ", typeof($scope.total_payment_1));
    };

    $scope.getTotalCopies = function(){
        return _.reduce($scope.cards_selected,
                        function(memo, it){
                            return memo + Math.abs(it.quantity_sell);
                        },
                        0);
    };

    $scope.discount_apply = function(index){
        var price_sold;
        price_sold = $scope.cards_selected[index].price_orig;
        $scope.cards_selected[index].price_sold = price_sold - price_sold * $scope.cards_selected[index].quick_discount.discount / 100;

        $scope.updateTotalPrice();
    };

    $scope.discount_global = function() {
        // Set the same discount to all cards
        var discount = $scope.discounts.global_discount;
        for(var card = 0; card < $scope.cards_selected.length; card++) {
            $scope.cards_selected[card].quick_discount = discount;
            $scope.discount_apply(card);
        }
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

    $scope.sumPrices = function(p1, p2) {
        // Summing decimals has rounding errors. Need to multiply to sum integers.
        return (p1 * 100 + p2 * 100) / 100;
    };

    $scope.sellCardsWith = function(payment) {
        "Register this payment method. When ready, validate the sell."
        console.log("Sell with ", payment);
        let do_sell = false;
        if (! $scope.show_payment_2) {
            // Register first payment method.
            $scope.payment = payment;
            // Check all totals are OK before validating the sell.
            if ($scope.total_payment_1 != $scope.total_price) {
                console.log("Payment is not complete.");
                $scope.show_payment_2 = true;
                // In JS, 10 - 9.9 = 0.099999999964
                $scope.total_payment_2 = ($scope.total_price * 100 - $scope.total_payment_1 * 100) / 100;
            } else {
                console.log("payment 1 OK");
                do_sell = true;
            }
        } else {
            // Register second payment method.
            $scope.payment_2 = payment;
            // Check the two payments sum correctly.
            if (($scope.sumPrices($scope.total_payment_1, $scope.total_payment_2)) != $scope.total_price) {
                alert("La somme des paiements ne correspond pas. Vous pouvez utiliser jusqu'à 2 moyens de paiement différents.");
            } else {
                console.log("-- payments sum OK");
                do_sell = true;
            }
        }
        if (do_sell) {
            $scope.sellCards();
        }
    };

    $scope.sellCards = function() {
        "Validate the Sell. API call."
        var ids = [];
        var prices = [];
        var quantities = [];
        if ($scope.cards_selected.length > 0) {
            ids = _.map($scope.cards_selected, function(card) {
                return card.id;
            });
            prices = _.map($scope.cards_selected, function(card){
                return card.price_sold;
            });
            quantities = _.map($scope.cards_selected, function(card){
                return card.quantity_sell;
            });
        } else {
            return;
        }

        var place_id = 0;
        if ($scope.place) {
            place_id = $scope.place.id;
        }
        $log.info($scope.place);
        var payment_id;
        if ($scope.payment) {
            payment_id = $scope.payment.id;
        }
        var payment_2_id = 0;
        if ($scope.payment_2) {
            payment_2_id = $scope.payment_2.id;
        }
        if (!$scope.total_payment_2) {
            // check against null, when user erases the price manually instead of
            // using the X button.
            $scope.remove_payment_2();
        }

        var params = {
            "to_sell": [ids, prices, quantities],
            "date": $filter('date')($scope.date, $scope.format, 'UTC') .toString($scope.format),
            "language": $scope.language,
            "place_id": place_id,
            "payment_id": payment_id,
            "total_payment_1": $scope.total_payment_1,
        };

        if (payment_2_id && $scope.total_payment_2 != 0) {
            params['payment_2_id'] = payment_2_id;
            params['total_payment_2'] = $scope.total_payment_2;
        }

        if ($scope.bon_de_commande_id != "") {
            params['bon_de_commande_id'] = $scope.bon_de_commande_id;
        }

        if ($scope.client) {
            params['client_id'] = $scope.client.id;
        }

          // This is needed for Django to process the params to its
          // request.POST dictionnary:
          $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8';

          // We need not to pass the parameters encoded as json to Django.
          // Encode them like url parameters.
          $http.defaults.transformRequest = utils.transformRequestAsFormPost; // don't transfrom params to json.
          // var config = {
          //     headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
          // };

          return $http.post("/api/sell", params)
              .then(function(response){
                  // Display server messages.
                  $scope.alerts = response.data.alerts;

                  // Remove the alert after 3 seconds:
                  // ok, but the bottom text comes back too abruptely.
                  // $timeout(function(){
                      // $scope.alerts.splice($scope.alerts.indexOf(alert), 1);
                  // }, 3000); // maybe '}, 3000, false);' to avoid calling apply

                  $scope.cancelCurrentData();
                  $window.removeEventListener('beforeunload', unloadlistener);

                  $scope.payment = $scope.payment_means[0];
                  $window.document.getElementById('client-input').value = "";
                  $scope.client = null;

                  $scope.date = new Date();

                  $scope.focus_input();

                  return response.data;
              });
      };

    $scope.cancelCurrentData = function() {
        $scope.total_price = null;
        $scope.total_payment_1 = null;
        $scope.total_payment_2 = 0;
        $scope.show_payment_2 = false;
        $scope.selected_ids = [];
        $scope.cards_selected = [];
        $scope.cards_fetched = [];
        $scope.client_selected = null;
        $scope.client = null;
        $scope.bon_de_commande_id = "";
        // $scope.show_bon_de_commande = false;
        $scope.focus_input();
    };

    $scope.remove_payment_2 = function() {
        $scope.show_payment_2 = false;
        $scope.total_payment_2 = 0;
        $scope.total_payment_1 = $scope.total_price * 100 / 100;
    };

    $scope.export_csv = function () {
        let date = $filter('date')($scope.date, $scope.format, 'UTC') .toString($scope.format);
        let filename = "Vente " + date + ".csv";
        let text = "";
        let rows = [];
        let total = 0;
        for (var i = 0; i < $scope.cards_selected.length; i++) {
            total += $scope.cards_selected[i].price_sold * $scope.cards_selected[i].quantity_sell;
            let row = $scope.cards_selected[i].title + ';' +
                $scope.cards_selected[i].pubs_repr + ';' +
                $scope.cards_selected[i].price_sold + ';' +
                $scope.cards_selected[i].quantity_sell;
            if ($scope.cards_selected[i].quick_discount) {
                row += ';' + $scope.cards_selected[i].quick_discount.name;
            }
            rows.push(row + '\n');
        }
        // * 100 and / 100: avoid decimial precision errors.
        // 3*21.9 = 38.6999999 lol.
        total = Math.round(total * 100) / 100;
        rows.push("\nTotal;;" + parseFloat(total) + $scope.cards_selected[0].currency + '\n');
        for (var i = 0; i < rows.length; i++) {
            text += rows[i];
        }
        let element = document.createElement('a');
        element.setAttribute('href', 'data:text/csv;charset=utf-8,' + encodeURIComponent(text));
        element.setAttribute('download', filename);
        element.style.display = 'none';
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    };

    $scope.create_bill = function() {
    // $scope.bill_url_params = function() {
        // copied from sell_cards.
        var ids = [];
        var prices = [];
        var prices_sold = [];
        var quantities = [];
        if ($scope.cards_selected.length > 0) {
            ids = _.map($scope.cards_selected, function(card) {
                return card.id;
            });
            prices_sold = _.map($scope.cards_selected, function(card){
                return card.price_sold;
            });
            prices = _.map($scope.cards_selected, function(card){
                return card.price;
            });
            quantities = _.map($scope.cards_selected, function(card){
                return card.quantity_sell;
            });
        } else {
            $log.info("-- no cards selected, won't create a bill!");
            return 0;
        }

        $log.info($scope.place);
        var payment_id;
        if ($scope.payment) {
            payment_id = $scope.payment.id;
        }

        var discount = $scope.discounts.global_discount;

        var params = {
            ids: ids,
            prices_sold: prices_sold,
            prices: prices,
            quantities: quantities,
            date: $filter('date')($scope.date, $scope.format, 'UTC') .toString($scope.format),
            discount: discount,
            language: $scope.language,
            payment_id: payment_id,
            client_id: 0,
            bon_de_commande_id: $scope.bon_de_commande_id,
        };

        var headers = {
            headers: {
                'Content-Type': "application/json",
            }
        };

        if ($scope.client !== undefined) {
            params['client_id'] = $scope.client.id;
            params['language'] = utils.url_language($window.location.pathname);
        }

        $http.post("/api/bill", params, headers)
            .then(function(response){
                if (response.status == 200) {
                    $log.info(response);
                    let element = document.createElement('a');
                    element.setAttribute('href', response.data.fileurl);
                    element.setAttribute('download', response.data.filename);
                    element.style.display = 'none';
                    document.body.appendChild(element);
                    element.click();
                    document.body.removeChild(element);

                    // Second pdf with the books list.
                    // XXX: this opens the same PDF twice...
                    // let elt2 = document.createElement('a');
                    // elt2.setAttribute('href', response.data.details_fileurl);
                    // elt2.setAttribute('download', response.data.details_filename);
                    // elt2.style.display = 'none';
                    // document.body.appendChild(elt2);
                    // elt2.click();
                    // document.body.removeChild(elt2);
                }});
    };

    $scope.toggle_show_bon_de_commande = function() {
        $scope.show_bon_de_commande = ! $scope.show_bon_de_commande;
        $log.info($scope.show_bon_de_commande);
    };

    $scope.add_bon_de_command = function() {
        // Add a label to enter a "bon de commande" number.
    };

   // The date picker:

    $scope.today = function() {
        $scope.date = new Date();
    };
    $scope.today();

    $scope.clear = function () {
        $scope.date = null;
    };

    $scope.open = function($event) {
        $event.preventDefault();
        $event.stopPropagation();

        $scope.opened = true;
    };

    $scope.dateOptions = {
        formatYear: 'yy',
        startingDay: 1
    };

    // Usable datejs format for Django.
    // Django will throw a warning: Sell.created received a naive datetime
    // while time zone support is active.
    $scope.formats = ['yyyy-MM-dd HH:mm:ss', 'dd.MM.yyyy', 'dd-MMMM-yyyy', 'yyyy/MM/dd', 'shortDate'];
    $scope.format = $scope.formats[0];

    // Set focus:
    $scope.focus_input = function() {
        angular.element('#default-input').trigger('focus');
    };
    $scope.focus_input();

    $window.document.title = "Abelujo - " + gettext("Sell");

    function unloadlistener (event) {
        // Cancel the event as stated by the standard.
        event.preventDefault();
        // Chrome requires returnValue to be set.
        event.returnValue = '';
    };

    $scope.do_card_command = function(id) {
        utils.card_command(id);
    };

  }]);

var api;
angular.module('abelujo.services', []).value('version', '0.1');
"Simple wrapper around the api to have hardcoded urls in one place.\n\nTo get the results, we still need to get the result of the promise with .then:\n\n```\napi.distributors!\n.then (response) ->\n    $scope.distributors = response.data\n```";
api = angular.module('abelujo.services', []);
api.factory('api', function($http){
  var ref$, Obj, join, reject, sum, map, filter, find, lines;
  ref$ = require('prelude-ls'), Obj = ref$.Obj, join = ref$.join, reject = ref$.reject, sum = ref$.sum, map = ref$.map, filter = ref$.filter, find = ref$.find, lines = ref$.lines;
  return {
    distributors: function(){
      return $http.get("/api/distributors");
    }
  };
});
var utils;
angular.module('abelujo.services', []).value('version', '0.1');
utils = angular.module('abelujo.services', []);
utils.factory('utils', [
  '$http', '$window', '$log', function($http, $window, $log){
    var ref$, Obj, join, reject, sum, map, filter, find, lines, sortBy, reverse, take, uniqueBy, mean, id, each;
    ref$ = require('prelude-ls'), Obj = ref$.Obj, join = ref$.join, reject = ref$.reject, sum = ref$.sum, map = ref$.map, filter = ref$.filter, find = ref$.find, lines = ref$.lines, sortBy = ref$.sortBy, reverse = ref$.reverse, take = ref$.take, uniqueBy = ref$.uniqueBy, mean = ref$.mean, id = ref$.id, each = ref$.each;
    return {
      transformRequestAsFormPost: function(obj){
        var str, p;
        str = [];
        for (p in obj) {
          str.push(encodeURIComponent(p) + "=" + encodeURIComponent(obj[p]));
        }
        return str.join("&");
      },
      url_language: function(url){
        var re, res;
        re = /\/([a-z][a-z])\//;
        res = url.match(re);
        if (res) {
          return res[1];
        }
        return "en";
      },
      locale_language: function(str){
        "Take a short string specifying a language (exple: fr,\nes; taken from the url) and return one that has meaning\nfor angular's $locale.";
        if (str === "fr") {
          return "fr-fr";
        }
        if (str === "es") {
          return "es-es";
        }
        if (str === "de") {
          return "de-de";
        }
        return "en-gb";
      },
      url_id: function(url){
        var re, res;
        re = /\/(\d+)/;
        res = url.match(re);
        if (res && res.length === 2) {
          return res[1];
        }
        return null;
      },
      set_focus: function(){
        angular.element('#default-input').trigger('focus');
      },
      total_price: function(copies){
        return sum(map(function(it){
          return it.price * it.basket_qty;
        }, copies)).toFixed(2);
      },
      total_price_discounted: function(copies){
        return sum(map(function(it){
          return it.price_discounted * it.basket_qty;
        }, copies)).toFixed(2);
      },
      total_price_excl_vat: function(copies){
        return sum(map(function(it){
          return it.price_excl_vat * it.basket_qty;
        }, copies)).toFixed(2);
      },
      total_price_discounted_excl_vat: function(copies){
        return sum(map(function(it){
          return it.price_discounted_excl_vat * it.basket_qty;
        }, copies)).toFixed(2);
      },
      total_copies: function(copies){
        return sum(map(function(it){
          return it.basket_qty;
        }, copies));
      },
      save_quantity: function(card, basket_id, is_box){
        "Save this card in the given basket. Card has a quantity field.";
        var params;
        is_box == null && (is_box = false);
        params = {
          card_id: card.id,
          quantity: card.basket_qty
        };
        if (is_box) {
          params['is_box'] = true;
        }
        $http.post("/api/baskets/" + basket_id + "/update/", params).then(function(response){
          var alerts;
          alerts = response.data.msgs;
        });
      },
      distributors: function(){
        return $http.get("/api/distributors");
      },
      shelfs: function(){
        return $http.get("/api/shelfs");
      },
      best_sells: function(sells){
        "- sells: list of objects, with a .total_sold (see function above)\n- return: the 10 best sells";
        var best_sells;
        best_sells = take(10)(
        reverse(
        sortBy(function(it){
          return it.total_sold;
        })(
        uniqueBy(function(it){
          return it.card_id;
        })(
        sells))));
        return best_sells;
      },
      sells_mean: function(sells){
        "- return the global mean of sells operation: how much in a sell by average.";
        var i$, len$, sell;
        for (i$ = 0, len$ = sells.length; i$ < len$; ++i$) {
          sell = sells[i$];
          sell.total_sell = mean(
          map(fn$)(
          filter(fn1$)(
          sells)));
        }
        return mean(
        map(function(it){
          return it.total_sell;
        })(
        uniqueBy(function(it){
          return it.sell_id;
        })(
        sells)));
        function fn$(it){
          return it.price_sold * it.quantity;
        }
        function fn1$(it){
          return it.sell_id === sell.sell_id;
        }
      },
      getCards: function(args){
        "Search cards, api call. Used in navbar's search, in baskets, etc.args: object with query, language, with_quantity and other keys.Use as a promise:>> promise = utils.getCards args>> promise.then (results) ->$scope.var = results";
        var re, res, ISBN_LENGTH, params, cards_fetched;
        re = /^(\d+)$/;
        res = args.query.match(re);
        ISBN_LENGTH = 13;
        if (!(args.query.startsWith('97') || args.query.startsWith('313'))) {
          "continue";
        } else if (res && res.length === 2 && args.query.length < ISBN_LENGTH) {
          $log.info("Incomplete ISBN.");
          return;
        }
        params = {
          query: args.query,
          language: args.language,
          with_quantity: args.with_quantity
        };
        cards_fetched = [];
        return $http.get("/api/cards/", {
          params: params
        }).then(function(response){
          map(function(it){
            var repr;
            repr = (it.title + ", " + it.authors_repr + ", ") + gettext("éd.") + " " + it.pubs_repr;
            it.basket_qty = 1;
            cards_fetched.push({
              repr: repr,
              id: it.id,
              item: it
            });
            return {
              repr: repr,
              id: it.id
            };
          }, response.data.cards);
          return cards_fetched;
        });
      },
      is_isbn: function(text){
        var reg;
        reg = /^[0-9]{10,13}/g;
        return text.match(reg);
      },
      card_command: function(id){
        var url;
        url = "/api/card/" + id + "/command";
        $http.post(url, {}).then(function(response){
          var elt;
          $log.info(response);
          if (response.data.status === "success") {
            Notiflix.Notify.Success("OK");
            elt = $window.document.getElementById('command' + id);
            elt.innerText = response.data.data.nb;
          } else {
            Notiflix.Notify.Warning("Warning");
          }
        });
      }
    };
  }
]);
angular.module("abelujo").controller("DistributorCreateModalController", function($http, $scope, $modal, $log, utils){
  $scope.animationsEnabled = true;
  $scope.open = function(size){
    var distributorCreateModalInstanceCtrl;
    distributorCreateModalInstanceCtrl = $modal.open({
      animation: $scope.animationsEnabled,
      templateUrl: 'modalContent.html',
      controller: 'DistributorCreateModalInstanceCtrl',
      size: size,
      resolve: {
        utils: function(){
          return utils;
        }
      }
    });
    distributorCreateModalInstanceCtrl.result.then(function(selectedItem){
      $scope.selected = selectedItem;
    }, function(){
      $log.info("modal dismissed");
    });
  };
});
angular.module("abelujo").controller("DistributorCreateModalInstanceCtrl", function($http, $scope, $distributorCreateModalInstanceCtrl, $window, $log, utils){
  $scope.ok = function(){
    var config, params;
    $distributorCreateModalInstanceCtrl.close();
    $log.info("post new distributor !");
    $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8';
    $http.defaults.transformRequest = utils.transformRequestAsFormPost;
    config = {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
      }
    };
    params = {
      "place_id": $scope.place.id
    };
    return $http.post("/api/inventories/create", params).then(function(response){
      $scope.distributor = response.data.data.distributor_id;
      if ($scope.distributor) {
        $window.location.href = "/en/inventories/" + $scope.distributor + "/";
      }
    });
  };
  $scope.cancel = function(){
    $distributorCreateModalInstanceCtrl.dismiss('cancel');
  };
});
angular.module("abelujo").controller("InventoryModalController", function($http, $scope, $uibModal, $log, utils){
  var ref$, sum, map, filter, lines, sort, sortBy;
  ref$ = require('prelude-ls'), sum = ref$.sum, map = ref$.map, filter = ref$.filter, lines = ref$.lines, sort = ref$.sort, sortBy = ref$.sortBy;
  $scope.animationsEnabled = true;
  $scope.data = {};
  $scope.places = [];
  $scope.place = {};
  $scope.shelfs = [];
  $scope.shelf = {};
  $scope.publisher = {};
  $scope.publishers = [];
  $http.get("/api/places").then(function(response){
    $scope.places = response.data;
    $scope.data.places = response.data;
  });
  $http.get("/api/shelfs").then(function(response){
    $scope.shelfs = sortBy(function(it){
      return it.fields.name;
    }, response.data);
    $scope.shelf = $scope.shelfs[0];
  });
  $http.get("/api/publishers/").then(function(response){
    $scope.publishers = sortBy(function(it){
      return it.fields.name;
    }, response.data);
  });
  $scope.open = function(size){
    var modalInstance;
    modalInstance = $uibModal.open({
      animation: $scope.animationsEnabled,
      templateUrl: 'modalContent.html',
      controller: 'ModalInstanceCtrl',
      size: size,
      resolve: {
        places: function(){
          return $scope.places;
        },
        place: function(){
          return $scope.place;
        },
        shelfs: function(){
          return $scope.shelfs;
        },
        shelf: function(){
          return $scope.shelf;
        },
        publishers: function(){
          return $scope.publishers;
        },
        publisher: function(){
          return $scope.publisher;
        },
        utils: function(){
          return utils;
        }
      }
    });
    modalInstance.result.then(function(selectedItem){
      $scope.selected = selectedItem;
    }, function(){
      $log.info("modal dismissed");
    });
  };
});
angular.module("abelujo").controller("ModalInstanceCtrl", function($http, $scope, $uibModalInstance, places, $window, $log, place, shelfs, shelf, publishers, publisher, utils){
  $scope.places = places;
  $scope.place = place;
  $scope.shelfs = shelfs;
  $scope.shelf = shelf;
  $scope.publishers = publishers;
  $scope.publisher = publisher;
  $scope.ok = function(model){
    var language, params;
    $uibModalInstance.close();
    $log.info("post new inventory !");
    language = utils.url_language($window.location.pathname);
    params = {
      place_id: model === 'place' ? $scope.place.id : void 8,
      shelf_id: model === 'shelf' ? $scope.shelf.pk : void 8,
      publisher_id: model === 'publisher' ? $scope.publisher.pk : void 8
    };
    return $http.post("/api/inventories/create", params).then(function(response){
      var inventory_id;
      inventory_id = response.data.data.inventory_id;
      if (inventory_id) {
        $window.location.href = "/" + language + "/inventories/" + inventory_id + "/";
      }
    });
  };
  $scope.cancel = function(){
    $uibModalInstance.dismiss('cancel');
  };
});
angular.module("abelujo").controller('baseController', [
  '$http', '$scope', '$window', '$log', function($http, $scope, $window, $log){
    var ref$, Obj, join, reject, sum, map, filter, lines, path, re, res;
    ref$ = require('prelude-ls'), Obj = ref$.Obj, join = ref$.join, reject = ref$.reject, sum = ref$.sum, map = ref$.map, filter = ref$.filter, lines = ref$.lines;
    $scope.alerts_open = null;
    $scope.auto_command_total = null;
    $scope.restocking_total = null;
    $scope.FEATURE_SHOW_RESERVATION_BUTTON = false;
    $http.get("/api/alerts/open").then(function(response){
      $scope.alerts_open = response.data;
      return response.data.data;
    });
    $http.get("/api/baskets/auto_command/open").then(function(response){
      $scope.auto_command_total = response.data;
      return response.data.data;
    });
    $http.get("/api/commands/nb_ongoing").then(function(response){
      $scope.ongoing_commands_nb = response.data.data;
      return response.data.data;
    });
    $http.get("/api/restocking/nb_ongoing").then(function(response){
      $scope.restocking_total = response.data.data;
      return response.data.data;
    });
    $http.get("/api/reservations/nb_ongoing").then(function(response){
      $scope.client_commands_nb = response.data.data;
      $scope.FEATURE_SHOW_RESERVATION_BUTTON = response.data.FEATURE_SHOW_RESERVATION_BUTTON;
      return response.data.data;
    });
    $scope.url = "";
    path = $window.location.pathname;
    re = RegExp("/([a-z][a-z])/([a-z]+)/?");
    res = path.match(re);
    if (res) {
      $scope.url = res[res.length - 1];
    }
    $scope.highlight_supplier_menu = function(){
      var ref$;
      if ((ref$ = $scope.url) === 'suppliers' || ref$ === 'publishers' || ref$ === 'distributors') {
        return true;
      }
      return false;
    };
  }
]);
angular.module("abelujo").controller('basketToCommandController', [
  '$http', '$scope', '$timeout', 'utils', '$window', '$log', 'hotkeys', function($http, $scope, $timeout, utils, $window, $log, hotkeys){
    var ref$, find, sum, map, filter, lines, groupBy, join, NEWLINE, ESPERLUETTE, AUTO_COMMAND_ID, getCards;
    $log.info("controller: basketToCommandController");
    ref$ = require('prelude-ls'), find = ref$.find, sum = ref$.sum, map = ref$.map, filter = ref$.filter, lines = ref$.lines, groupBy = ref$.groupBy, join = ref$.join;
    NEWLINE = "%0D%0A";
    ESPERLUETTE = "%26";
    AUTO_COMMAND_ID = 1;
    $scope.alerts = [];
    $scope.distributor = {};
    $scope.distributor_id = -1;
    $scope.cards = [];
    $scope.sorted_cards = {};
    $scope.body = "";
    $scope.page = 1;
    $scope.nb_results = 0;
    $scope.page_max = 1;
    $scope.page_size = 200;
    $scope.meta = {
      num_pages: null,
      nb_results: null
    };
    $scope.language = utils.url_language($window.location.pathname);
    $scope.show_images = false;
    $scope.distributor_id = utils.url_id($window.location.pathname);
    if (!$scope.distributor_id) {
      if ($window.location.pathname.endsWith("all")) {
        $scope.distributor_id = "all";
      }
    }
    $log.info($scope.distributor_id);
    if ((ref$ = $scope.distributor_id) !== "0" && ref$ !== "all") {
      $http.get("/api/distributors/" + $scope.distributor_id).then(function(response){
        $scope.distributor = response.data.data;
        $log.info("-- dist: ", response.data.data);
      });
    } else {
      if ($scope.distributor_id === "0") {
        $scope.distributor = {
          name: "No supplier",
          id: 0,
          repr: "No supplier",
          get_absolute_url: ""
        };
      } else if ($scope.distributor_id === "all") {
        $scope.distributor = {
          name: "All cards",
          id: "all",
          repr: "All cards",
          get_absolute_url: ""
        };
      }
    }
    getCards = function(){
      var params;
      params = {
        page: $scope.page,
        page_size: $scope.page_size,
        dist_id: -1
      };
      $http.get("/api/commands/supplier/" + $scope.distributor_id + "/copies", {
        params: params
      }).then(function(response){
        $scope.cards = response.data.data;
        $scope.totals = response.data.totals;
        $scope.meta.num_pages = response.data.num_pages;
        $scope.meta.nb_results = response.data.nb_results;
        $log.info("cards: ", $scope.cards);
        $log.info("-- meta: ", $scope.meta);
      });
    };
    getCards();
    $scope.save_quantity = function(index){
      var card;
      $log.info("--- save_quantity ");
      card = $scope.cards[index];
      $log.info("saving ", card);
      utils.save_quantity(card, AUTO_COMMAND_ID);
    };
    $scope.closeAlert = function(index){
      $scope.alerts.splice(index, 1);
    };
    $scope.get_body = function(){
      "Get the list of cards and their quantities for the email body.";
      var body, i$, ref$, len$, card, total_price, discount, total_discount;
      body = "";
      for (i$ = 0, len$ = (ref$ = $scope.cards).length; i$ < len$; ++i$) {
        card = ref$[i$];
        body += (card.basket_qty + " x " + card.title + " ( " + card.price + " €), " + card.pubs_repr + ", " + card.isbn) + NEWLINE;
      }
      total_price = 0;
      total_price = sum(
      map(function(it){
        return it.price * it.threshold;
      })(
      filter(function(it){
        return it.threshold > 0;
      })(
      $scope.cards)));
      discount = 0;
      discount = $scope.distributor.discount;
      total_discount = total_price - total_price * discount / 100;
      body = body.replace("&", ESPERLUETTE);
      body += NEWLINE + gettext("total price: ") + total_price + " €";
      body += NEWLINE + gettext("total with {}% discount: ").replace("{}", discount) + total_discount + " €";
      body += NEWLINE + gettext("Thank you.");
      $scope.body = body;
      return body;
    };
    $scope.remove_from_selection = function(dist_name, index_to_rm){
      "Remove the card from the list. Server call.";
      var sure, card_id;
      sure = confirm(gettext("Are you sure to remove the card '{}' from the command basket ?").replace("{}", $scope.cards[index_to_rm].title));
      if (sure) {
        card_id = $scope.cards[index_to_rm].id;
        $http.post("/api/baskets/" + AUTO_COMMAND_ID + "/remove/" + card_id + "/").then(function(response){
          $scope.cards.splice(index_to_rm, 1);
        })['catch'](function(resp){
          $log.info("Error when trying to remove the card " + card_id);
        });
      }
    };
    $scope.empty = function(){
      var sure, params;
      sure = confirm(gettext("Are you sure to remove all the cards from the command basket ?"));
      if (sure) {
        params = {
          distributor_id: $scope.distributor_id
        };
        $http.post("/api/baskets/" + AUTO_COMMAND_ID + "/empty/", params).success(function(response){
          Notiflix.Notify.Success("OK");
          $window.location.reload();
        }).error(function(respons){
          Notiflix.Notify.Warning("mmmh");
        });
      }
    };
    $scope.validate_command = function(){
      "Validate the command. We'll wait for it. Remove the list from the ToCommand basket.";
      var cards, ids_qties, params;
      if (confirm(gettext("Do you want to order this command for " + $scope.distributor.name + " ?\nThe cards will be removed from this list."))) {
        $log.info("validate " + $scope.distributor.name);
        cards = $scope.cards;
        ids_qties = [];
        map(function(it){
          return ids_qties.push(it.id + ", " + it.basket_qty);
        }, cards);
        $log.info("card ids_qties: " + ids_qties);
        params = {
          ids_qties: ids_qties,
          distributor_id: $scope.distributor_id,
          foo: 1
        };
        $http.post("/api/commands/create/", params).then(function(response){
          $log.info(response.data);
          if (response.data.status === 'success') {
            $log.info("success !");
            $window.location.href = "/" + $scope.language + "/commands/";
            $scope.cards = [];
          } else {
            $scope.alerts = response.data.alerts;
          }
        });
      }
    };
    $scope.dist_href = function(name){
      $window.location.href = "#" + name;
    };
    $scope.toggle_images = function(){
      $scope.show_images = !$scope.show_images;
    };
    $scope.add_selected_card = function(card_obj){
      var params;
      $log.info("selected: ", card_obj);
      params = {
        language: $scope.language,
        card_id: card_obj.id,
        dist_id: $scope.distributor_id
      };
      $http.post("/api/v2/baskets/" + AUTO_COMMAND_ID + "/add/", {
        params: params
      }).then(function(response){
        var updated_card;
        $log.info("-- card_obj ", card_obj);
        $scope.alerts = response.data.alerts;
        if (response.data.card) {
          updated_card = response.data.card;
          updated_card.basket_qty = 1;
          $log.info("updated_card: ", updated_card);
          return $scope.cards.unshift(updated_card);
        }
      });
    };
    $scope.nextPage = function(){
      if ($scope.page < $scope.meta.num_pages) {
        $scope.page += 1;
        getCards();
      }
    };
    $scope.lastPage = function(){
      $scope.page = $scope.meta.num_pages;
      getCards();
    };
    $scope.previousPage = function(){
      if ($scope.page > 1) {
        $scope.page -= 1;
        getCards();
      }
    };
    $scope.firstPage = function(){
      $scope.page = 1;
      getCards();
    };
    hotkeys.bindTo($scope).add({
      combo: "d",
      description: gettext("show or hide the book details in tables."),
      callback: function(){
        $scope.toggle_images();
      }
    });
    $window.document.title = "Abelujo - " + gettext("To command");
  }
]);
angular.module("abelujo").controller('basketsController', [
  '$http', '$scope', '$timeout', '$filter', '$window', '$uibModal', '$log', 'utils', '$location', 'hotkeys', function($http, $scope, $timeout, $filter, $window, $uibModal, $log, utils, $location, hotkeys){
    var ref$, Obj, join, reject, sum, map, filter, find, lines, sortBy, findIndex, reverse, COMMAND_BASKET_ID, url_match, page_size, params;
    ref$ = require('prelude-ls'), Obj = ref$.Obj, join = ref$.join, reject = ref$.reject, sum = ref$.sum, map = ref$.map, filter = ref$.filter, find = ref$.find, lines = ref$.lines, sortBy = ref$.sortBy, findIndex = ref$.findIndex, reverse = ref$.reverse;
    $scope.baskets = [];
    $scope.copies = [];
    $scope.alerts = [];
    $scope.show_buttons = {};
    $scope.new_name = null;
    $scope.cur_basket = undefined;
    $scope.cards_fetched = [];
    $scope.copy_selected = undefined;
    $scope.show_images = false;
    $scope.selected_client = null;
    COMMAND_BASKET_ID = 1;
    $scope.language = utils.url_language($window.location.pathname);
    url_match = $window.location.pathname.match("/boxes");
    if (url_match && url_match !== null) {
      $scope.boxes_page = true;
    } else {
      $scope.boxes_page = false;
    }
    $scope.showing_notes = false;
    $scope.last_sort = "title";
    $scope.page = 1;
    $scope.page_size = 25;
    $scope.page_sizes = [25, 50, 100, 200];
    $scope.page_max = 1;
    $scope.meta = {
      num_pages: null,
      nb_results: null
    };
    page_size = $window.localStorage.getItem("baskets_page_size");
    if (page_size !== null) {
      $scope.page_size = parseInt(page_size);
    }
    params = {};
    if ($scope.boxes_page) {
      params['boxes'] = true;
    }
    $http.get("/api/baskets", {
      params: params
    }).then(function(response){
      "Get the baskets, do not show the \"to command\" one, of id=1.";
      var hash_basket_id, index;
      $scope.baskets = reject(function(it){
        return it.id === 1;
      })(
      response.data.data);
      hash_basket_id = parseInt($location.hash(), 10);
      index = findIndex(function(it){
        return hash_basket_id === it.id;
      }, $scope.baskets);
      if (!index) {
        index = 0;
      }
      $scope.cur_basket_index = index;
      return $scope.showBasket(index);
    });
    $scope.save_basket = function(){
      var params;
      params = {
        comment: $scope.cur_basket.comment
      };
      $log.info("updating basket " + $scope.cur_basket.id + "…");
      $http.post("/api/baskets/" + $scope.cur_basket.id + "/update/", params).then(function(response){
        var resp;
        return resp = response.data;
      });
    };
    $scope.getCopies = function(index){
      var params;
      if ($scope.cur_basket) {
        params = {
          page_size: $scope.page_size,
          page: $scope.page
        };
        $http.get("/api/baskets/" + $scope.cur_basket.id + "/copies", {
          params: params
        }).then(function(response){
          $scope.baskets[index].copies = response.data.data;
          $scope.meta = response.data.meta;
          $scope.copies = response.data.data;
        });
      }
    };
    $scope.showBasket = function(index){
      "Show the copies of the given basket.";
      $scope.cur_basket = $scope.baskets[index];
      if ($scope.cur_basket) {
        $location.hash($scope.cur_basket.id);
        $window.document.title = "Abelujo - " + gettext("Baskets") + ", " + $scope.cur_basket.name;
        $window.localStorage.setItem('cur_basket_id', $scope.cur_basket.id);
        if (!$scope.cur_basket.copies) {
          $scope.getCopies(index);
        } else {
          $scope.copies = $scope.cur_basket.copies;
        }
        angular.element('#default-input').trigger('focus');
      }
    };
    $scope.empty_basket = function(){
      var sure;
      sure = confirm(gettext("Are you sure to empty this list {}?").replace("{}", $scope.cur_basket.name));
      if (sure) {
        $http.post("/api/baskets/" + $scope.cur_basket.id + "/empty").then(function(response){
          var index;
          index = findIndex(function(it){
            return it.id === $scope.cur_basket.id;
          }, $scope.baskets);
          $scope.baskets[index].copies = [];
          $scope.baskets[index].length = 0;
          $scope.copies = [];
        });
      }
    };
    $scope.do_archive_basket = function(){
      $http.post("/api/baskets/" + $scope.cur_basket.id + "/archive").then(function(response){
        var index;
        index = findIndex(function(it){
          return it.id === $scope.cur_basket.id;
        }, $scope.baskets);
        $scope.baskets.splice(index, 1);
        $scope.showBasket(index);
      });
    };
    $scope.archive_basket = function(){
      var sure;
      sure = confirm(gettext("Are you sure to archive this list {}?").replace("{}", $scope.cur_basket.name));
      if (sure) {
        $scope.do_archive_basket();
      }
    };
    $scope.delete_basket = function(){
      var sure;
      sure = confirm(gettext("You are going to delete the list {}. This can not be undone. Are you sure ?").replace("{}", $scope.cur_basket.name));
      if (sure) {
        $http.post("/api/baskets/" + $scope.cur_basket.id + "/delete").then(function(response){
          var index;
          index = findIndex(function(it){
            return it.id === $scope.cur_basket.id;
          }, $scope.baskets);
          $scope.baskets.splice(index, 1);
          if (index >= $scope.baskets.length) {
            index -= 1;
          }
          $scope.showBasket(index);
        });
      }
    };
    $window.document.title = "Abelujo - " + gettext("Baskets");
    $scope.closeAlert = function(index){
      return $scope.alerts.splice(index, 1);
    };
    $scope.getCards = function(query){
      var args, promise;
      args = {
        query: query,
        language: $scope.language,
        lang: $scope.language
      };
      promise = utils.getCards(args);
      if (promise) {
        return promise.then(function(res){
          $scope.cards_fetched = res;
          if (utils.is_isbn(query) && res.length === 1) {
            setTimeout(function(){
              $window.document.getElementById("default-input").value = "";
              return $scope.add_selected_card(res[0]);
            }, 700);
            return;
          }
          return res;
        });
      }
    };
    $scope.add_selected_card = function(card){
      " Add the card selected from the autocomplete to the current list's copies.\nSave it.";
      var now, tmpcard, existing, index;
      now = luxon.DateTime.local().toFormat('yyyy-LL-dd HH:mm:ss');
      tmpcard = find(function(it){
        return it.repr === card.repr;
      })(
      $scope.cards_fetched);
      if (!tmpcard) {
        $log.warn("we were expecting an existing tmpcard amongst cards_fetched ", $scope.cards_fetched);
        Notiflix.Notify.Warning("Le serveur n'est pas prêt ! Veuillez attendre un instant et ré-essayer, merci.");
        $scope.copy_selected = undefined;
        return;
      }
      tmpcard = tmpcard.item;
      existing = find(function(it){
        return it.id === tmpcard.id;
      })(
      $scope.copies);
      if (existing) {
        existing.basket_qty += 1;
        existing.modified = now;
        index = findIndex(function(it){
          return existing.id === it.id;
        }, $scope.copies);
        if (index) {
          $scope.copies.splice(index, 1);
          $scope.copies.unshift(existing);
        }
      } else {
        tmpcard.modified = now;
        $scope.copies.unshift(tmpcard);
      }
      $scope.copy_selected = undefined;
      $scope.save_card_to_basket(tmpcard.id, $scope.cur_basket.id);
    };
    $scope.save_card_to_basket = function(card_id, basket_id){
      var coma_sep, params;
      coma_sep = card_id + "";
      params = {
        card_ids: coma_sep
      };
      $http.post("/api/baskets/" + basket_id + "/add/", params).then(function(response){
        $log.info("added cards to basket");
      }, function(response){
        Notiflix.Notify.Warning("Something went wrong.");
        throw Error('unimplemented');
      });
    };
    $scope.save_quantity = function(index){
      "Save the item quantity.";
      var card, now, is_box;
      card = $scope.copies[index];
      now = luxon.DateTime.local().toFormat('yyyy-LL-dd HH:mm:ss');
      utils.save_quantity(card, $scope.cur_basket.id, is_box = $scope.boxes_page);
      card.modified = now;
    };
    $scope.command = function(){
      "Add the copies of the current basket to the Command basket. Api call.";
      var text, sure, params;
      if (!confirm(gettext("You didn't set a supplier for this list (menu -> set a supplier). Do you want to carry on ?"))) {
        return;
      }
      if (!$scope.copies.length) {
        alert(gettext("This basket has no copies to command !"));
        return;
      }
      text = gettext("Do you want to mark all the cards of this list to command ?");
      if ($scope.cur_basket.distributor) {
        text += gettext(" They will be associated with the supplier " + $scope.cur_basket.distributor + ".");
      }
      sure = confirm(text);
      if (sure) {
        params = {
          basket_id: $scope.cur_basket.id
        };
        $http.post("/api/baskets/" + COMMAND_BASKET_ID + "/add/", params).then(function(response){
          $scope.alerts = response.data.alerts;
        });
      }
    };
    $scope.remove_from_selection = function(index_to_rm){
      "Remove the card from the list. Server call to the api.";
      var card_id, params;
      card_id = $scope.copies[index_to_rm].id;
      params = {};
      if ($scope.boxes_page) {
        params['is_box'] = true;
      }
      $http.post("/api/baskets/" + $scope.cur_basket.id + "/remove/" + card_id + "/", params).then(function(response){
        $scope.copies.splice(index_to_rm, 1);
      })['catch'](function(resp){
        $log.info("Error when trying to remove the card " + card_id);
      });
    };
    $scope.get_data = function(){
      return join(",")(
      map(function(it){
        return it.id;
      })(
      $scope.cur_basket.copies));
    };
    $scope.get_total_price = function(){
      return utils.total_price($scope.copies);
    };
    $scope.get_total_copies = function(){
      return utils.total_copies($scope.copies);
    };
    $scope.receive_command = function(){
      var sure;
      if (!$scope.cur_basket.distributor) {
        alert("You didn't set a distributor for this basket. Please see the menu Action -> set the supplier.");
        return;
      }
      sure = confirm(gettext("Do you want to receive a command for the supplier '" + $scope.cur_basket.distributor + "' ?"));
      if (sure) {
        $http.get("/api/baskets/" + $scope.cur_basket.id + "/inventories/").then(function(response){
          var inv_id;
          inv_id = response.data.data.inv_id;
          $window.location.href = "/" + $scope.language + "/inventories/" + inv_id + "/";
        });
      }
    };
    $scope.return_to_supplier = function(){
      var sure;
      if (!$scope.cur_basket.distributor) {
        alert("You didn't set a distributor for this basket. Please see the menu Action -> set the supplier.");
        return;
      }
      sure = confirm(gettext("Do you want to return this basket to " + $scope.cur_basket.distributor + " ? This will remove the given quantities from your stock."));
      if (sure) {
        $http.post("/api/baskets/" + $scope.cur_basket.id + "/return").then(function(response){
          $scope.alerts = response.data.alerts;
        });
      }
    };
    $scope.$watch("page_size", function(){
      $window.localStorage.baskets_page_size = $scope.page_size;
      $scope.getCopies($scope.cur_basket_index);
    });
    $scope.nextPage = function(){
      if ($scope.page < $scope.meta.num_pages) {
        $scope.page += 1;
        $scope.getCopies($scope.cur_basket_index);
      }
    };
    $scope.lastPage = function(){
      $scope.page = $scope.meta.num_pages;
      $scope.getCopies($scope.cur_basket_index);
    };
    $scope.previousPage = function(){
      if ($scope.page > 1) {
        $scope.page -= 1;
        $scope.getCopies($scope.cur_basket_index);
      }
    };
    $scope.firstPage = function(){
      $scope.page = 1;
      $scope.getCopies($scope.cur_basket_index);
    };
    $scope.open_new_basket = function(size){
      var modalInstance;
      modalInstance = $uibModal.open({
        animation: $scope.animationsEnabled,
        templateUrl: 'basketModal.html',
        controller: 'BasketModalControllerInstance',
        size: size,
        resolve: {
          utils: function(){
            return utils;
          }
        }
      });
      modalInstance.result.then(function(basket){
        $scope.baskets.unshift(basket);
        $log.info("new basket: ", basket);
        $scope.showBasket(1);
        $scope.cur_basket = basket;
      }, function(){
        $log.info("modal dismissed");
      });
    };
    $scope.add_to_shelf = function(cur_basket_id){
      var modalInstance;
      modalInstance = $uibModal.open({
        animation: $scope.animationsEnabled,
        templateUrl: 'chooseShelfModal.html',
        controller: 'ChooseShelfModalControllerInstance',
        cur_basket_id: cur_basket_id,
        resolve: {
          utils: function(){
            return utils;
          }
        }
      });
      modalInstance.result.then()(function(){
        var basket;
        basket = $scope.baskets[cur_basket_id];
        basket.copies = [];
        $scope.copies = [];
      }, function(){
        $log.info("modal dismissed");
      });
    };
    $scope.add_to_stock = function(cur_basket_id){
      var params, sure;
      params = {
        shelf_id: cur_basket_id
      };
      sure = confirm(gettext("Do you want to add all the cards to your stock?"));
      if (sure) {
        $http.post("/api/baskets/" + cur_basket_id + "/add_to_stock/", params).then(function(response){
          var index;
          if (response.data.status === "success") {
            $scope.alerts = response.data.alerts;
            index = findIndex(function(it){
              return it.id === cur_basket_id;
            }, $scope.baskets);
            $scope.baskets.splice(index, 1);
            if (index >= $scope.baskets.length) {
              index -= 1;
            }
            $scope.showBasket(index);
          } else {
            Notiflix.Notify.Info("Warning: it seems that an error occured.");
          }
        });
      }
    };
    $scope.toggle_images = function(){
      $scope.show_images = !$scope.show_images;
    };
    $scope.sort_by = function(key){
      if ($scope.last_sort === key) {
        $scope.copies = reverse(
        $scope.copies);
      } else {
        $scope.copies = sortBy(function(it){
          return it[key];
        })(
        $scope.copies);
        $scope.last_sort = key;
      }
      $log.info($scope.copies);
    };
    $scope.choose_client_for_bill = function(cur_basket_id, bill_or_estimate){
      "1: bill, 2: estimate";
      var modalInstance;
      $window.localStorage.setItem('checkboxsell', true);
      modalInstance = $uibModal.open({
        animation: $scope.animationsEnabled,
        templateUrl: 'chooseClientModal.html',
        controller: 'ChooseClientModalControllerInstance',
        cur_basket_id: cur_basket_id,
        bill_or_estimate: bill_or_estimate,
        resolve: {
          utils: function(){
            return utils;
          }
        }
      });
      modalInstance.result.then(function(response){
        $window.localStorage.setItem('bill_or_estimate', bill_or_estimate);
      }, function(){
        $log.info("modal dismissed");
      });
    };
    $scope.choose_client_to_sell = function(cur_basket_id){
      var modalInstance;
      modalInstance = $uibModal.open({
        animation: $scope.animationsEnabled,
        templateUrl: 'chooseClientToSellModal.html',
        controller: 'ChooseClientToSellModalControllerInstance',
        cur_basket_id: cur_basket_id,
        resolve: {
          utils: function(){
            return utils;
          }
        }
      });
      modalInstance.result.then(function(response){}, function(){
        $log.info("modal dismissed");
      });
    };
    $scope.choose_client_for_estimate = function(cur_basket_id){
      "1: bill, 2: estimate";
      var modalInstance;
      $window.localStorage.setItem('checkboxsell', false);
      modalInstance = $uibModal.open({
        animation: $scope.animationsEnabled,
        templateUrl: 'chooseClientForEstimateModal.html',
        controller: 'ChooseClientModalControllerInstance',
        cur_basket_id: cur_basket_id,
        resolve: {
          utils: function(){
            return utils;
          }
        }
      });
      modalInstance.result.then(function(response){
        $window.localStorage.setItem('bill_or_estimate', "2");
      }, function(){
        $log.info("modal dismissed");
      });
    };
    hotkeys.bindTo($scope).add({
      combo: "d",
      description: gettext("show or hide the book details in tables."),
      callback: function(){
        $scope.toggle_images();
      }
    }).add({
      combo: "s",
      description: gettext("go to the search box"),
      callback: function(){
        utils.set_focus();
      }
    }).add({
      combo: "n",
      description: gettext("hide or show your notes"),
      callback: function(){
        $scope.showing_notes = !$scope.showing_notes;
      }
    }).add({
      combo: "C",
      description: gettext("Create a new list"),
      callback: function(){
        $scope.open();
      }
    });
  }
]);
angular.module("abelujo").controller("BasketModalControllerInstance", function($http, $scope, $uibModalInstance, $window, $log, utils){
  utils.set_focus();
  $scope.ok = function(){
    var params;
    if (typeof $scope.new_name === "undefined" || $scope.new_name === "") {
      $uibModalInstance.dismiss('cancel');
      return;
    }
    params = {
      name: $scope.new_name
    };
    if ($window.location.pathname.match("/boxes")) {
      params['box'] = true;
    }
    $http.post("/api/baskets/create", params).then(function(response){
      var basket;
      basket = response.data.data;
      $scope.alerts = response.data.alerts;
      $uibModalInstance.close(basket);
    });
  };
  $scope.cancel = function(){
    $uibModalInstance.dismiss('cancel');
  };
});
angular.module("abelujo").controller("ChooseShelfModalControllerInstance", function($http, $scope, $uibModalInstance, $window, $log, utils){
  utils.set_focus();
  $scope.shelves = [];
  $scope.selected_shelf = null;
  $scope.cur_basket_id = $window.localStorage.getItem('cur_basket_id');
  $http.get("/api/shelfs").then(function(response){
    return $scope.shelves = response.data;
  });
  $scope.ok = function(){
    var config, params;
    if (typeof $scope.selected_shelf === "undefined" || $scope.selected_shelf === "") {
      $uibModalInstance.dismiss('cancel');
      return;
    }
    $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8';
    $http.defaults.transformRequest = utils.transformRequestAsFormPost;
    config = {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
      }
    };
    params = {
      shelf_id: $scope.selected_shelf.pk
    };
    $http.post("/api/baskets/" + $scope.cur_basket_id + "/add_to_shelf/", params).then(function(response){
      $scope.alerts = response.data.alerts;
      $uibModalInstance.close();
      $scope.alerts = response.data.alerts;
    });
  };
  $scope.cancel = function(){
    $uibModalInstance.dismiss('cancel');
  };
});
angular.module("abelujo").controller("ChooseClientModalControllerInstance", function($http, $scope, $uibModalInstance, $window, $log, utils){
  utils.set_focus();
  $scope.shelves = [];
  $scope.checkboxsell = $window.localStorage.getItem("checkboxsell");
  $scope.cur_basket_id = $window.localStorage.getItem('cur_basket_id');
  $http.get("/api/clients").then(function(response){
    return $scope.clients = response.data.data;
  });
  $scope.ok = function(){
    var checkboxsell, bill_or_estimate, params;
    if (typeof $scope.selected_client === "undefined" || $scope.selected_client === "") {
      $uibModalInstance.dismiss('cancel');
      Notiflix.Notify.Info(gettext("You didn't select a client."));
      return;
    }
    checkboxsell = $scope.checkboxsell;
    bill_or_estimate = $window.localStorage.getItem('bill_or_estimate');
    if (bill_or_estimate === 1) {
      checkboxsell = false;
    }
    params = {
      client_id: $scope.selected_client.id,
      basket_id: $scope.cur_basket_id,
      language: utils.url_language($window.location.pathname),
      bill_or_estimate: bill_or_estimate,
      checkboxsell: checkboxsell
    };
    $http.post("/api/bill", params).then(function(response){
      var element;
      $scope.alerts = response.data.alerts;
      $uibModalInstance.close();
      $scope.alerts = response.data.alerts;
      if (response.status === 200) {
        element = document.createElement('a');
        element.setAttribute('href', response.data.fileurl);
        element.setAttribute('download', response.data.filename);
        element.style.display = 'none';
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
      }
    });
  };
  $scope.cancel = function(){
    $uibModalInstance.dismiss('cancel');
  };
});
angular.module("abelujo").controller("ChooseClientToSellModalControllerInstance", function($http, $scope, $uibModalInstance, $window, $log, utils){
  var ref$, Obj, join, reject, sum, map, filter, find, lines, sortBy, findIndex, reverse;
  ref$ = require('prelude-ls'), Obj = ref$.Obj, join = ref$.join, reject = ref$.reject, sum = ref$.sum, map = ref$.map, filter = ref$.filter, find = ref$.find, lines = ref$.lines, sortBy = ref$.sortBy, findIndex = ref$.findIndex, reverse = ref$.reverse;
  utils.set_focus();
  $scope.shelves = [];
  $scope.cur_basket_id = $window.localStorage.getItem('cur_basket_id');
  $http.get("/api/clients").then(function(response){
    return $scope.clients = response.data.data;
  });
  $scope.ok = function(){
    var copies, params;
    if (typeof $scope.selected_client === "undefined" || $scope.selected_client === "") {
      $uibModalInstance.dismiss('cancel');
      Notiflix.Notify.Info(gettext("You didn't select a client."));
      return;
    }
    copies = $scope.cur_basket_id;
    params = {
      client_id: $scope.selected_client.id,
      language: utils.url_language($window.location.pathname)
    };
    $http.post("/api/baskets/" + $scope.cur_basket_id + "/sell", params).then(function(response){
      $scope.alerts = response.data.alerts;
      $uibModalInstance.close();
      $scope.alerts = response.data.alerts;
      if (!deepEq$(response.status, 200, '===')) {
        Notiflix.Notify.Info("The sell got an error. We have bee notified.");
      }
      if (response.status === 200) {
        Notiflix.Notify.Success("OK");
      }
    });
  };
  $scope.cancel = function(){
    $uibModalInstance.dismiss('cancel');
  };
});
function deepEq$(x, y, type){
  var toString = {}.toString, hasOwnProperty = {}.hasOwnProperty,
      has = function (obj, key) { return hasOwnProperty.call(obj, key); };
  var first = true;
  return eq(x, y, []);
  function eq(a, b, stack) {
    var className, length, size, result, alength, blength, r, key, ref, sizeB;
    if (a == null || b == null) { return a === b; }
    if (a.__placeholder__ || b.__placeholder__) { return true; }
    if (a === b) { return a !== 0 || 1 / a == 1 / b; }
    className = toString.call(a);
    if (toString.call(b) != className) { return false; }
    switch (className) {
      case '[object String]': return a == String(b);
      case '[object Number]':
        return a != +a ? b != +b : (a == 0 ? 1 / a == 1 / b : a == +b);
      case '[object Date]':
      case '[object Boolean]':
        return +a == +b;
      case '[object RegExp]':
        return a.source == b.source &&
               a.global == b.global &&
               a.multiline == b.multiline &&
               a.ignoreCase == b.ignoreCase;
    }
    if (typeof a != 'object' || typeof b != 'object') { return false; }
    length = stack.length;
    while (length--) { if (stack[length] == a) { return true; } }
    stack.push(a);
    size = 0;
    result = true;
    if (className == '[object Array]') {
      alength = a.length;
      blength = b.length;
      if (first) {
        switch (type) {
        case '===': result = alength === blength; break;
        case '<==': result = alength <= blength; break;
        case '<<=': result = alength < blength; break;
        }
        size = alength;
        first = false;
      } else {
        result = alength === blength;
        size = alength;
      }
      if (result) {
        while (size--) {
          if (!(result = size in a == size in b && eq(a[size], b[size], stack))){ break; }
        }
      }
    } else {
      if ('constructor' in a != 'constructor' in b || a.constructor != b.constructor) {
        return false;
      }
      for (key in a) {
        if (has(a, key)) {
          size++;
          if (!(result = has(b, key) && eq(a[key], b[key], stack))) { break; }
        }
      }
      if (result) {
        sizeB = 0;
        for (key in b) {
          if (has(b, key)) { ++sizeB; }
        }
        if (first) {
          if (type === '<<=') {
            result = size < sizeB;
          } else if (type === '<==') {
            result = size <= sizeB
          } else {
            result = size === sizeB;
          }
        } else {
          first = false;
          result = size === sizeB;
        }
      }
    }
    stack.pop();
    return result;
  }
}
angular.module("abelujo").controller('cardAddController', [
  '$http', '$scope', '$timeout', 'utils', '$filter', '$window', '$log', function($http, $scope, $timeout, utils, $filter, $window, $log){
    var ref$, sum, map, filter, lines, re, card_id, getDistributors;
    ref$ = require('prelude-ls'), sum = ref$.sum, map = ref$.map, filter = ref$.filter, lines = ref$.lines;
    $scope.card = {};
    $scope.ready = false;
    $scope.shelf = {};
    $scope.distributor = {};
    $scope.threshold = 0;
    $scope.places = [];
    $scope.baskets = [];
    $scope.total_places = 0;
    $scope.total_deposits = 0;
    $scope.language = utils.url_language($window.location.pathname);
    $scope.update_total_deposits = function(){
      $scope.total_deposits = sum(
      map(function(it){
        return it.quantity;
      })(
      $scope.deposits));
    };
    re = /(\d)+/;
    card_id = $window.location.pathname.match(re);
    card_id = card_id[0];
    $http.get("/api/card/" + card_id, {
      params: {}
    }).then(function(response){
      $scope.card = response.data.data;
      $scope.threshold = $scope.card.threshold;
      $scope.ready = true;
    });
    getDistributors = function(){
      return $http.get("/api/distributors", {
        params: {
          "query": ""
        }
      }).then(function(response){
        $scope.distributor_list = response.data;
        return response.data;
      });
    };
    getDistributors();
    $http.get("/api/deposits/", {
      params: {}
    }).then(function(response){
      var i$, ref$, len$, dep;
      $scope.deposits = response.data.data;
      for (i$ = 0, len$ = (ref$ = $scope.deposits).length; i$ < len$; ++i$) {
        dep = ref$[i$];
        dep.quantity = 0;
      }
    });
    $http.get("/api/places/", {
      params: {}
    }).then(function(response){
      var i$, ref$, len$, place;
      $scope.places = response.data;
      for (i$ = 0, len$ = (ref$ = $scope.places).length; i$ < len$; ++i$) {
        place = ref$[i$];
        place.quantity = 0;
      }
      $scope.places[0].quantity = 1;
    });
    $http.get("/api/baskets/", {
      params: {}
    }).then(function(response){
      var i$, ref$, len$, it;
      $scope.baskets = response.data.data;
      for (i$ = 0, len$ = (ref$ = $scope.baskets).length; i$ < len$; ++i$) {
        it = ref$[i$];
        it.quantity = 0;
      }
    });
    $http.get("/api/shelfs/", {
      params: {}
    }).then(function(response){
      $scope.shelfs = response.data;
    });
    $scope.validate = function(){
      var config, places_ids_qties, baskets_ids_qties, deposits_ids_qties, params;
      $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8';
      $http.defaults.transformRequest = utils.transformRequestAsFormPost;
      config = {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
      };
      places_ids_qties = [];
      map(function(it){
        return places_ids_qties.push(it.id + ", " + it.quantity);
      }, $scope.places);
      baskets_ids_qties = [];
      map(function(it){
        return baskets_ids_qties.push(it.id + "," + it.quantity);
      }, $scope.baskets);
      deposits_ids_qties = [];
      map(function(it){
        return deposits_ids_qties.push(it.id + "," + it.quantity);
      }, $scope.deposits);
      params = {
        card_id: $scope.card_id,
        distributor_id: $scope.distributor.id,
        places_ids_qties: places_ids_qties,
        deposits_ids_qties: deposits_ids_qties,
        baskets_ids_qties: baskets_ids_qties,
        threshold: $scope.threshold
      };
      if ($scope.shelf.pk) {
        params.shelf_id = $scope.shelf.pk;
      }
      return $http.post("/api/card/" + $scope.card.id + "/add/", params).then(function(response){
        if (response.status === 200) {
          $window.location.href = "/" + $scope.language + "/search#" + $window.location.search;
        }
      });
    };
    angular.element('#default-input').trigger('focus');
    $window.document.title = "Abelujo - " + gettext("Add a card");
  }
]);
angular.module("abelujo").controller('cardCommandController', [
  '$http', '$scope', '$window', 'utils', '$filter', '$log', function($http, $scope, $window, utils, $filter, $log){
    var ref$, sum, map, filter, lines, find, card_id;
    ref$ = require('prelude-ls'), sum = ref$.sum, map = ref$.map, filter = ref$.filter, lines = ref$.lines, find = ref$.find;
    $scope.language = utils.url_language($window.location.pathname);
    $scope.card = null;
    $scope.clients = [];
    $scope.client = null;
    $scope.alerts = [];
    card_id = utils.url_id($window.location.pathname);
    $log.info("----------go http");
    $http.get("/api/clients").then(function(response){
      $log.info("clients: ", $scope.clients);
      $scope.clients = response.data.data;
      $log.info("clients: ", $scope.clients);
    });
    $scope.validate = function(){
      $log.info("go");
    };
  }
]);
angular.module("abelujo").controller('cardCreateController', [
  '$http', '$scope', '$window', 'utils', '$filter', '$log', function($http, $scope, $window, utils, $filter, $log){
    var ref$, sum, map, filter, lines, find, card_id, getDistributors;
    ref$ = require('prelude-ls'), sum = ref$.sum, map = ref$.map, filter = ref$.filter, lines = ref$.lines, find = ref$.find;
    $scope.language = utils.url_language($window.location.pathname);
    $scope.authors_selected = [];
    $scope.author_input = "";
    $scope.price = 0;
    $scope.publishers = [];
    $scope.pub_input = "";
    $scope.pubs_selected = [];
    $scope.distributor = {};
    $scope.distributor_list = [];
    $scope.distributor_selected = undefined;
    $scope.has_isbn = false;
    $scope.isbn = "";
    $scope.year_published = undefined;
    $scope.details_url = undefined;
    $scope.title = null;
    $scope.threshold = 1;
    $scope.type = "";
    $scope.card = {};
    $scope.card_types = [];
    $scope.shelf = {
      "fields": {
        "pk": 0
      }
    };
    $scope.shelfs = [];
    $scope.shelf_id = "";
    $scope.alerts = [];
    $scope.ready = false;
    card_id = utils.url_id($window.location.pathname);
    $scope.card_created_id = card_id;
    if (card_id) {
      $http.get("/api/card/" + card_id).then(function(response){
        $scope.card = response.data.data;
        $scope.title = $scope.card.title;
        $scope.price = $scope.card.price;
        $scope.selling_price = $scope.card.selling_price;
        $scope.authors_selected = $scope.card.authors;
        $scope.distributor = $scope.card.distributor;
        $scope.isbn = $scope.card.isbn;
        $scope.details_url = $scope.card.details_url;
        $scope.pubs_selected = $scope.card.publishers;
        $scope.shelf = find(function(it){
          return it.fields.name === $scope.card.shelf;
        })(
        $scope.shelfs);
        $scope.threshold = $scope.card.threshold;
        $scope.alerts = response.data.alerts;
        return $scope.ready = true;
      });
    } else {
      $scope.ready = true;
    }
    $scope.getItemsApi = function(api_url, query, model_selected){
      return $http.get(api_url, {
        query: query
      }).then(function(response){
        return response.data.map(function(item){
          return item;
        });
      });
    };
    $http.get("/api/publishers").then(function(response){
      return $scope.publishers = response.data;
    });
    $http.get("/api/cardtype").then(function(response){
      $scope.card_types = response.data;
      $scope.type = $scope.card_types[0];
      return response.data;
    });
    $http.get("/api/shelfs").then(function(response){
      $scope.shelfs = response.data;
    });
    getDistributors = function(){
      return utils.distributors().then(function(response){
        return $scope.distributor_list = response.data;
      });
    };
    getDistributors();
    $scope.add_selected_item = function(item, model_input, model_list){
      $scope[model_input] = "";
      return $scope[model_list].push(item);
    };
    $scope.remove_from_selection = function(index_to_rm, model_list){
      return $scope[model_list].splice(index_to_rm, 1);
    };
    $scope.validate = function(next_view){
      var shelf_id, params, i$, ref$, len$, it, type, config;
      if ($scope.shelf) {
        shelf_id = $scope.shelf.pk;
      }
      params = {
        authors: map(function(it){
          return it.pk;
        }, $scope.authors_selected),
        publishers: [$scope.pubs_selected.pk],
        threshold: $scope.threshold
      };
      if (card_id) {
        params.card_id = card_id;
      }
      for (i$ = 0, len$ = (ref$ = ["title", "year_published", "has_isbn", "price", "selling_price", "isbn", "details_url"]).length; i$ < len$; ++i$) {
        it = ref$[i$];
        if ($scope[it]) {
          params[it] = $scope[it];
        }
      }
      if (shelf_id) {
        params.shelf_id = shelf_id;
      }
      type = $scope.type;
      if (type && type.fields.name !== undefined) {
        params.type = type.fields.name;
      }
      if ($scope.distributor_selected !== undefined) {
        params.distributor_id = $scope.distributor_selected.id;
      }
      $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded charset=UTF-8';
      $http.defaults.transformRequest = utils.transformRequestAsFormPost;
      config = {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded charset=UTF-8'
        }
      };
      return $http.post("/api/cards/create", params).then(function(response){
        var url;
        $scope.alerts = response.data.alerts;
        $scope.card_created_id = response.data.card_id;
        url = "/" + $scope.language + "/stock/card/" + $scope.card_created_id + "/";
        if (next_view === "view") {
          return $window.location.href = url;
        }
      });
    };
    $scope.closeAlert = function(index){
      return $scope.alerts.splice(index, 1);
    };
    angular.element('#default-input').trigger('focus');
    $window.document.title = "Abelujo - " + gettext("new card");
  }
]);
angular.module("abelujo").controller('cardReviewsController', [
  '$http', '$scope', '$timeout', '$filter', '$window', '$log', 'utils', '$location', 'hotkeys', function($http, $scope, $timeout, $filter, $window, $log, utils, $location, hotkeys){
    var ref$, Obj, join, reject, sum, map, filter, find, lines, params;
    ref$ = require('prelude-ls'), Obj = ref$.Obj, join = ref$.join, reject = ref$.reject, sum = ref$.sum, map = ref$.map, filter = ref$.filter, find = ref$.find, lines = ref$.lines;
    $scope.language = utils.url_language($window.location.pathname);
    $scope.reviews = [];
    $scope.card_id = utils.url_id($window.location.pathname);
    $log.info($scope.card_id);
    if ($scope.card_id) {
      params = {
        language: $scope.language
      };
      $http.get("/api/card/" + $scope.card_id + "/reviews", {
        ignoreLoadingBar: true
      }).then(function(response){
        $scope.reviews = response.data;
      });
    }
  }
]);
angular.module("abelujo.controllers", []).controller('collectionController', [
  '$http', '$scope', '$timeout', 'utils', '$filter', '$window', '$cookies', '$uibModal', '$log', 'hotkeys', function($http, $scope, $timeout, utils, $filter, $window, $cookies, $uibModal, $log, hotkeys){
    var ref$, Obj, join, sum, map, filter, lines, show_images, page_size, config, get_selected;
    $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;
    ref$ = require('prelude-ls'), Obj = ref$.Obj, join = ref$.join, sum = ref$.sum, map = ref$.map, filter = ref$.filter, lines = ref$.lines;
    $scope.language = utils.url_language($window.location.pathname);
    $scope.query = "";
    $scope.cards = [];
    $scope.first_page_load = true;
    $scope.places = [];
    $scope.place = null;
    $scope.shelfs = [];
    $scope.shelf = null;
    $scope.publisher = null;
    $scope.distributors = [];
    $scope.distributor = null;
    $scope.baskets = [];
    $scope.show_images = true;
    $scope.quantity_choice = null;
    $scope.quantity_choices = [
      {
        name: gettext(" "),
        id: ""
      }, {
        name: "< 0",
        id: "<0"
      }, {
        name: "<= 0",
        id: "<=0"
      }, {
        name: "0",
        id: "0"
      }, {
        name: "> 0",
        id: ">0"
      }, {
        name: "> 1",
        id: ">1"
      }, {
        name: "> 2",
        id: ">2"
      }, {
        name: "> 3",
        id: ">3"
      }, {
        name: gettext("between 1 and 3"),
        id: "[1,3]"
      }, {
        name: gettext("between 1 and 5"),
        id: "[1,5]"
      }, {
        name: gettext("between 3 and 5"),
        id: "[3,5]"
      }, {
        name: gettext("between 5 and 10"),
        id: "[5,10]"
      }, {
        name: gettext("> 10"),
        id: ">10"
      }
    ];
    $scope.price_choice = null;
    $scope.price_choices = [];
    $scope.meta = {};
    $scope.define_price_choices = function(){
      var currency;
      currency = document.getElementById('data-currency').dataset['currency'];
      $scope.meta.currency = currency;
      $scope.price_choices = [
        {
          name: gettext(" "),
          id: ""
        }, {
          name: "0",
          id: "0"
        }, {
          name: "<= 3 " + $scope.meta.currency,
          id: "<=3"
        }, {
          name: "<= 5 " + $scope.meta.currency,
          id: "<=5"
        }, {
          name: "<= 10 " + $scope.meta.currency,
          id: "<=10"
        }, {
          name: "<= 20 " + $scope.meta.currency,
          id: "<=20"
        }, {
          name: gettext("between 0 and 5 " + $scope.meta.currency),
          id: "[0,5]"
        }, {
          name: gettext("between 0 and 10 " + $scope.meta.currency),
          id: "[0,10]"
        }, {
          name: gettext("between 5 and 10 " + $scope.meta.currency),
          id: "[5,10]"
        }, {
          name: gettext("> 5 " + $scope.meta.currency),
          id: ">5"
        }, {
          name: gettext("> 10 " + $scope.meta.currency),
          id: ">10"
        }, {
          name: gettext("> 20 " + $scope.meta.currency),
          id: ">20"
        }
      ];
    };
    $scope.define_price_choices();
    $scope.date_created = null;
    $scope.date_created_sort = "";
    $scope.date_created_sort_choices = [
      {
        name: " ",
        id: ""
      }, {
        name: "<=",
        id: "<="
      }, {
        name: "=",
        id: "="
      }, {
        name: ">=",
        id: ">="
      }
    ];
    $scope.order_by_choices = [
      {
        name: gettext("Most recent created first"),
        id: "-created"
      }, {
        name: gettext("Oldest created first"),
        id: "created"
      }, {
        name: gettext("Titles"),
        id: "title"
      }, {
        name: gettext("Titles") + " ⤵",
        id: "-title"
      }, {
        name: gettext("Price"),
        id: "price"
      }, {
        name: gettext("Price") + " ⤵",
        id: "-price"
      }, {
        name: gettext("Publisher"),
        id: "publisher"
      }, {
        name: gettext("Publisher") + " ⤵",
        id: "-publisher"
      }, {
        name: gettext("Shelf"),
        id: "shelf__name"
      }, {
        name: gettext("Shelf") + " ⤵",
        id: "-shelf__name"
      }
    ];
    $scope.order_by = $scope.order_by_choices[0];
    $scope.page = 1;
    $scope.page_size = 50;
    $scope.page_sizes = [25, 50, 100, 200];
    $scope.page_max = 1;
    show_images = $window.localStorage.getItem("show_images");
    if (show_images !== null) {
      if (show_images === "true") {
        show_images = true;
      } else {
        show_images = false;
      }
      $scope.show_images = show_images;
    }
    page_size = $window.localStorage.getItem("page_size");
    if (page_size !== null) {
      $scope.page_size = parseInt(page_size);
    }
    $scope.selectAll = true;
    $scope.selected = {};
    $scope.alerts = [];
    $scope.card_types = [
      {
        name: gettext("all publication"),
        id: null
      }, {
        name: gettext("book"),
        group: gettext("book"),
        id: 1
      }, {
        name: gettext("booklet"),
        group: gettext("book"),
        id: 2
      }, {
        name: gettext("periodical"),
        group: gettext("book"),
        id: 3
      }, {
        name: gettext("other print"),
        group: gettext("book"),
        id: 4
      }, {
        name: gettext("CD"),
        group: gettext("CD"),
        id: 5
      }, {
        name: gettext("DVD"),
        group: gettext("CD"),
        id: 6
      }, {
        name: gettext("vinyl"),
        group: gettext("CD"),
        id: 8
      }, {
        name: gettext("others"),
        group: gettext("others"),
        id: 9
      }
    ];
    $http.get("/api/places").then(function(response){
      $scope.places = response.data;
      $scope.places.unshift({
        repr: "",
        id: 0
      });
    });
    $http.get("/api/shelfs").then(function(response){
      $scope.shelfs = response.data;
      $scope.shelfs.unshift({
        repr: "",
        id: 0
      });
    });
    $http.get("/api/publishers").then(function(response){
      $scope.publishers = response.data;
    });
    $http.get("/api/distributors").then(function(response){
      $scope.distributors = response.data;
      $scope.distributors.unshift({
        repr: "",
        id: 0
      });
    });
    $scope.validate = function(){
      var params;
      params = {
        query: $scope.query,
        order_by: $scope.order_by.id,
        in_stock: true,
        with_authors: true,
        with_total_sells: true
      };
      if ($scope.publisher) {
        params.publisher_id = $scope.publisher.pk;
      }
      if ($scope.place) {
        params.place_id = $scope.place.id;
      }
      if ($scope.card_type) {
        params.card_type = $scope.card_type;
      }
      if ($scope.shelf) {
        params.shelf_id = $scope.shelf.pk;
      }
      if ($scope.distributor) {
        params.distributor_id = $scope.distributor.id;
      }
      if ($scope.quantity_choice) {
        params.quantity_choice = $scope.quantity_choice.id;
      }
      if ($scope.price_choice) {
        params.price_choice = $scope.price_choice.id;
      }
      if ($scope.date_created) {
        params.date_created = $scope.date_created;
        params.date_created_sort = $scope.date_created_sort.id;
      }
      params.page = $scope.page;
      params.page_size = $scope.page_size;
      $window.localStorage.page_size = $scope.page_size;
      $http.get("/api/cards", {
        params: params
      }).then(function(response){
        $scope.cards = response.data.cards;
        $scope.meta = response.data.meta;
        $window.document.getElementById("default-input").select();
        $scope.first_page_load = false;
      });
    };
    $scope.nextPage = function(){
      if ($scope.page < $scope.meta.num_pages) {
        $scope.page += 1;
        $scope.validate();
      }
    };
    $scope.lastPage = function(){
      $scope.page = $scope.meta.num_pages;
      $scope.validate();
    };
    $scope.previousPage = function(){
      if ($scope.page > 1) {
        $scope.page -= 1;
        $scope.validate();
      }
    };
    $scope.firstPage = function(){
      $scope.page = 1;
      $scope.validate();
    };
    $scope.toggleAll = function(){
      var i$, ref$, len$, elt;
      for (i$ = 0, len$ = (ref$ = $scope.cards).length; i$ < len$; ++i$) {
        elt = ref$[i$];
        $scope.selected[elt.id] = $scope.selectAll;
      }
      $scope.selectAll = !$scope.selectAll;
    };
    utils.set_focus();
    $window.document.title = "Abelujo - " + gettext("Stock");
    $scope.closeAlert = function(index){
      $scope.alerts.splice(index, 1);
    };
    $scope.toggle_images = function(){
      $scope.show_images = !$scope.show_images;
      $window.localStorage.show_images = $scope.show_images;
    };
    $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded charset=UTF-8';
    $http.defaults.transformRequest = utils.transformRequestAsFormPost;
    config = {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded charset=UTF-8'
      }
    };
    get_selected = function(){
      var to_add;
      return to_add = Obj.keys(
      Obj.filter((function(it){
        return it === true;
      }), $scope.selected));
    };
    $scope.add_to_lists = function(size){
      var to_add, modalInstance;
      to_add = get_selected();
      if (!to_add.length) {
        alert("Please select some cards.");
        return;
      }
      modalInstance = $uibModal.open({
        animation: $scope.animationsEnabled,
        templateUrl: 'collectionModal.html',
        controller: 'CollectionModalControllerInstance',
        size: size,
        resolve: {
          selected: function(){
            return $scope.selected;
          },
          utils: function(){
            return utils;
          }
        }
      });
      modalInstance.result.then(function(alerts){
        $scope.alerts = alerts;
        $scope.selected = {};
      }, function(){
        $log.info("modal dismissed");
      });
    };
    $scope.set_supplier = function(card){
      var cards_ids, params;
      cards_ids = get_selected();
      if (!cards_ids.length) {
        alert("Please select some cards.");
        return;
      }
      params = {
        cards_ids: join(",", cards_ids)
      };
      $http.post("/api/cards/set_supplier", params).then(function(response){
        var card_id;
        $log.info("--- done");
        card_id = response.data.card_id;
        $log.info($window.location.pathname);
        $log.info(response.data.url);
        $window.location.pathname = $scope.language + response.data.url;
      }, function(response){
        return $log.info("--- error ", response.status, response.statusText);
      });
    };
    $scope.set_shelf = function(card){
      var cards_ids, params;
      cards_ids = get_selected();
      if (!cards_ids.length) {
        alert("Please select some cards.");
        return;
      }
      params = {
        cards_ids: join(",", cards_ids)
      };
      $http.post("/api/cards/set_shelf", params).then(function(response){
        var card_id;
        $log.info("--- done");
        card_id = response.data.card_id;
        $log.info($window.location.pathname);
        $log.info(response.data.url);
        $window.location.pathname = $scope.language + response.data.url;
      }, function(response){
        return $log.info("--- error ", response.status, response.statusText);
      });
    };
    $scope.do_card_command = function(id){
      utils.card_command(id);
    };
    hotkeys.bindTo($scope).add({
      combo: "d",
      description: gettext("show or hide the book details in tables."),
      callback: function(){
        $scope.toggle_images();
      }
    }).add({
      combo: "s",
      description: gettext("go to the search box"),
      callback: function(){
        utils.set_focus();
      }
    });
  }
]);
angular.module("abelujo").controller("CollectionModalControllerInstance", function($http, $scope, $uibModalInstance, $window, $log, utils, selected){
  var ref$, Obj, join, sum, map, filter, lines;
  ref$ = require('prelude-ls'), Obj = ref$.Obj, join = ref$.join, sum = ref$.sum, map = ref$.map, filter = ref$.filter, lines = ref$.lines;
  $scope.selected_baskets = {};
  $scope.alerts = [];
  $http.get("/api/baskets").then(function(response){
    $scope.baskets = response.data.data;
  });
  $scope.ok = function(){
    var to_add, coma_sep, baskets_ids, params, i$, len$, b_id;
    to_add = Obj.keys(
    Obj.filter((function(it){
      return it === true;
    }), selected));
    coma_sep = join(",", to_add);
    baskets_ids = Obj.keys(
    Obj.filter(function(it){
      return it === true;
    })(
    $scope.selected_baskets));
    params = {
      card_ids: coma_sep
    };
    for (i$ = 0, len$ = baskets_ids.length; i$ < len$; ++i$) {
      b_id = baskets_ids[i$];
      $log.info("Adding cards to basket " + b_id + "...");
      $http.post("/api/baskets/" + b_id + "/add/", params).then(fn$);
    }
    $uibModalInstance.close($scope.alerts);
    function fn$(response){
      $scope.alerts = $scope.alerts.concat(response.data.msgs);
    }
  };
  $scope.cancel = function(){
    $uibModalInstance.dismiss('cancel');
  };
});
angular.module("abelujo").controller('CommandReceiveController', [
  '$http', '$scope', '$timeout', 'utils', '$filter', '$window', 'hotkeys', '$log', function($http, $scope, $timeout, utils, $filter, $window, hotkeys, $log){
    var ref$, sum, map, filter, lines, reverse, join, reject, round, existing_card;
    ref$ = require('prelude-ls'), sum = ref$.sum, map = ref$.map, filter = ref$.filter, lines = ref$.lines, reverse = ref$.reverse, join = ref$.join, reject = ref$.reject, round = ref$.round;
    $scope.cards_fetched = [];
    $scope.copy_selected = undefined;
    $scope.history = [];
    $scope.cards_selected = [];
    $scope.all = [];
    $scope.showAll = false;
    $scope.cards_to_show = [];
    $scope.total_value = 0;
    $scope.nb_cards = 0;
    $scope.nb_copies = 0;
    $scope.tmpcard = undefined;
    $scope.selected_ids = [];
    existing_card = undefined;
    $scope.inv_id = utils.url_id($window.location.pathname);
    $scope.cur_inv = "the parcel of a command !";
    $scope.progress_current = 0;
    $scope.language = utils.url_language($window.location.pathname);
    hotkeys.bindTo($scope).add({
      combo: "a",
      description: gettext("show all cards inventoried"),
      callback: function(){
        $scope.toggleCardsToShow();
      }
    }).add({
      combo: "s",
      description: gettext("go to the search box"),
      callback: function(){
        utils.set_focus();
      }
    });
    utils.set_focus();
    $window.document.title = "Abelujo - " + gettext("Inventory");
  }
]);
angular.module("abelujo").controller('CommandsOngoingController', [
  '$http', '$scope', '$window', 'utils', '$log', function($http, $scope, $window, utils, $log){
    var ref$, Obj, join, reject, sum, map, filter, lines, findIndex;
    ref$ = require('prelude-ls'), Obj = ref$.Obj, join = ref$.join, reject = ref$.reject, sum = ref$.sum, map = ref$.map, filter = ref$.filter, lines = ref$.lines, findIndex = ref$.findIndex;
    $scope.commands = [];
    $scope.alerts = [];
    $scope.show_icon = {};
    $scope.language = utils.url_language($window.location.pathname);
    $scope.commands_url = "/" + $scope.language + "/commands/";
    $scope.command_popup_status = {};
    $scope.dates_labels = [];
    $http.get("/api/commands/ongoing/").then(function(response){
      var i$, ref$, len$, cmd, j$, ref1$, len1$, label;
      $scope.commands = response.data;
      $log.info("-- commands: ", response.data);
      $scope.dates_labels = ['date_received', 'date_bill_received', 'date_paid', 'date_payment_sent'];
      for (i$ = 0, len$ = (ref$ = $scope.commands).length; i$ < len$; ++i$) {
        cmd = ref$[i$];
        if (cmd) {
          for (j$ = 0, len1$ = (ref1$ = $scope.dates_labels).length; j$ < len1$; ++j$) {
            label = ref1$[j$];
            $scope.command_popup_status[cmd.id] = {};
            $scope.command_popup_status[cmd.id][label] = {};
            $scope.command_popup_status[cmd.id][label].opened = false;
            $scope.command_date[cmd.id] = {};
            $scope.command_date[cmd.id][label] = "";
            $scope.command_date[cmd.id][label] = cmd[label];
          }
        }
      }
    });
    $scope.set_date = function(cmd_id, elt, date){
      "Update the given date for the given command (api call). Display confirmation message.";
      var date_formatted, params;
      date_formatted = date.toString($scope.date_format);
      params = {
        cmd_id: cmd_id,
        date_label: elt,
        date: date_formatted
      };
      return $http.post("/api/commands/" + cmd_id + "/update", params).then(function(response){
        var index;
        index = findIndex(function(it){
          return it.id === cmd_id;
        })(
        $scope.commands);
        if (response.data.status === "success") {
          $scope.commands[index][elt] = date;
          return $scope.alerts.push({
            level: "success",
            message: gettext("Date changed")
          });
        } else {
          $scope.alerts.concat({
            level: "warning",
            message: gettext("Sorry, there was an internal problem")
          });
          $scope.alerts.concat(response.data.msgs);
          return $scope.commands[index][elt] = undefined;
        }
      });
    };
    $scope.command_date = {};
    $scope.today = function(){
      return $scope.command_date = new Date();
    };
    $scope.today();
    $scope.command_open_datepicker = function(event, cmd_id, elt){
      if (!cmd_id || !elt) {
        return;
      }
      if ($scope.command_popup_status[cmd_id] && !$scope.command_popup_status[cmd_id][elt]) {
        $scope.command_popup_status[cmd_id] = {};
        $scope.command_popup_status[cmd_id][elt] = {
          opened: true
        };
      }
      $scope.command_popup_status[cmd_id][elt].opened = true;
    };
    $scope.datepicker_command_options = {
      formatYear: 'yyyy',
      formatMonth: 'MMMM',
      startingDay: 1
    };
    $scope.command_date_format = "ddmmyyyy";
    $scope.date_format = 'yyyy-MM-dd HH:mm:ss';
    $scope.command_set_date = function(cmd_id, elt){
      "Save the date of this command. api call.";
      var date;
      date = $scope.command_date[cmd_id][elt];
      $scope.set_date(cmd_id, elt, date);
    };
    $scope.closeAlert = function(index){
      return $scope.alerts.splice(index, 1);
    };
  }
]);
angular.module("abelujo").controller('dashboardController', [
  '$http', '$scope', '$timeout', '$window', '$log', 'utils', '$locale', 'tmhDynamicLocale', function($http, $scope, $timeout, $window, $log, utils, $locale, tmhDynamicLocale){
    var ref$, sum, map, filter, lines, params;
    ref$ = require('prelude-ls'), sum = ref$.sum, map = ref$.map, filter = ref$.filter, lines = ref$.lines;
    $scope.language = utils.url_language($window.location.pathname);
    tmhDynamicLocale.set($scope.language);
    $scope.stats = undefined;
    $scope.sells_month = {};
    params = {
      language: $scope.language
    };
    $http.get("/api/stats/", {
      params: params
    }).then(function(response){
      response.data.data;
      $scope.stats = response.data;
    });
    $scope.shelfs = [];
    $scope.shelf = {};
    $http.get("/api/stats/sells/month").then(function(response){
      $scope.sells_month = response.data;
    });
    $scope.revenue_date = undefined;
    $scope.today = function(){
      return $scope.revenue_date = new Date();
    };
    $scope.today();
    $scope.revenue_popup_status = {
      opened: false
    };
    $scope.revenue_open_datepicker = function(event){
      return $scope.revenue_popup_status.opened = true;
    };
    $scope.datepicker_revenue_options = {
      minMode: "month",
      formatYear: 'yyyy',
      formatMonth: 'MMMM',
      startingDay: 1
    };
    $scope.revenue_date_format = "MMMM";
    $scope.revenue_change_month = function(){
      var params;
      params = {
        year: $scope.revenue_date.getFullYear(),
        month: $scope.revenue_date.getMonth() + 1
      };
      $log.info("Calling monthly report for " + $scope.revenue_date);
      $http.get("/api/stats/sells/month", {
        params: params
      }).then(function(response){
        $scope.sells_month = response.data;
      });
    };
    $window.document.title = "Abelujo" + " - " + gettext("dashboard");
  }
]);
angular.module("abelujo").controller('historyController', [
  '$http', '$scope', '$timeout', '$filter', '$window', 'utils', '$log', 'hotkeys', '$resource', 'tmhDynamicLocale', function($http, $scope, $timeout, $filter, $window, utils, $log, hotkeys, $resource, tmhDynamicLocale){
    var ref$, Obj, join, reject, sum, map, filter, find, lines, sortBy, findIndex, reverse, take, groupBy, uniqueBy, Distributors, getDistributors, DistSells;
    ref$ = require('prelude-ls'), Obj = ref$.Obj, join = ref$.join, reject = ref$.reject, sum = ref$.sum, map = ref$.map, filter = ref$.filter, find = ref$.find, lines = ref$.lines, sortBy = ref$.sortBy, findIndex = ref$.findIndex, reverse = ref$.reverse, take = ref$.take, groupBy = ref$.groupBy, uniqueBy = ref$.uniqueBy;
    $scope.history = [];
    $scope.sells_month = 0.0;
    $scope.total_sells_month_excl_tax = 0.0;
    $scope.back = [];
    $scope.filterModel = 'All';
    $scope.alerts = [];
    $scope.show_details = false;
    $scope.show_unique = false;
    $scope.show_tab = 'sells';
    $scope.last_sort = "created";
    $scope.distributors = [];
    $scope.distributor = {};
    $scope.today = function(){
      return $scope.user_date = new Date();
    };
    $scope.user_date = $scope.today();
    $scope.page = 1;
    $scope.page_size = 15;
    $scope.page_max = 1;
    $scope.sortorder = 0;
    $scope.sortby = "";
    Distributors = $resource('/api/distributors/:id');
    getDistributors = function(){
      Distributors.query(function(res){
        $scope.distributors = res;
      });
    };
    getDistributors();
    $scope.get_history = function(){
      var params;
      params = {
        month: $scope.user_date.getMonth() + 1,
        year: $scope.user_date.getFullYear(),
        page: $scope.page,
        page_size: $scope.page_size,
        sortby: $scope.sortby,
        sortorder: $scope.sortorder
      };
      $http.get("/api/history/sells", {
        params: params
      }).then(function(response){
        $scope.sells = [];
        $scope.sells_month = 0;
        $scope.total_sells_month_excl_tax = 0;
        $scope.nb_sells = response.data.data.nb_sells;
        $scope.nb_cards_sold = response.data.data.nb_cards_sold;
        $scope.get_page_max(response.data.data.total);
        return response.data.data.data.map(function(item){
          var repr, created;
          repr = "sell n° " + item.id;
          created = Date.parse(item.created);
          created = created.toString("d-MMM-yyyy");
          item.created = created;
          item.repr = repr;
          item.show_row = false;
          item.show_covers = false;
          $scope.sells.push(item);
          $scope.sells_month += item.price_sold;
          $scope.total_sells_month_excl_tax += item.price_sold_excl_tax;
          return {
            repr: repr,
            id: item.id
          };
        });
      });
    };
    $scope.get_history();
    $scope.get_page_max = function(){
      var add_one_page;
      add_one_page = function(total, page_size){
        if (total % page_size === 0) {
          return 0;
        }
        return 1;
      };
      $scope.page_max = Math.floor($scope.nb_sells / this.page_size) + add_one_page($scope.nb_sells, $scope.page_size);
    };
    $scope.nextPage = function(){
      if ($scope.page < $scope.page_max) {
        $scope.page += 1;
        $scope.get_history();
      }
    };
    $scope.previousPage = function(){
      if ($scope.page > 1) {
        $scope.page -= 1;
        $scope.get_history();
      }
    };
    $scope.firstPage = function(){
      $scope.page = 1;
      $scope.get_history();
    };
    $scope.lastPage = function(){
      $scope.page = $scope.page_max;
      $scope.get_history();
    };
    $scope.get_stats = function(){
      var stats_params;
      stats_params = {
        year: $scope.user_date.getFullYear(),
        month: $scope.user_date.getMonth() + 1
      };
      $http.get("/api/stats/sells/month", {
        params: stats_params
      }).then(function(response){
        $scope.stats_month = response.data;
      });
    };
    $scope.get_stats();
    $scope.history_entries = function(){
      $http.get("/api/history/entries").then(function(response){
        $scope.show_tab = 'entries';
        $scope.entries = map(function(it){
          it.created = Date.parse(it.created).toString("d-MMM-yyyy");
          return it;
        })(
        response.data.data);
        $log.info(response.data);
      });
      $http.get("/api/stats/entries/month").then(function(response){
        $scope.entries_month = response.data;
      });
    };
    $scope.select_tab = function(model){
      $scope.show_tab = model;
    };
    $scope.sellUndo = function(index){
      var sell, sure, params;
      sell = $scope.sells[index];
      $log.info("undo sell " + sell.id);
      sure = confirm(gettext("Are you sure to undo this sell ?"));
      if (sure) {
        params = {
          soldcard_id: sell.soldcard_id
        };
        $http.get("/api/sell/" + sell.sell_id + "/undo", {
          params: params
        }).then(function(response){
          $scope.alerts = response.data.alerts;
        });
      }
    };
    $scope.closeAlert = function(index){
      $scope.alerts.splice(index, 1);
    };
    $scope.toggle_details = function(){
      $scope.show_details = !$scope.show_details;
    };
    $scope.sort_by = function(key){
      "Custom sort function. Smart-table is buggy and\nunder-documented. Didn't find a good table for angular.";
      $scope.sortby = key;
      $scope.sortorder = ($scope.sortorder + 1) % 2;
      return $scope.get_history();
    };
    $scope.refreshDistributors = function(search, select){
      "For ui-select";
      getDistributors();
      select.refreshItems();
    };
    DistSells = $resource('/api/sell/');
    $scope.distChanged = function(){
      $scope.sells = DistSells.get({
        distributor_id: $scope.distributor.selected ? $scope.distributor.selected.id : void 8,
        month: $scope.user_date.getMonth() + 1,
        year: $scope.user_date.getFullYear(),
        page: $scope.page,
        page_size: $scope.page_size,
        sortby: $scope.sortby,
        sortorder: $scope.sortorder
      }, function(resp){
        var sells;
        $scope.sells = [];
        $scope.nb_sells = resp.data.data.length;
        $scope.sells_month = 0;
        $scope.total_sells_month_excl_tax = 0;
        sells = resp.data.data;
        sells.map(function(item){
          var repr, created;
          repr = "sell n° " + item.id;
          created = Date.parse(item.created);
          created = created.toString("d-MMM-yyyy");
          item.created = created;
          item.repr = repr;
          item.show_row = false;
          item.show_covers = false;
          $scope.sells.push(item);
          $scope.sells_month += item.price_sold;
          $scope.total_sells_month_excl_tax += item.price_sold_excl_tax;
          return {
            repr: repr,
            id: item.id
          };
        });
        if ($scope.show_unique) {
          $scope.filter_unique();
        }
      });
    };
    $scope.distErased = function(){
      $scope.distributor.selected = undefined;
      $scope.distChanged();
    };
    hotkeys.bindTo($scope).add({
      combo: "d",
      description: gettext("show or hide the book details in tables."),
      callback: function(){
        $scope.toggle_details();
      }
    }).add({
      combo: "f",
      description: gettext("filter one title per line"),
      callback: function(){
        $scope.show_unique = !$scope.show_unique;
        $scope.filter_unique();
      }
    });
    $scope.getMonth = function(){
      if ($scope.user_date) {
        return $scope.user_date.getMonth() + 1;
      }
    };
    $scope.user_popup_status = {
      opened: false
    };
    $scope.user_open_datepicker = function(event){
      return $scope.user_popup_status.opened = true;
    };
    $scope.datepicker_user_options = {
      minMode: "month",
      formatYear: 'yyyy',
      formatMonth: 'MMMM',
      startingDay: 1
    };
    $scope.user_date_format = "MMMM";
    $scope.user_change_month = function(){
      $scope.get_history();
      $scope.get_stats();
    };
    $window.document.title = "Abelujo - " + gettext("History");
  }
]);
angular.module("abelujo").controller('inventoriesController', [
  '$http', '$scope', '$log', 'utils', function($http, $scope, $log, utils){
    var ref$, sum, map, filter, lines, reverse, sortBy;
    ref$ = require('prelude-ls'), sum = ref$.sum, map = ref$.map, filter = ref$.filter, lines = ref$.lines, reverse = ref$.reverse, sortBy = ref$.sortBy;
    $scope.inventories = [];
    $scope.alerts = [];
    $scope.page = 1;
    $scope.nb_results = 0;
    $scope.page_max = 1;
    $scope.meta = {
      num_pages: null,
      nb_results: null
    };
    $scope.get_inventories = function(){
      var params;
      params = {
        page: $scope.page
      };
      $http.get("/api/inventories/", {
        params: params
      }).then(function(response){
        if (response.data.status === "error") {
          $log.error("Error while getting inventories server side");
        }
        $scope.inventories = response.data.data;
        $scope.meta = response.data.meta;
      });
    };
    $scope.get_inventories();
    $scope.last_sort = "name";
    $scope.sort_by = function(key){
      if ($scope.last_sort === key) {
        $scope.inventories = reverse(
        $scope.inventories);
      } else {
        $scope.inventories = sortBy(function(it){
          return it[key];
        })(
        $scope.inventories);
        $scope.last_sort = key;
      }
    };
    $scope.validate = function(index){
      var inv, sure;
      inv = $scope.inventories[index];
      if (inv.applied) {
        alert(gettext("This inventory is already applied."));
      } else {
        sure = confirm(gettext("Are you sure to apply this inventory to your stock ?"));
        if (sure) {
          inv.ongoing = true;
          $http.post("/api/inventories/" + inv.id + "/apply").then(function(response){
            var status;
            status = response.data.status;
            $scope.alerts = response.data.alerts;
          });
        }
      }
    };
    $scope.closeAlert = function(index){
      return $scope.alerts.splice(index, 1);
    };
    $scope.nextPage = function(){
      $scope.page += 1;
      if ($scope.page > $scope.meta.num_pages) {
        $scope.page = $scope.meta.num_pages;
      }
      $scope.get_inventories();
    };
    $scope.lastPage = function(){
      $scope.page = $scope.meta.num_pages;
      $scope.get_inventories();
    };
    $scope.previousPage = function(){
      if ($scope.page > 1) {
        $scope.page -= 1;
      }
      $scope.get_inventories();
    };
    $scope.firstPage = function(){
      $scope.page = 1;
      $scope.get_inventories();
    };
  }
]);
angular.module("abelujo").controller('inventoryNewController', [
  '$http', '$scope', '$timeout', 'utils', '$filter', '$window', 'hotkeys', '$log', function($http, $scope, $timeout, utils, $filter, $window, hotkeys, $log){
    var ref$, sum, map, filter, lines, reverse, join, reject, round, showAll, existing_card, page_size, is_default_inventory, is_command_receive, pathname, api_inventory_id, api_inventory_id_remove, api_inventory_id_update, api_inventory_id_diff, url_inventory_id_terminate, get_api, params;
    String.prototype.contains = function(it){
      return this.indexOf(it) !== -1;
    };
    ref$ = require('prelude-ls'), sum = ref$.sum, map = ref$.map, filter = ref$.filter, lines = ref$.lines, reverse = ref$.reverse, join = ref$.join, reject = ref$.reject, round = ref$.round;
    $scope.language = utils.url_language($window.location.pathname);
    $scope.cards_fetched = [];
    $scope.copy_selected = undefined;
    $scope.history = [];
    $scope.cards_selected = [];
    $scope.all = [];
    $scope.showAll = false;
    showAll = $window.localStorage.getItem("inventories_showAll");
    if (showAll !== undefined) {
      if (showAll === "true") {
        $scope.showAll = true;
      }
    }
    $scope.cards_to_show = [];
    $scope.total_value = 0;
    $scope.nb_cards = 0;
    $scope.nb_copies = 0;
    $scope.tmpcard = undefined;
    $scope.selected_ids = [];
    existing_card = undefined;
    $scope.page = 1;
    $scope.page_sizes = [25, 50, 100, 200];
    $scope.page_max = 1;
    $scope.meta = {
      num_pages: null,
      nb_results: null
    };
    page_size = $window.localStorage.getItem("inventories_page_size");
    if (page_size !== null) {
      $scope.page_size = parseInt(page_size);
    } else {
      $scope.page_size = 25;
    }
    is_default_inventory = false;
    is_command_receive = false;
    pathname = $window.location.pathname;
    if (pathname.contains("inventories")) {
      is_default_inventory = true;
      $log.info("found default inventory");
      api_inventory_id = "/api/inventories/{inv_or_cmd_id}/";
      api_inventory_id_remove = api_inventory_id + "remove/";
      api_inventory_id_update = api_inventory_id + "update/";
      api_inventory_id_diff = api_inventory_id + "diff/";
      url_inventory_id_terminate = "/" + $scope.language + "/inventories/{inv_or_cmd_id}/terminate/";
    } else if (pathname.contains("commands")) {
      is_command_receive = true;
      $log.info("found a command inventory.");
      api_inventory_id = "/api/commands/{inv_or_cmd_id}/receive/";
      api_inventory_id_remove = api_inventory_id + "remove/";
      api_inventory_id_update = api_inventory_id + "update/";
      api_inventory_id_diff = api_inventory_id + "diff/";
      url_inventory_id_terminate = "/" + $scope.language + "/commands/{inv_or_cmd_id}/receive/terminate/";
    } else {
      $log.error("What are we doing the inventory of ??");
      throw Error('unimplemented');
    }
    get_api = function(api){
      return api.replace("{inv_or_cmd_id}", $scope.inv_or_cmd_id);
    };
    $scope.inv_or_cmd_id = utils.url_id($window.location.pathname);
    $log.info("found inv_or_cmd_id: ", $scope.inv_or_cmd_id);
    $scope.cur_inv = "";
    $scope.setCardsToShow = function(){
      " Show all the cards inventoried, or the current ones. ";
      if ($scope.showAll) {
        $scope.cards_to_show = reverse(
        $scope.all);
      } else {
        $scope.cards_to_show = reverse(
        $scope.cards_selected);
      }
    };
    $scope.toggleCardsToShow = function(){
      $scope.showAll = !$scope.showAll;
      $window.localStorage.inventories_showAll = $scope.showAll;
      $scope.setCardsToShow();
    };
    if ($scope.inv_or_cmd_id) {
      $log.info("using api_inventory_id: ", get_api(api_inventory_id));
      params = {
        page_size: $scope.page_size,
        page: $scope.page
      };
      $http.get(get_api(api_inventory_id), {
        params: params
      }).then(function(response){
        $log.info("Response of api_inventory_id");
        response.data.data;
        $scope.state = response.data.data;
        $scope.cards_fetched = $scope.state.copies;
        $scope.nb_cards = response.data.data.nb_cards;
        $scope.nb_copies = response.data.data.nb_copies;
        $scope.meta = response.data.data.meta;
        map(function(it){
          var ref$;
          $scope.all.push(it.card);
          return (ref$ = $scope.all)[ref$.length - 1].quantity = it.quantity;
        }, $scope.state.copies);
        $scope.selected_ids = map(function(it){
          return it.card.id;
        }, $scope.state.copies);
        $scope.cur_inv = $scope.state.inv_name;
        $scope.total_value = response.data.data.total_value;
      });
    }
    $scope.getCopies = function(){
      var params, url;
      params = {
        page_size: $scope.page_size,
        page: $scope.page
      };
      url = get_api(api_inventory_id);
      url += "copies";
      $http.get(url, {
        params: params
      }).then(function(response){
        $log.info("-- cards: ", response.data);
        $scope.cards_fetched = response.data;
        $scope.all = [];
        map(function(it){
          var ref$;
          $scope.all.push(it.card);
          return (ref$ = $scope.all)[ref$.length - 1].quantity = it.quantity;
        }, response.data);
        $scope.setCardsToShow();
      });
    };
    $scope.getCards = function(val){
      return $http.get("/api/cards", {
        params: {
          query: val,
          card_type_id: null,
          lang: $scope.language
        }
      }).then(function(response){
        var res;
        res = response.data.cards.map(function(item){
          var repr;
          repr = item.title + ", " + item.authors_repr + ", éd " + item.pubs_repr;
          item.quantity = 1;
          $scope.cards_fetched.push({
            "repr": repr,
            "id": item.id,
            "item": item
          });
          return {
            "repr": repr,
            "id": item.id
          };
        });
        if (utils.is_isbn(val) && res.length === 1) {
          setTimeout(function(){
            $window.document.getElementById("default-input").value = "";
            return $scope.add_selected_card(res[0]);
          }, 500);
          return;
        }
        return res;
      });
    };
    $scope.add_selected_card = function(card){
      var existing_card;
      $scope.tmpcard = _.filter($scope.cards_fetched, function(it){
        return it.repr === card.repr;
      });
      $scope.tmpcard = $scope.tmpcard[0].item;
      if (!_.contains($scope.selected_ids, $scope.tmpcard.id)) {
        $scope.cards_selected.push($scope.tmpcard);
        $scope.all.push($scope.tmpcard);
        $scope.selected_ids.push($scope.tmpcard.id);
      } else {
        existing_card = _.filter($scope.all, function(it){
          return it.id === $scope.tmpcard.id;
        });
        existing_card = existing_card[0];
        existing_card.quantity += 1;
        if (!_.contains($scope.cards_selected, existing_card)) {
          $scope.cards_selected.push(existing_card);
        }
      }
      $scope.copy_selected = undefined;
      $scope.setCardsToShow();
      $scope.total_value += $scope.tmpcard.price * $scope.tmpcard.quantity;
      $scope.total_value = round($scope.total_value * 10) / 10;
      $scope.nb_cards += 1;
      $scope.nb_copies += $scope.tmpcard.quantity;
      $scope.save();
    };
    $scope.remove_from_selection = function(index_to_rm){
      "Remove the card from the selection to display\nand from the inventory (api call).";
      var card, params;
      $scope.selected_ids.splice(index_to_rm, 1);
      $scope.cards_selected.splice(index_to_rm, 1);
      $scope.all.splice(index_to_rm, 1);
      focus();
      card = $scope.cards_to_show[index_to_rm];
      params = {
        "card_id": card.id
      };
      $log.info("calling api_inventory_id_remove: ", api_inventory_id_remove);
      $http.post(get_api(api_inventory_id_remove), params).then(function(response){
        $scope.cards_to_show.splice(index_to_rm, 1);
        $scope.total_value -= card.price * card.quantity;
        $scope.total_value = round($scope.total_value * 10) / 10;
        $scope.nb_cards -= 1;
        $scope.nb_copies -= card.quantity;
      });
    };
    $scope.updateCard = function(index){
      "";
      var card, params;
      card = $scope.cards_to_show[index];
      params = {
        "ids_qties": card.id + "," + card.quantity + ";"
      };
      $log.info("using api_inventory_id_update: ", api_inventory_id_update);
      $http.post(get_api(api_inventory_id_update), params).then(function(response){
        var thecard;
        $log.info($scope.all);
        thecard = $scope.all;
        $scope.all = reject(function(it){
          return it.id === card.id;
        })(
        $scope.all);
        $scope.all.push(card);
        $scope.total_value = response.data.total_value;
        $scope.nb_cards = response.data.nb_cards;
        $scope.nb_copies = response.data.nb_copies;
        $scope.alerts = response.data.alerts;
      });
    };
    $scope.save = function(){
      "Send the new copies and quantities to be saved.";
      var ids_qties, params;
      ids_qties = [];
      map(function(it){
        return ids_qties.push(it.id + ", " + it.quantity + ";");
      }, $scope.cards_selected);
      params = {
        "ids_qties": join("", ids_qties)
      };
      return $http.post(get_api(api_inventory_id_update), params).then(function(response){
        $scope.alerts = response.data.msgs;
        return response.data.status;
      });
    };
    $scope.terminate = function(){
      $log.info("using api_inventory_id_diff: ", api_inventory_id_diff);
      $http.get(get_api(api_inventory_id_diff)).then(function(response){
        $log.info("using url_inventory_id_terminate: ", get_api(url_inventory_id_terminate));
        $window.location.href = get_api(url_inventory_id_terminate);
      });
    };
    if ($scope.showAll) {
      $scope.setCardsToShow();
    }
    $scope.$watch("page_size", function(){
      $window.localStorage.inventories_page_size = $scope.page_size;
      $scope.getCopies();
    });
    $scope.nextPage = function(){
      if ($scope.page < $scope.meta.num_pages) {
        $scope.page += 1;
        $scope.getCopies();
      }
    };
    $scope.lastPage = function(){
      $scope.page = $scope.meta.num_pages;
      $scope.getCopies();
    };
    $scope.previousPage = function(){
      if ($scope.page > 1) {
        $scope.page -= 1;
        $scope.getCopies();
      }
    };
    $scope.firstPage = function(){
      $scope.page = 1;
      $scope.getCopies();
    };
    hotkeys.bindTo($scope).add({
      combo: "a",
      description: gettext("show all cards inventoried"),
      callback: function(){
        $scope.toggleCardsToShow();
      }
    }).add({
      combo: "s",
      description: gettext("go to the search box"),
      callback: function(){
        utils.set_focus();
      }
    });
    utils.set_focus();
    $window.document.title = "Abelujo - " + gettext("Inventory");
  }
]);
angular.module("abelujo").controller('inventoryTerminateController', [
  '$http', '$scope', '$timeout', 'utils', '$filter', '$window', '$log', function($http, $scope, $timeout, utils, $filter, $window, $log){
    var ref$, sum, map, filter, lines, join, Obj, pathname, api_inventory_id, base_url_inventory_view, api_inventory_id_diff, api_inventory_id_apply, get_api, existing_card, focus;
    ref$ = require('prelude-ls'), sum = ref$.sum, map = ref$.map, filter = ref$.filter, lines = ref$.lines, join = ref$.join, Obj = ref$.Obj;
    $scope.is_default_inventory = false;
    $scope.is_command_receive = false;
    pathname = $window.location.pathname;
    $scope.inv_or_cmd_id = utils.url_id($window.location.pathname);
    String.prototype.contains = function(it){
      return this.indexOf(it) !== -1;
    };
    if (pathname.contains("inventories")) {
      $scope.is_default_inventory = true;
      $log.info("found default inventory");
      api_inventory_id = "/api/inventories/{inv_or_cmd_id}/";
      base_url_inventory_view = "/inventories/{inv_or_cmd_id}/";
    } else if (pathname.contains("commands")) {
      $scope.is_command_receive = true;
      $log.info("found a command inventory.");
      api_inventory_id = "/api/commands/{inv_or_cmd_id}/receive/";
      base_url_inventory_view = "/commands/{inv_or_cmd_id}/receive/terminate/";
    } else {
      $log.error("What are we doing the inventory of ??");
      throw Error('unimplemented');
    }
    api_inventory_id_diff = api_inventory_id + "diff/";
    api_inventory_id_apply = api_inventory_id + "apply/";
    get_api = function(api){
      return api.replace("{inv_or_cmd_id}", $scope.inv_or_cmd_id);
    };
    $scope.get_base_url = function(){
      return base_url_inventory_view.replace("{inv_or_cmd_id}", $scope.inv_or_cmd_id);
    };
    $scope.cards_fetched = [];
    $scope.copy_selected = undefined;
    $scope.history = [];
    $scope.cards_selected = [];
    $scope.all = [];
    $scope.showAll = false;
    $scope.cards_to_show = [];
    $scope.name;
    $scope.alerts = [];
    $scope.tmpcard = undefined;
    $scope.selected_ids = [];
    existing_card = undefined;
    $scope.more_in_inv = {};
    $scope.less_in_inv = {};
    $scope.missing = {};
    $scope.is_more_in_inv = false;
    $scope.is_less_in_inv = false;
    $scope.is_missing = false;
    $scope.page = 1;
    $scope.page_size = 50;
    $scope.page_sizes = [25, 50, 100, 200];
    $scope.page_max = 1;
    $scope.meta = {
      num_pages: 1
    };
    $scope.inv_id = utils.url_id($window.location.pathname);
    $scope.language = utils.url_language($window.location.pathname);
    $scope.get_diff = function(){
      var params;
      params = {
        page: $scope.page
      };
      $http.get(get_api(api_inventory_id_diff), {
        params: params
      }).then(function(response){
        $scope.diff = response.data.cards;
        $scope.name = response.data.name;
        $scope.total_copies_in_inv = response.data.total_copies_in_inv;
        $scope.total_copies_in_stock = response.data.total_copies_in_stock;
        $scope.meta = response.data.meta;
        $scope.more_in_inv = Obj.filter(function(it){
          return it.diff < 0;
        })(
        $scope.diff);
        $scope.is_more_in_inv = !Obj.empty($scope.more_in_inv);
        $scope.less_in_inv = Obj.filter(function(it){
          return it.diff > 0;
        })(
        $scope.diff);
        $scope.is_less_in_inv = !Obj.empty($scope.less_in_inv);
        $scope.missing = Obj.filter(function(it){
          return it.inv === 0;
        })(
        $scope.diff);
        $scope.is_missing = !Obj.empty($scope.missing);
        $scope.no_origin = Obj.filter(function(it){
          return it.stock === 0;
        })(
        $scope.diff);
        $scope.is_no_origin = !Obj.empty($scope.no_origin);
      });
    };
    $scope.get_diff();
    $scope.obj_length = function(obj){
      return Obj.keys(obj).length;
    };
    $scope.validate = function(){
      var sure;
      sure = confirm("Are you sure to apply this inventory to your stock ?");
      if (sure) {
        $log.info("post to ", get_api(api_inventory_id_apply));
        $http.post(get_api(api_inventory_id_apply)).then(function(response){
          var status;
          status = response.data.status;
          $scope.alerts = response.data.alerts;
        });
      }
    };
    $scope.closeAlert = function(index){
      $scope.alerts.splice(index, 1);
    };
    $scope.nextPage = function(){
      if ($scope.page < $scope.meta.num_pages) {
        $scope.page += 1;
        $scope.get_diff();
      }
    };
    $scope.lastPage = function(){
      $scope.page = $scope.meta.num_pages;
      $scope.get_diff();
    };
    $scope.previousPage = function(){
      if ($scope.page > 1) {
        $scope.page -= 1;
        $scope.get_diff();
      }
    };
    $scope.firstPage = function(){
      $scope.page = 1;
      $scope.get_diff();
    };
    focus = function(){
      angular.element('#default-input').trigger('focus');
    };
    focus();
    $window.document.title = "Abelujo - " + gettext("Terminate inventory") + "-" + $scope.name;
  }
]);
angular.module("abelujo").controller('loginController', ['$http', '$scope', '$timeout', '$log', function($http, $scope, $timeout, $log){}]);
angular.module("abelujo").controller('navbarController', [
  '$http', '$scope', '$log', 'utils', '$window', function($http, $scope, $log, utils, $window){
    var ref$, sum, map, filter, find;
    ref$ = require('prelude-ls'), sum = ref$.sum, map = ref$.map, filter = ref$.filter, find = ref$.find;
    $scope.username = undefined;
    $scope.cards_fetched = [];
    $scope.copy_selected = undefined;
    $scope.language = utils.url_language($window.location.pathname);
    $http.get("/api/userinfo").then(function(response){
      $scope.username = response.data.data.username;
    });
    $scope.getCards = function(query){
      var args, promise;
      args = {
        query: query,
        language: $scope.language,
        with_quantity: false
      };
      promise = utils.getCards(args);
      if (promise) {
        return promise.then(function(res){
          $scope.cards_fetched = res;
          if (utils.is_isbn(query) && res.length === 1) {
            $scope.go_to_card(res[0]);
          }
          if (utils.is_isbn(query) && res.length === 0) {
            Notiflix.Notify.Merge({
              timeout: 20000
            });
            Notiflix.Notify.Warning(gettext('ISBN not found.'));
            Notiflix.Notify.Info(gettext('You can still create a card manually.'));
            $window.document.getElementById("navbar-input").value = "";
          }
          return res;
        });
      }
    };
    $scope.go_to_card = function(item){
      var card;
      $log.info(item);
      card = find(function(it){
        return it.id === item.id;
      })(
      $scope.cards_fetched);
      if (card) {
        card = card.item;
        $log.info(card);
        $window.location.href = card.get_absolute_url;
      } else {
        $log.warn("card is undefined");
        $window.document.getElementById("navbar-input").value = "";
      }
    };
  }
]);
angular.module("abelujo").controller('preferencesController', [
  '$http', '$scope', '$log', 'utils', '$resource', 'hotkeys', function($http, $scope, $log, utils, $resource, hotkeys){
    var ref$, sum, map, filter, find, Places;
    ref$ = require('prelude-ls'), sum = ref$.sum, map = ref$.map, filter = ref$.filter, find = ref$.find;
    $scope.preferences = {};
    $scope.username = undefined;
    $scope.places = [];
    $scope.place = undefined;
    $scope.vat_book = undefined;
    Places = $resource("/api/places/:id");
    Places.query(function(places){
      $scope.places = places;
      $http.get("/api/preferences").then(function(response){
        $scope.preferences = response.data.data;
        $scope.place = find(function(it){
          return it.id === $scope.preferences.default_place.id;
        })(
        $scope.places);
        $scope.place_orig = $scope.place;
        $scope.vat_book = $scope.preferences.vat_book;
      });
    });
    $scope.save = function(userForm){
      var params;
      if (userForm.$valid) {
        params = {
          place_id: $scope.place.id,
          vat_book: $scope.vat_book
        };
        $http.post("/api/preferences", params).then(function(response){
          if (response.data.status === "success") {
            $scope.alerts = [{
              'level': 'success',
              'message': gettext("Preferences updated")
            }];
          } else {
            $scope.alerts = [{
              'level': 'warning',
              'message': gettext("There seems to be a problem to save preferences.")
            }];
          }
        });
      } else {
        $log.info("form is not valid");
      }
    };
    $scope.closeAlert = function(index){
      return $scope.alerts.splice(index, 1);
    };
  }
]);
angular.module("abelujo").controller('receptionController', [
  '$http', '$scope', '$timeout', '$filter', '$window', '$uibModal', '$log', 'utils', '$location', 'hotkeys', function($http, $scope, $timeout, $filter, $window, $uibModal, $log, utils, $location, hotkeys){
    var ref$, Obj, Str, join, reject, sum, map, filter, find, lines, sortBy, findIndex, reverse, page_size;
    ref$ = require('prelude-ls'), Obj = ref$.Obj, Str = ref$.Str, join = ref$.join, reject = ref$.reject, sum = ref$.sum, map = ref$.map, filter = ref$.filter, find = ref$.find, lines = ref$.lines, sortBy = ref$.sortBy, findIndex = ref$.findIndex, reverse = ref$.reverse;
    $scope.shelves = [];
    $scope.shelves_length = {};
    $scope.new_shelf = null;
    $scope.cur_basket = {
      id: -1,
      fields: {
        name: "Tous les titres"
      }
    };
    $scope.cur_basket_index = 0;
    $scope.copies = [];
    $scope.all_copies = [];
    $scope.cards_fetched = [];
    $scope.copy_selected = undefined;
    $scope.cur_card_reservations = "hello";
    $scope.show_buttons = {};
    $scope.copy_selected = undefined;
    $scope.show_images = false;
    $scope.language = utils.url_language($window.location.pathname);
    $window.document.title = "Abelujo - " + gettext("Reception");
    $scope.body = "";
    $scope.page = 1;
    $scope.page_size = 200;
    $scope.page_sizes = [25, 50, 100, 200];
    $scope.page_max = 1;
    $scope.meta = {
      num_pages: null,
      nb_results: null
    };
    page_size = $window.localStorage.getItem("baskets_page_size");
    if (page_size !== null) {
      $scope.page_size = parseInt(page_size);
    }
    Notiflix.Notify.Init({
      timeout: 7000,
      messageMaxLength: 220,
      position: "center-top"
    });
    $http.defaults.headers.common.XCSRFToken = getCSRFToken();
    $log.info("token: ", getCSRFToken());
    $http.get("/api/shelfs").then(function(response){
      "Get the shelves.";
      return $scope.shelves = response.data;
    });
    $http.get("/api/reception/").then(function(response){
      var i$, ref$, len$, copy, results$ = [];
      $scope.all_copies = response.data.data;
      $scope.copies = response.data.data;
      $scope.get_basket_quantity();
      for (i$ = 0, len$ = (ref$ = $scope.copies).length; i$ < len$; ++i$) {
        copy = ref$[i$];
        if (!copy.shelf) {
          copy.alerts = [];
          results$.push(copy.alerts.push({
            message: "Pas de rayon"
          }));
        }
      }
      return results$;
    });
    $http.get("/api/reception/shelfs").then(function(response){
      return $scope.shelves_length = response.data.data;
    });
    $scope.getCards = function(query){
      var args, promise;
      args = {
        query: query,
        language: $scope.language,
        lang: $scope.language
      };
      promise = utils.getCards(args);
      if (promise) {
        return promise.then(function(res){
          $scope.cards_fetched = res;
          if (utils.is_isbn(query) && res.length === 1) {
            setTimeout(function(){
              $window.document.getElementById("default-input").value = "";
              return $scope.add_selected_card(res[0]);
            }, 700);
            return;
          }
          return res;
        });
      }
    };
    $scope.add_selected_card = function(card){
      "Add the card selected from the autocomplete to the current list's copies.\nAnd then, save it. If there is an error at this phase, show it asynchronously.";
      var cards_fetched, now, tmpcard, existing, index, title;
      cards_fetched = $scope.cards_fetched;
      now = luxon.DateTime.local().toFormat('yyyy-LL-dd HH:mm:ss');
      tmpcard = find(function(it){
        return it.repr === card.repr;
      })(
      cards_fetched);
      if (!tmpcard) {
        $log.warn("we were expecting an existing tmpcard amongst cards_fetched ", cards_fetched);
        Notiflix.Notify.Warning("Le serveur n'est pas prêt ! Veuillez attendre un instant et ré-essayer, merci.");
        $scope.copy_selected = undefined;
        return;
      }
      tmpcard = tmpcard.item;
      existing = find(function(it){
        return it.id === tmpcard.id;
      })(
      $scope.all_copies);
      if (existing) {
        existing.basket_qty += 1;
        existing.modified = now;
        index = findIndex(function(it){
          return existing.id === it.id;
        }, $scope.all_copies);
        if (index) {
          $scope.all_copies.splice(index, 1);
          $scope.all_copies.unshift(existing);
        }
      } else {
        tmpcard.modified = now;
        $scope.all_copies.unshift(tmpcard);
        existing = tmpcard;
      }
      $scope.shelves_length[tmpcard.shelf_id] += 1;
      $scope.copy_selected = undefined;
      if ($scope.cur_basket.id !== -1 && existing.shelf_id && $scope.cur_basket.pk !== existing.shelf_id) {
        title = Str.take(20, existing.title);
        Notiflix.Notify.Info("Attention vous êtes dans le menu '" + $scope.cur_basket.fields.name + "' et le livre '" + title + "' a déjà un rayon ('" + existing.shelf + "').");
      } else {
        tmpcard.shelf_id = $scope.cur_basket.pk;
        tmpcard.shelf = $scope.cur_basket.fields.name;
      }
      $scope.save_card_to_reception(tmpcard.id);
    };
    $scope.save_card_to_reception = function(card_id, quantity){
      var params;
      quantity == null && (quantity = null);
      params = {
        card_id: card_id,
        shelf_id: $scope.cur_basket.pk
      };
      if (quantity !== null) {
        params['quantity'] = quantity;
      }
      $http.post("/api/reception/add/", params).then(function(response){
        var card;
        card = find(function(it){
          return it.id === card_id;
        })(
        $scope.all_copies);
        if (card) {
          card.alerts = response.data.alerts;
        } else {
          $log.info("PAS DE CARD !");
        }
        if ($scope.cur_basket.id !== -1 && card.shelf_id && $scope.cur_basket.pk !== card.shelf_id) {
          card.shelf_id = $scope.cur_basket.pk;
          card.shelf = $scope.cur_basket.fields.name;
        }
        Notiflix.Notify.Success("OK!");
        $scope.get_basket_quantity();
        $scope.showShelfById($scope.cur_basket.pk);
      }, function(response){
        var elt;
        Notiflix.Notify.Warning("Something went wrong.");
        elt = $window.document.getElementById("card" + tmpcard.id);
      });
    };
    $scope.getCopies = function(shelf_id){
      var res;
      res = filter(function(it){
        return it.shelf_id === shelf_id;
      })(
      $scope.all_copies);
      $scope.copies = res;
      return res;
    };
    $scope.showBasket = function(index){
      "Show the copies of the shelf (by its index in the shelves list).";
      if (index === -1) {
        $scope.copies = $scope.all_copies;
        $scope.cur_basket_index = 0;
        $scope.cur_basket = {
          id: -1,
          fields: {
            name: ""
          }
        };
        $scope.set_focus();
        return;
      }
      $scope.cur_basket = $scope.shelves[index];
      if ($scope.cur_basket) {
        $location.hash($scope.cur_basket.id);
        $scope.getCopies($scope.cur_basket.pk);
        $scope.set_focus();
      }
    };
    $scope.showShelfById = function(pk){
      var shelf;
      shelf = find(function(it){
        return it.pk === pk;
      })(
      $scope.shelves);
      if (shelf) {
        $scope.cur_basket = shelf;
        $scope.getCopies(shelf.pk);
        return $scope.set_focus();
      }
    };
    $scope.update_card_shelf = function(card, shelf){
      var params;
      params = {
        card_id: card.id,
        shelf_id: shelf.pk
      };
      $http.post("/api/cards/update", params).then(function(response){
        var copy;
        copy = find(function(it){
          return it.id === card.id;
        })(
        $scope.all_copies);
        copy.shelf = shelf.fields.name;
        copy.shelf_id = shelf.pk;
        copy.alerts = [];
        Notiflix.Notify.Success("Shelf updated.");
      }, function(response){
        Notiflix.Notify.Warning("Something went wrong.");
      });
    };
    $scope.set_focus = function(){
      angular.element('#default-input').trigger('focus');
    };
    $scope.set_focus();
    $scope.save_quantity = function(index){
      "Save the item quantity after click.";
      var card, quantity, now;
      card = $scope.copies[index];
      $scope.save_card_to_reception(card.id, quantity = card.basket_qty);
      now = luxon.DateTime.local().toFormat('yyyy-LL-dd HH:mm:ss');
      card.modified = now;
    };
    $scope.get_basket_quantity = function(){
      $scope.total_basket_quantity = sum(
      map(function(it){
        return it.basket_qty;
      })(
      $scope.all_copies));
    };
    $scope.validate_reception = function(){
      "Validate the reception, start anew.";
      var params;
      if (confirm(gettext("Do you want to validate this reception ?"))) {
        params = {
          foo: 1
        };
        $http.post("/api/reception/validate/", params).then(function(response){
          if (response.data.status === 'success') {
            $window.location.href = "/" + $scope.language + "/reception/";
            $scope.all_copies = [];
          } else {
            Notiflix.Notify.Warning("Something went wrong.");
          }
        }, function(response){
          Notiflix.Notify.Warning("Something went wrong.");
        });
      }
    };
    $scope.reservation_details = function(card_id){
      var copy, NEWLINE, ESPERLUETTE;
      $log.info("I was here ", card_id);
      copy = find(function(it){
        return it.id === card_id;
      })(
      $scope.all_copies);
      NEWLINE = "%0D%0A";
      ESPERLUETTE = "%26";
      $scope.body = "Votre réservation suivante est arrivée à la librairie:" + NEWLINE + NEWLINE + "-  " + copy.title + " " + copy.price_fmt;
      $scope.body += NEWLINE + NEWLINE + "Nous vous l'avons mise de côté." + NEWLINE + NEWLINE + "À bientôt.";
      $http.post("/api/card/" + card_id + "/reservations/").then(function(response){
        if (response.data.status === 'success') {
          if (copy) {
            copy.reservations = response.data.data;
            $scope.cur_card_reservations = copy;
            $log.info("-- response: ", response);
            $log.info("-- cur_card_reservations ", $scope.cur_card_reservations);
          } else {
            Notiflix.Notify.Warning("Server is busy, please wait a bit.");
          }
        } else {
          Notiflix.Notify.Warning("Something went wrong.");
        }
      }, function(response){
        Notiflix.Notify.Warning("Something went wrong.");
      });
    };
    $scope.validate_reservation = function(resa){
      var params;
      $log.info("-- ok validate");
      params = {
        card_id: resa.card_id,
        client_id: resa.client_id
      };
      $log.info("-- params: ", params);
      $http.post("/api/card/" + resa.card_id + "/putaside/", params).then(function(response){
        if (response.data.status) {
          resa.disabled = true;
          Notiflix.Notify.Success("OK");
          $('#fixreservationModal').modal('toggle');
        } else {
          Notiflix.Notify.Warning("mmh");
        }
      }, function(response){
        Notiflix.Notify.Warning("Something went wrong.");
      });
    };
    hotkeys.bindTo($scope).add({
      combo: "d",
      description: gettext("show or hide the book details in tables."),
      callback: function(){
        $scope.toggle_images();
      }
    });
    $scope.$watch("page_size", function(){
      $window.localStorage.baskets_page_size = $scope.page_size;
      $scope.getCopies($scope.cur_basket_index);
    });
    $scope.nextPage = function(){
      if ($scope.page < $scope.meta.num_pages) {
        $scope.page += 1;
        $scope.getCopies($scope.cur_basket_index);
      }
    };
    $scope.lastPage = function(){
      $scope.page = $scope.meta.num_pages;
      $scope.getCopies($scope.cur_basket_index);
    };
    $scope.previousPage = function(){
      if ($scope.page > 1) {
        $scope.page -= 1;
        $scope.getCopies($scope.cur_basket_index);
      }
    };
    $scope.firstPage = function(){
      $scope.page = 1;
      $scope.getCopies($scope.cur_basket_index);
    };
    $scope.toggle_images = function(){
      $scope.show_images = !$scope.show_images;
    };
  }
]);
angular.module("abelujo").controller('restockingController', [
  '$http', '$scope', '$timeout', '$filter', '$window', 'utils', '$log', 'hotkeys', '$resource', function($http, $scope, $timeout, $filter, $window, utils, $log, hotkeys, $resource){
    var ref$, Obj, join, reject, sum, map, filter, find, lines, sortBy, findIndex, reverse, take, groupBy, uniqueBy;
    ref$ = require('prelude-ls'), Obj = ref$.Obj, join = ref$.join, reject = ref$.reject, sum = ref$.sum, map = ref$.map, filter = ref$.filter, find = ref$.find, lines = ref$.lines, sortBy = ref$.sortBy, findIndex = ref$.findIndex, reverse = ref$.reverse, take = ref$.take, groupBy = ref$.groupBy, uniqueBy = ref$.uniqueBy;
    $scope.ignored_cards = {};
    $scope.cards_ok = {};
    $scope.alerts = [];
    $scope.not_implemented = function(){
      alert("Not implemented.");
    };
    $http.get("/api/restocking/").then(function(response){
      $log.info(response);
      $scope.cards = response.data;
    });
    $scope.ignore_card = function(id){
      var card;
      $log.info(id);
      $scope.ignored_cards[id] = true;
      card = document.getElementById(id);
      card.setAttribute('data-card-ok', 'no');
      return $log.info("card ok? ", card.getAttribute('data-card-ok'));
    };
    $scope.mark_ready = function(id){
      var card;
      if ($scope.ignored_cards[id]) {
        $scope.ignored_cards[id] = false;
      }
      $scope.cards_ok[id] = true;
      card = document.getElementById(id);
      card.setAttribute('data-card-ok', 'yes');
      $log.info("card ok? ", card.getAttribute('data-card-ok'));
      return $log.info("cards ok: ", $scope.cards_ok);
    };
    $scope.remove_card = function(id){
      var answer;
      $log.info(id);
      answer = confirm("Are you sure to remove this card from the restocking list, until next time? This action cannot be undone.");
      if (answer) {
        return $http.post("/api/restocking/remove/" + id).then(function(response){
          $log.info(response);
          $scope.alerts = response.data.alerts;
        });
      }
    };
    $scope.is_ready = function(id){
      if ($scope.ignored_cards[id] === true) {
        return false;
      }
      return $scope.cards_ok[id];
    };
    $scope.card_ignored = function(id){
      var sid;
      if ($scope.ignored_cards[id]) {
        $log.info("id int is ignored");
        return true;
      }
      sid = id.toString();
      if ($scope.ignored_cards[sid]) {
        $log.info("this id (type string) is ignored");
        return true;
      }
      return false;
    };
    $scope.validate = function(){
      var inputs, ids, qties, i$, len$, input, config, params;
      $log.info("validating cards ok: ", $scope.cards_ok);
      inputs = document.getElementsByClassName('my-number-input');
      ids = [];
      qties = [];
      for (i$ = 0, len$ = inputs.length; i$ < len$; ++i$) {
        input = inputs[i$];
        if (input.getAttribute('data-card-ok') === 'yes') {
          ids.push(input.getAttribute('data-card-id'));
          qties.push(input.value);
        }
      }
      $log.info("sending: ", ids, qties);
      config = {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
      };
      params = {
        ids: ids,
        qties: qties
      };
      $http.post("/api/restocking/validate", params).then(function(response){
        $log.info(response);
        $scope.alerts = response.data.alerts;
        setTimeout(function(){
          $window.location.pathname = "/restocking";
        }, 4000);
      });
    };
    $window.document.title = "Abelujo - " + gettext("Restocking");
  }
]);
angular.module("abelujo").controller('returnsController', [
  '$http', '$scope', '$timeout', '$filter', '$window', '$uibModal', '$log', 'utils', '$location', 'hotkeys', function($http, $scope, $timeout, $filter, $window, $uibModal, $log, utils, $location, hotkeys){
    var ref$, Obj, join, reject, sum, map, filter, find, lines, sortBy, findIndex, reverse, COMMAND_BASKET_ID, page_size;
    ref$ = require('prelude-ls'), Obj = ref$.Obj, join = ref$.join, reject = ref$.reject, sum = ref$.sum, map = ref$.map, filter = ref$.filter, find = ref$.find, lines = ref$.lines, sortBy = ref$.sortBy, findIndex = ref$.findIndex, reverse = ref$.reverse;
    $scope.baskets = [];
    $scope.copies = [];
    $scope.alerts = [];
    $scope.show_buttons = {};
    $scope.new_name = null;
    $scope.cur_basket = undefined;
    $scope.cards_fetched = [];
    $scope.copy_selected = undefined;
    $scope.show_images = false;
    COMMAND_BASKET_ID = 1;
    $scope.language = utils.url_language($window.location.pathname);
    $scope.showing_notes = false;
    $scope.last_sort = "title";
    $scope.page = 1;
    $scope.page_size = 25;
    $scope.page_sizes = [25, 50, 100, 200];
    $scope.page_max = 1;
    $scope.meta = {
      num_pages: null,
      nb_results: null
    };
    page_size = $window.localStorage.getItem("baskets_page_size");
    if (page_size !== null) {
      $scope.page_size = parseInt(page_size);
    }
    $http.get("/api/returns").then(function(response){
      "Get the returnBaskets, do not show the \"to command\" one, of id=1.";
      var hash_basket_id, index;
      hash_basket_id = parseInt($location.hash(), 10);
      index = findIndex(function(it){
        return hash_basket_id === it.id;
      }, $scope.baskets);
      if (!index) {
        index = 0;
      }
      $scope.cur_basket_index = index;
      $log.info("index: ", index);
      return $scope.showBasket(index);
    });
    $scope.save_basket = function(){
      var params;
      params = {
        comment: $scope.cur_basket.comment
      };
      $log.info("updating basket " + $scope.cur_basket.id + "…");
      $http.post("/api/baskets/" + $scope.cur_basket.id + "/update/", params).then(function(response){
        var resp;
        return resp = response.data;
      });
    };
    $scope.getCopies = function(index){
      var params;
      if ($scope.cur_basket) {
        params = {
          page_size: $scope.page_size,
          page: $scope.page
        };
        $http.get("/api/returns/" + $scope.cur_basket.id + "/copies", {
          params: params
        }).then(function(response){
          $scope.baskets[index].copies = response.data.data;
          $scope.meta = response.data.meta;
          $scope.copies = response.data.data;
        });
      }
    };
    $scope.showBasket = function(index){
      "Show the copies of the given basket.";
      $scope.cur_basket = $scope.baskets[index];
      if ($scope.cur_basket) {
        $location.hash($scope.cur_basket.id);
        $window.document.title = "Abelujo - " + gettext("Returns") + ", " + $scope.cur_basket.name;
        $window.localStorage.setItem('cur_basket_id', $scope.cur_basket.id);
        if (!$scope.cur_basket.copies) {
          $scope.getCopies(index);
        } else {
          $scope.copies = $scope.cur_basket.copies;
        }
        angular.element('#default-input').trigger('focus');
      }
    };
    $scope.archive_basket = function(){
      var sure;
      sure = confirm(gettext("Are you sure to archive this list {}?").replace("{}", $scope.cur_basket.name));
      if (sure) {
        $http.post("/api/baskets/" + $scope.cur_basket.id + "/archive").then(function(response){
          var index;
          index = findIndex(function(it){
            return it.id === $scope.cur_basket.id;
          }, $scope.baskets);
          $scope.baskets.splice(index, 1);
          if (index >= $scope.baskets.length) {
            index -= 1;
          }
          $scope.showBasket(index);
        });
      }
    };
    $scope.delete_basket = function(){
      var sure;
      sure = confirm(gettext("You are going to delete the list {}. This can not be undone. Are you sure ?").replace("{}", $scope.cur_basket.name));
      $log.info(sure);
      if (sure) {
        $http.post("/api/baskets/" + $scope.cur_basket.id + "/delete").then(function(response){
          var index;
          index = findIndex(function(it){
            return it.id === $scope.cur_basket.id;
          }, $scope.baskets);
          $scope.baskets.splice(index, 1);
          if (index >= $scope.baskets.length) {
            index -= 1;
          }
          $scope.showBasket(index);
        });
      }
    };
    $window.document.title = "Abelujo - " + gettext("Baskets");
    $scope.closeAlert = function(index){
      return $scope.alerts.splice(index, 1);
    };
    $scope.getCards = function(query){
      var args, promise;
      args = {
        query: query,
        language: $scope.language,
        lang: $scope.language
      };
      promise = utils.getCards(args);
      if (promise) {
        return promise.then(function(res){
          $scope.cards_fetched = res;
          if (utils.is_isbn(query) && res.length === 1) {
            setTimeout(function(){
              $window.document.getElementById("default-input").value = "";
              return $scope.add_selected_card(res[0]);
            }, 700);
            return;
          }
          return res;
        });
      }
    };
    $scope.add_selected_card = function(card){
      " Add the card selected from the autocomplete to the current list's copies.\nSave it.";
      var tmpcard, index;
      tmpcard = find(function(it){
        return it.repr === card.repr;
      })(
      $scope.cards_fetched);
      tmpcard = tmpcard.item;
      index = 0;
      index = findIndex(function(it){
        return tmpcard.title < it.title;
      }, $scope.copies);
      if (!index) {
        index = $scope.copies.length;
      }
      $scope.copies.splice(index, 0, tmpcard);
      $scope.copy_selected = undefined;
      $scope.save_card_to_basket(tmpcard.id, $scope.cur_basket.id);
    };
    $scope.save_card_to_basket = function(card_id, basket_id){
      var coma_sep, params;
      coma_sep = card_id + "";
      params = {
        card_ids: coma_sep
      };
      $http.post("/api/baskets/" + basket_id + "/add/", params).then(function(response){
        $log.info("added cards to basket");
      }, function(response){
        throw Error('unimplemented');
      });
    };
    $scope.save_quantity = function(index){
      "Save the item quantity.";
      var card;
      card = $scope.copies[index];
      utils.save_quantity(card, $scope.cur_basket.id);
    };
    $scope.command = function(){
      "Add the copies of the current basket to the Command basket. Api call.";
      var text, sure, params;
      if (!confirm(gettext("You didn't set a supplier for this list (menu -> set a supplier). Do you want to carry on ?"))) {
        return;
      }
      $log.info("cur_basket: ", $scope.cur_basket);
      $log.info("copies: ", $scope.copies);
      if (!$scope.copies.length) {
        alert(gettext("This basket has no copies to command !"));
        return;
      }
      text = gettext("Do you want to mark all the cards of this list to command ?");
      if ($scope.cur_basket.distributor) {
        text += gettext(" They will be associated with the supplier " + $scope.cur_basket.distributor + ".");
      }
      sure = confirm(text);
      if (sure) {
        params = {
          basket_id: $scope.cur_basket.id
        };
        $http.post("/api/baskets/" + COMMAND_BASKET_ID + "/add/", params).then(function(response){
          $scope.alerts = response.data.alerts;
        });
      }
    };
    $scope.remove_from_selection = function(index_to_rm){
      "Remove the card from the list. Server call to the api.";
      var card_id;
      card_id = $scope.copies[index_to_rm].id;
      $http.post("/api/baskets/" + $scope.cur_basket.id + "/remove/" + card_id + "/").then(function(response){
        $scope.copies.splice(index_to_rm, 1);
      })['catch'](function(resp){
        $log.info("Error when trying to remove the card " + card_id);
      });
    };
    $scope.get_data = function(){
      return join(",")(
      map(function(it){
        return it.id;
      })(
      $scope.cur_basket.copies));
    };
    $scope.get_total_price = function(){
      return utils.total_price($scope.copies);
    };
    $scope.get_total_copies = function(){
      return utils.total_copies($scope.copies);
    };
    $scope.receive_command = function(){
      var sure;
      if (!$scope.cur_basket.distributor) {
        alert("You didn't set a distributor for this basket. Please see the menu Action -> set the supplier.");
        return;
      }
      sure = confirm(gettext("Do you want to receive a command for the supplier '" + $scope.cur_basket.distributor + "' ?"));
      if (sure) {
        $http.get("/api/baskets/" + $scope.cur_basket.id + "/inventories/").then(function(response){
          var inv_id;
          inv_id = response.data.data.inv_id;
          $window.location.href = "/" + $scope.language + "/inventories/" + inv_id + "/";
        });
      }
    };
    $scope.return_to_supplier = function(){
      var sure;
      if (!$scope.cur_basket.distributor) {
        alert("You didn't set a distributor for this basket. Please see the menu Action -> set the supplier.");
        return;
      }
      sure = confirm(gettext("Do you want to return this basket to " + $scope.cur_basket.distributor + " ? This will remove the given quantities from your stock."));
      if (sure) {
        $http.post("/api/baskets/" + $scope.cur_basket.id + "/return").then(function(response){
          $log.info(response);
          $scope.alerts = response.data.alerts;
        });
      }
    };
    $scope.$watch("page_size", function(){
      $window.localStorage.baskets_page_size = $scope.page_size;
      $scope.getCopies($scope.cur_basket_index);
    });
    $scope.nextPage = function(){
      if ($scope.page < $scope.meta.num_pages) {
        $scope.page += 1;
        $log.info("-- cur_basket_index: ", $scope.cur_basket_index);
        $scope.getCopies($scope.cur_basket_index);
      }
    };
    $scope.lastPage = function(){
      $scope.page = $scope.meta.num_pages;
      $scope.getCopies($scope.cur_basket_index);
    };
    $scope.previousPage = function(){
      if ($scope.page > 1) {
        $scope.page -= 1;
        $scope.getCopies($scope.cur_basket_index);
      }
    };
    $scope.firstPage = function(){
      $scope.page = 1;
      $scope.getCopies($scope.cur_basket_index);
    };
    $scope.open_new_basket = function(size){
      var modalInstance;
      modalInstance = $uibModal.open({
        animation: $scope.animationsEnabled,
        templateUrl: 'basketModal.html',
        controller: 'BasketModalControllerInstance',
        size: size,
        resolve: {
          utils: function(){
            return utils;
          }
        }
      });
      modalInstance.result.then(function(basket){
        $scope.baskets.push(basket);
        $log.info("new basket: ", basket);
        $log.info("all baskets: ", $scope.baskets);
      }, function(){
        $log.info("modal dismissed");
      });
    };
    $scope.add_to_shelf = function(cur_basket_id){
      var modalInstance;
      $log.info("add_to_shelf got basket id", cur_basket_id);
      modalInstance = $uibModal.open({
        animation: $scope.animationsEnabled,
        templateUrl: 'chooseShelfModal.html',
        controller: 'ChooseShelfModalControllerInstance',
        cur_basket_id: cur_basket_id,
        resolve: {
          utils: function(){
            return utils;
          }
        }
      });
      modalInstance.result.then(function(basket){
        basket = $scope.baskets[cur_basket_id];
        basket.copies = [];
        $scope.copies = [];
        $log.info("modal ok");
      }, function(){
        $log.info("modal dismissed");
      });
    };
    $scope.toggle_images = function(){
      $scope.show_images = !$scope.show_images;
    };
    $scope.sort_by = function(key){
      if ($scope.last_sort === key) {
        $scope.copies = reverse(
        $scope.copies);
      } else {
        $scope.copies = sortBy(function(it){
          return it[key];
        })(
        $scope.copies);
        $scope.last_sort = key;
      }
      $log.info($scope.copies);
    };
    hotkeys.bindTo($scope).add({
      combo: "d",
      description: gettext("show or hide the book details in tables."),
      callback: function(){
        $scope.toggle_images();
      }
    }).add({
      combo: "s",
      description: gettext("go to the search box"),
      callback: function(){
        utils.set_focus();
      }
    }).add({
      combo: "n",
      description: gettext("hide or show your notes"),
      callback: function(){
        $scope.showing_notes = !$scope.showing_notes;
      }
    }).add({
      combo: "C",
      description: gettext("Create a new list"),
      callback: function(){
        $scope.open();
      }
    });
  }
]);
angular.module("abelujo").controller("ChooseShelfModalControllerInstance", function($http, $scope, $uibModalInstance, $window, $log, utils){
  utils.set_focus();
  $scope.shelves = [];
  $scope.selected_shelf = null;
  $log.info("cur_basket_id storage: ", $window.localStorage.getItem('cur_basket_id'));
  $scope.cur_basket_id = $window.localStorage.getItem('cur_basket_id');
  $http.get("/api/shelfs").then(function(response){
    $log.info("response: ", response);
    $scope.shelves = response.data;
    return $log.info("shelves: ", $scope.shelves);
  });
  $scope.ok = function(){
    var config, params;
    if (typeof $scope.selected_shelf === "undefined" || $scope.selected_shelf === "") {
      $uibModalInstance.dismiss('cancel');
      return;
    }
    $log.info("selected shelf: ", $scope.selected_shelf);
    $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8';
    $http.defaults.transformRequest = utils.transformRequestAsFormPost;
    config = {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
      }
    };
    params = {
      shelf_id: $scope.selected_shelf.pk
    };
    $http.post("/api/baskets/" + $scope.cur_basket_id + "/add_to_shelf/", params).then(function(response){
      $scope.alerts = response.data.alerts;
      $uibModalInstance.close();
      $scope.alerts = response.data.alerts;
    });
  };
  $scope.cancel = function(){
    $uibModalInstance.dismiss('cancel');
    $scope.alerts = response.data.alerts;
  };
});

angular.module("abelujo").controller('searchResultsController', [
  '$http', '$scope', '$timeout', '$filter', '$window', '$uibModal', '$log', 'utils', '$location', 'hotkeys', function($http, $scope, $timeout, $filter, $window, $uibModal, $log, utils, $location, hotkeys){
    var ref$, Obj, join, reject, sum, map, filter, find, lines, defaultdatasource, datasource, search_obj, previous_query, source_id, datasource_id;
    ref$ = require('prelude-ls'), Obj = ref$.Obj, join = ref$.join, reject = ref$.reject, sum = ref$.sum, map = ref$.map, filter = ref$.filter, find = ref$.find, lines = ref$.lines;
    $scope.language = utils.url_language($window.location.pathname);
    $scope.not_available_status = ["Indisponible temporairement", "Indisponible", "Epuise", "epuise", "Epuisé", "epuisé", "06", "6", "7", "Manque sans date"];
    $scope.is_not_available = function(label){
      return in$(label, $scope.not_available_status);
    };
    $scope.cards = [];
    $scope.data = {};
    $scope.alerts = [];
    $scope.page = 1;
    $scope.selectAll = true;
    $scope.datasources = [
      {
        name: "librairiedeparis - fr",
        id: "librairiedeparis"
      }, {
        name: "dilicom - fr",
        id: "dilicom"
      }, {
        name: "electre - fr",
        id: "electre"
      }, {
        name: "lelivre - ch",
        id: "lelivre"
      }, {
        name: "Casa del libro - es",
        id: "casadellibro"
      }, {
        name: "Belgique - be",
        id: "filigranes"
      }, {
        name: "Bookdepository",
        id: "bookdepository"
      }, {
        name: "DVDs",
        id: "momox"
      }, {
        name: "discogs - CDs",
        id: "discogs"
      }
    ];
    defaultdatasource = $window.document.getElementById('defaultdatasource');
    if (defaultdatasource) {
      defaultdatasource = defaultdatasource.textContent;
      datasource = find(function(it){
        return it.id === defaultdatasource;
      })(
      $scope.datasources);
      $scope.datasource = datasource;
    }
    $scope.results_page = [];
    $scope.show_images = true;
    $scope.saveDatasource = function(){
      $window.localStorage.setItem('datasource', $scope.datasource.id);
    };
    $scope.details_url_for = function(card){
      if (card.in_stock !== null) {
        return card.get_absolute_url;
      }
      if (card.details_url) {
        return card.details_url;
      }
      return null;
    };
    $scope.next_results = function(){
      var search_obj, page;
      if (!$scope.query) {
        return;
      }
      search_obj = $location.search();
      page = search_obj.page;
      if (!page) {
        page = "1";
      }
      page = parseInt(page, 10);
      page += 1;
      $scope.page = page;
      $location.search('page', page);
      $scope.validate();
    };
    $scope.previous_results = function(){
      var search_obj, page;
      if (!$scope.query) {
        return;
      }
      search_obj = $location.search();
      page = search_obj.page;
      if (!page) {
        page = "1";
      }
      page = parseInt(page, 10);
      page -= 1;
      if (page < 1) {
        page = 1;
      }
      $scope.page = page;
      $location.search('page', page);
      $scope.validate();
    };
    $scope.validate = function(){
      $scope.validate_with_query($scope.query);
    };
    $scope.validate_with_query = function(query){
      "Search for cards.";
      var search_obj, cache, params;
      if (!query) {
        return;
      }
      $location.search('q', query);
      $location.search('source', $scope.datasource.id);
      search_obj = $location.search();
      cache = find(function(it){
        return it.page === $scope.page && it.query === query && it.datasource === $scope.datasource.id;
      })(
      $scope.results_page);
      if (cache) {
        $scope.cards = cache.cards;
        $window.document.getElementById("default-input").select();
        return;
      }
      params = {
        query: query,
        datasource: search_obj.source,
        page: search_obj.page,
        language: $scope.language
      };
      $http.get("/api/datasource/search/", {
        params: params
      }).then(function(response){
        var i$, ref$, len$, card;
        $window.document.title = "Abelujo - " + gettext("search") + " " + query;
        $scope.cards = response.data.data;
        $window.document.getElementById("default-input").select();
        if (response.data.data.length === 0) {
          $scope.no_results = true;
        } else {
          $scope.no_results = false;
        }
        $scope.data = response.data;
        for (i$ = 0, len$ = (ref$ = $scope.cards).length; i$ < len$; ++i$) {
          card = ref$[i$];
          card.selected = false;
        }
        $scope.results_page.push({
          cards: $scope.cards,
          page: $scope.page,
          query: query,
          datasource: $scope.datasource.id
        });
      }, function(response){
        $scope.alerts.push({
          level: 'danger',
          message: gettext("Internal error, sorry ! We've been notified about it.")
        });
      });
    };
    search_obj = $location.search();
    previous_query = search_obj.q;
    source_id = search_obj.source;
    if (source_id) {
      $scope.datasource = find(function(it){
        return it.id === source_id;
      })(
      $scope.datasources);
      if (!$scope.datasource) {
        $scope.datasource = $scope.datasources[0];
      }
    } else {
      datasource_id = $window.localStorage.getItem("datasource");
      if (datasource_id) {
        $scope.datasource = find(function(it){
          return it.id === datasource_id;
        })(
        $scope.datasources);
      } else {
        $scope.datasource = $scope.datasources[0];
      }
    }
    $scope.validate_with_query(previous_query);
    $window.document.title = "Abelujo - " + gettext("search") + " " + previous_query;
    $scope.toggleAll = function(){
      var i$, ref$, len$, card;
      for (i$ = 0, len$ = (ref$ = $scope.cards).length; i$ < len$; ++i$) {
        card = ref$[i$];
        card.selected = $scope.selectAll;
      }
      $scope.selectAll = !$scope.selectAll;
    };
    $scope.toggle_images = function(){
      $scope.show_images = !$scope.show_images;
    };
    $scope.closeAlert = function(index){
      $scope.alerts.splice(index, 1);
    };
    $scope.create_and_add = function(card){
      var params;
      params = {
        card: card
      };
      $http.post("/api/cards/create", params).then(function(response){
        var query, card_id;
        query = $location.search().q;
        card_id = response.data.card_id;
        if (card_id) {
          $window.location.href = "/" + $scope.language + "/stock/card/create/" + card_id + "?q=" + query + "&source=" + $scope.datasource.id;
        } else {
          $scope.alerts.push({
            level: 'danger',
            message: gettext("Server error… sorry !")
          });
        }
      }, function(response){
        throw Error('unimplemented');
      });
    };
    $scope.create_and_command_client = function(card){
      var params;
      $log.info("card: ", card);
      $log.info("isbn: ", card.isbn);
      params = {
        card: card
      };
      $http.post("/api/cards/create", params).then(function(response){
        var card_id;
        card_id = response.data.card_id;
        if (card_id) {
          $window.location.href = "/" + $scope.language + "/command/" + card_id + "?q=" + $scope.query + "&source=" + $scope.datasource.id;
        } else {
          $scope.alerts.push({
            level: 'danger',
            message: gettext("Server error… sorry !")
          });
        }
      }, function(response){
        throw Error('unimplemented');
      });
    };
    $scope.do_card_command = function(isbn){
      var params;
      if (!isbn) {
        alert("Ce livre n'a pas d'ISBN ! Commande impossible.");
        return;
      }
      $log.info("--- do_card_command ", isbn);
      params = {
        isbn: isbn,
        command: true
      };
      $http.post("/api/cards/quickcreate/", params).then(function(response){
        $log.info(response);
        Notiflix.Notify.Success("Commandé");
      });
    };
    $scope.add_to_command = function(size){
      var to_add, keys, params;
      to_add = Obj.filter(function(it){
        return it.selected === true;
      }, $scope.cards);
      keys = Obj.keys(to_add);
      if (!keys.length) {
        alert("Please select some cards first");
        return;
      }
      params = {
        cards: to_add
      };
      $http.post("/api/baskets/1/add/", params).then(function(response){
        var card_id;
        card_id = response.data.card_id;
      });
    };
    $scope.open_list_select = function(size){
      var to_add, keys, modalInstance;
      to_add = Obj.filter(function(it){
        return it.selected === true;
      }, $scope.cards);
      keys = Obj.keys(to_add);
      if (!keys.length) {
        alert("Please select some cards first");
        return;
      }
      modalInstance = $uibModal.open({
        animation: $scope.animationsEnabled,
        templateUrl: 'SearchResultsModal.html',
        controller: 'SearchResultsModalControllerInstance',
        size: size,
        resolve: {
          selected: function(){
            return to_add;
          },
          utils: function(){
            return utils;
          }
        }
      });
      modalInstance.result.then(function(alerts){
        $scope.alerts = alerts;
      }, function(){
        $log.info("modal dismissed");
      });
    };
    $scope.open_inv_select = function(size){
      var to_add, keys, modalInstance;
      to_add = Obj.filter(function(it){
        return it.selected === true;
      }, $scope.cards);
      keys = Obj.keys(to_add);
      if (!keys.length) {
        alert("Please select some cards first");
        return;
      }
      modalInstance = $uibModal.open({
        animation: $scope.animationsEnabled,
        templateUrl: 'SearchResultsAddToInventoryModal.html',
        controller: 'SearchResultsAddToInventoryModalController',
        size: size,
        resolve: {
          cards_selected: function(){
            return to_add;
          },
          utils: function(){
            return utils;
          }
        }
      });
      modalInstance.result.then(function(alerts){
        $scope.alerts = alerts;
      }, function(){
        $log.info("modal dismissed");
      });
    };
    utils.set_focus();
    hotkeys.bindTo($scope).add({
      combo: "d",
      description: gettext("show or hide the book details in tables."),
      callback: function(){
        $scope.toggle_images();
      }
    }).add({
      combo: "s",
      description: gettext("go to the search box"),
      callback: function(){
        utils.set_focus();
      }
    });
  }
]);
angular.module("abelujo").controller("SearchResultsModalControllerInstance", function($http, $scope, $uibModalInstance, $window, $log, utils, selected){
  var ref$, Obj, join, sum, map, filter, lines, tail;
  ref$ = require('prelude-ls'), Obj = ref$.Obj, join = ref$.join, sum = ref$.sum, map = ref$.map, filter = ref$.filter, lines = ref$.lines, tail = ref$.tail;
  $scope.selected_baskets = {};
  $scope.alerts = [];
  $http.get("/api/baskets").then(function(response){
    $scope.baskets = tail(response.data.data);
  });
  $scope.ok = function(){
    var to_add, baskets_ids, config, params, i$, len$, b_id;
    to_add = selected;
    baskets_ids = Obj.keys(
    Obj.filter(function(it){
      return it === true;
    })(
    $scope.selected_baskets));
    config = {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
      }
    };
    params = {
      cards: to_add
    };
    for (i$ = 0, len$ = baskets_ids.length; i$ < len$; ++i$) {
      b_id = baskets_ids[i$];
      $log.info("Adding cards to basket " + b_id + "...");
      $http.post("/api/baskets/" + b_id + "/add/", params).then(fn$);
    }
    $uibModalInstance.close($scope.alerts);
    function fn$(response){
      $scope.alerts = $scope.alerts.concat(response.data.msgs);
    }
  };
  $scope.cancel = function(){
    $uibModalInstance.dismiss('cancel');
  };
});
angular.module("abelujo").controller("SearchResultsAddToInventoryModalController", function($http, $scope, $uibModalInstance, $window, $log, utils, cards_selected){
  var ref$, Obj, join, sum, map, filter, lines;
  ref$ = require('prelude-ls'), Obj = ref$.Obj, join = ref$.join, sum = ref$.sum, map = ref$.map, filter = ref$.filter, lines = ref$.lines;
  $scope.inventory = undefined;
  $scope.alerts = [];
  $http.get("/api/inventories").then(function(response){
    $scope.inventories = response.data.data;
  });
  $scope.ok = function(){
    var to_add, config, params;
    to_add = cards_selected;
    config = {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
      }
    };
    params = {
      cards: to_add
    };
    $log.info("Adding cards to inventory " + $scope.inventory.id + "...");
    $log.info("Adding cards", to_add);
    $http.post("/api/inventories/" + $scope.inventory.id + "/update/", params).then(function(response){
      $scope.alerts = $scope.alerts.concat(response.data.msgs);
    });
    $uibModalInstance.close($scope.alerts);
  };
  $scope.cancel = function(){
    $uibModalInstance.dismiss('cancel');
  };
});
function in$(x, xs){
  var i = -1, l = xs.length >>> 0;
  while (++i < l) if (x === xs[i]) return true;
  return false;
}