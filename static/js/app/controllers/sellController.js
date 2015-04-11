angular.module("abelujo").controller('sellController', ['$http', '$scope', '$timeout', '$window', function ($http, $scope, $timeout, $window) {
      // set the xsrf token via cookies.
      // $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;
      $scope.dist_list = [];
      $scope.distributor = undefined;
      $scope.copy_selected = undefined;
      $scope.cards_selected = [];
      // Remember the pairs card representation / object from the model.
      $scope.cards_fetched = [];
      //TODO: use django-angular to limit code duplication.
      $scope.card_types = [
          // WARNING duplication from dbfixture.json
          {name:"all", id:null},
          {name:"book", group:"livre",        id:1},
          {name:"booklet", group:"livre",     id:2},
          {name:"newspaper", group:"livre",   id:3},
          {name:"other print", group:"livre", id:4},
          {name:"CD", group:"CD",             id:5},
          {name:"DVD", group:"CD",            id:6},
          {name:"vinyl", group:"CD",          id:8},
          {name:"autres", group:"autres",     id:9},
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
                  $scope.dist_list.push(item.fields.name);
              });

          });

      $scope.getCards = function(val){
          return $http.get("/api/cards", {
              params: {
                  "query": val,
                  "card_type_id": $scope.card_type.id,
              }})
              .then(function(response){ // "then", not "success"
                  return response.data.map(function(item){
                      // give a string representation for each object (result)
                      // xxx: take the repr from django
                      // return item.title + ", " + item.authors + ", éd. " + item.publishers;
                      var repr = item.title + ", " + item.authors + ", éd. " + item.publishers;
                      $scope.cards_fetched.push({"repr": repr,
                                                 "id": item.id,
                                                 "item": item,});
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
          // TODO: don't put duplicates. ONGOING !
          if (! _.contains($scope.selected_ids, $scope.tmpcard.id)) {
              $scope.cards_selected.push($scope.tmpcard);
              $scope.total_price += $scope.tmpcard.price;
              $scope.selected_ids.push($scope.tmpcard.id);
          };
          $scope.copy_selected = undefined;
      };

      $scope.remove_from_selection = function(index_to_rm){
          $scope.total_price -= $scope.cards_selected[index_to_rm].price;
          $scope.selected_ids.splice(index_to_rm, 1);
          $scope.cards_selected.splice(index_to_rm, 1);
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
                                          return memo + it.price_sold;},
                                      0)
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
          var cards_id = [];
          // get the selected card's id TODO:
          if ($scope.cards_selected.length > 0) {
              cards_id = _.map($scope.cards_selected, function(card) {
                  return card.id;
              });
          }

          var params = {
              "cards_id": cards_id,
          };

          // This is needed for Django to process the params to its
          // request.POST dictionnary:
          $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8';

          // We need not to pass the parameters encoded as json to Django.
          // Encode them like url parameters.
          // TODO: put in a service.
          var transformRequestAsFormPost = function(obj){
              var str = [];
              for(var p in obj)
                  str.push(encodeURIComponent(p) + "=" + encodeURIComponent(obj[p]));
              return str.join("&");
          };
          $http.defaults.transformRequest = transformRequestAsFormPost; // don't transfrom params to json.
          var config = {
              headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
          };

          return $http.post("/api/sell", params)
              .then(function(response){
                  // Display server messages.
                  $scope.alerts = response.data;

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

    $scope.formats = ['dd.MM.yyyy', 'dd-MMMM-yyyy', 'yyyy/MM/dd', 'shortDate'];
    $scope.format = $scope.formats[0];

  }]);
