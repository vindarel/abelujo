angular.module("abelujo").controller('inventoryNewController', ['$http', '$scope', '$timeout', 'utils', '$filter', function ($http, $scope, $timeout, utils, $filter) {
    // utils: in services.js

    // set the xsrf token via cookies.
    // $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;

    $scope.copy_selected = undefined;
    $scope.history = [];
    $scope.cards_selected = [];
    $scope.cards_fetched = [];
      $scope.tmpcard = undefined;
      $scope.selected_ids = [];
    var existing_card = undefined;

    $scope.getCards = function(val){
        return $http.get("/api/cards", {
            params: {
                "query": val,
                "card_type_id": null,
            }})
            .then(function(response){
                return response.data.map(function(item){
                    // give a string representation for each object (result)
                    // xxx: take the repr from django
                    // return item.title + ", " + item.authors + ", éd. " + item.publishers;
                    var repr = item.title + ", " + item.authors + ", éd. " + item.publishers;
                    item.quantity = 1;
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
          // TODO: don't put duplicates. ONGOING !
          if (! _.contains($scope.selected_ids, $scope.tmpcard.id)) {
              $scope.cards_selected.push($scope.tmpcard);
              $scope.selected_ids.push($scope.tmpcard.id);
          }
          else {
              existing_card = _.filter($scope.cards_selected, function(it){
                  return it.id == $scope.tmpcard.id;
              });
              existing_card = existing_card[0];
              existing_card.quantity += 1;
          };

          $scope.copy_selected = undefined;
      };

    $scope.remove_from_selection = function(index_to_rm){
        $scope.selected_ids.splice(index_to_rm, 1);
        $scope.cards_selected.splice(index_to_rm, 1);
        $scope.updateTotalPrice();
    };


}]);
