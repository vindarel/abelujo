angular.module("abelujo").controller('sellController', ['$http', '$scope', '$timeout', 'utils', '$filter', '$window', '$log', function ($http, $scope, $timeout, utils, $filter, $window, $log) {
    // utils: in services.js

      $scope.language = utils.url_language($window.location.pathname);

      // set the xsrf token via cookies.
      // $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;
      $scope.dist_list = [];

    // List of places we can sell from.
    $scope.places = [];
    $scope.place = undefined;

    // List of deposits.
    $scope.deposits = [];
    $scope.deposit = undefined;

      $scope.distributor = undefined;
      $scope.copy_selected = undefined;
    // List of the cards we're going to sell.
    // Objects augmented with price_orig, quick_discount
      $scope.cards_selected = [];
      // Remember the pairs card representation / object from the model.
      $scope.cards_fetched = [];
      //TODO: use django-angular to limit code duplication.
      $scope.card_types = [
          // WARNING duplication from dbfixture.json
          {name: gettext("all publication"), id:null},
          {name: gettext("book"), group: gettext("book"), id:1},
          {name: gettext("booklet"), group: gettext("book"),id:2},
          {name: gettext("periodical"), group: gettext("book"), id:3},
          {name: gettext("other print"), group: gettext("book"), id:4},
          {name: gettext("CD"), group: gettext("CD"), id:5},
          {name: gettext("DVD"), group: gettext("CD"), id:6},
          {name: gettext("vinyl"), group: gettext("CD"), id:8},
          {name: gettext("others"), group: gettext("others"), id:9},
      ];

      $scope.payment_means = [
          {name: gettext("cash"), id:1},
          {name: gettext("cheque"), id:2},
          {name: gettext("visa card"), id:3},
          {name: gettext("gift"), id:4},
          {name: gettext("transfer"), id:6},
          {name: gettext("other"), id:5},
      ];
      $scope.payment = $scope.payment_means[0];

    $scope.discounts = {};
    // and store the selected discount in this object.
    // For the first time had pbs with another variable.
    $scope.discounts.choices = [
        {discount: 0,
         name: "0%", // caution. a "" may introduce a bug
         id:1},
        {discount: 5,
         name: "5%",
         id:2
        },
        {discount: 30,
         name: "30%",
         id:3}
    ];

      $scope.card_type = $scope.card_types[0];
      $scope.tmpcard = undefined;
      $scope.selected_ids = [];
      $scope.total_price = 0;

      // messages for ui feedback: list of couple level/message
      $scope.alerts = undefined;


      $http.get("/api/distributors")
          .then(function(response){ // "then", not "success"
              return response.data.map(function(item){
                  // give a string representation for each object (result)
                  $scope.dist_list.push(item.name);
              });

          });

    $http.get("/api/places")
        .then(function(response) {
            $scope.places = [{"name": "", "id": 0}];
            $scope.places = $scope.places.concat(response.data);
        });

    $http.get("/api/deposits")
        .then(function(response) {
            $scope.deposits = [{"name": "", "id": 0}];
            $scope.deposits = $scope.deposits.concat(response.data.data);
        });

      // Fetch cards for the autocomplete.
      // Livescript version: see basketsController.ls
      $scope.getCards = function(val){

          var deposit_id = 0;
          if ($scope.deposit) {
              deposit_id = $scope.deposit.id;
          }
          var place_id = 0;
          if ($scope.place) {
              place_id = $scope.place.id;
          }

          return $http.get("/api/cards", {
              params: {
                  "query": val,
                  "lang": $scope.language,
                  "language": $scope.language,
                  "deposit_id": deposit_id,
                  "place_id": place_id,
                  "card_type_id": $scope.card_type.id
              }})
              .then(function(response){ // "then", not "success"
                  return response.data.cards.map(function(item){
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
              });
      };

      $scope.add_selected_card = function(card_repr){
          // $scope.cards_selected.push(card_repr);
          $scope.tmpcard = _.filter($scope.cards_fetched, function(it){
              return it.repr === card_repr.repr;
          }) ;
          $scope.tmpcard = $scope.tmpcard[0].item;
          $scope.tmpcard.price_orig = $scope.tmpcard.price_sold;
          if (!_.contains($scope.selected_ids, $scope.tmpcard.id)) {
              $scope.cards_selected.push($scope.tmpcard);
              $scope.total_price += $scope.tmpcard.price;
              $scope.selected_ids.push($scope.tmpcard.id);
          } else {
              var existing = _.find($scope.cards_selected, function(it){
                  return it.id === card_repr.id;
              });
              existing.quantity_sell += 1;
          }
          $scope.copy_selected = undefined;
          $scope.updateTotalPrice();
          $scope.alerts = [];
      };

      $scope.remove_from_selection = function(index_to_rm){
          $scope.selected_ids.splice(index_to_rm, 1);
          $scope.cards_selected.splice(index_to_rm, 1);
          $scope.updateTotalPrice();
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
                            return memo + it.quantity_sell;},
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
        var deposit_id = 0;
        if ($scope.deposit) {
            deposit_id = $scope.deposit.id;
        }

        var params = {
            "to_sell": [ids, prices, quantities],
            "date": $filter('date')(new Date(), $scope.format, 'UTC') .toString($scope.format),
            "language": $scope.language,
            "place_id": place_id,
            "deposit_id": deposit_id
        };

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
                  return response.data;
              });
      };

    $scope.cancelCurrentData = function() {
        $scope.total_price = null;
        $scope.selected_ids = [];
        $scope.cards_selected = [];
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

  }]);
