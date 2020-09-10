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
                query: val
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
    };

    $http.get("/api/places")
        .then(function(response) {
            $scope.places = [{"name": "", "id": 0}];
            $scope.places = $scope.places.concat(response.data);
        });

      // Fetch cards for the autocomplete.
      // Livescript version: see basketsController.ls
      $scope.getCards = function(val){

          if ($scope.all_digits_re.test(val)) {
              if (val.length < 13) {
                  console.log("--- dismissing ", val);
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
          // $scope.cards_selected.push(card);
          $scope.tmpcard = _.filter($scope.cards_fetched, function(it){
              return it.repr === card.repr;
          }) ;
          $scope.tmpcard = $scope.tmpcard[0].item;
          $scope.tmpcard.price_orig = $scope.tmpcard.price_sold;
          if (!_.contains($scope.selected_ids, $scope.tmpcard.id)) {
              $scope.cards_selected.push($scope.tmpcard);
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

          // Prevent from quitting the page when sells are entered but not confirmed.
          $window.addEventListener('beforeunload', unloadlistener);
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

    $scope.sellCardsWith = function(payment) {
        console.log("Sell with ", payment);
        $scope.payment = payment;
        $scope.sellCards();
    };

    $scope.sellCards = function() {
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

        var params = {
            "to_sell": [ids, prices, quantities],
            "date": $filter('date')($scope.date, $scope.format, 'UTC') .toString($scope.format),
            "language": $scope.language,
            "place_id": place_id,
            "payment_id": payment_id
        };

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

                  return response.data;
              });
      };

    $scope.cancelCurrentData = function() {
        $scope.total_price = null;
        $scope.selected_ids = [];
        $scope.cards_selected = [];
        $scope.cards_fetched = [];
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
        };

        if ($scope.client !== undefined) {
            params['client_id'] = $scope.client.id;
        }

        $http.post("/api/bill", params)
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
    angular.element('#default-input').trigger('focus');

    $window.document.title = "Abelujo - " + gettext("Sell");

    function unloadlistener (event) {
        // Cancel the event as stated by the standard.
        event.preventDefault();
        // Chrome requires returnValue to be set.
        event.returnValue = '';
    };

  }]);
