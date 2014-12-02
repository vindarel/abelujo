angular.module('abelujo.controllers', [])
  .controller('IntroController', ['$http', '$scope', function ($http, $scope) {
      // set the xsrf token via cookies.
      // $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;
      $scope.dist_list = [];
      $scope.distributor = undefined;
      $scope.copy_selected = undefined;
      $scope.cards_selected = [];
      // Remember the pairs card representation / object from the model.
      $scope.cards_fetched = [];
      //TODO: use django-angular to limit code duplication.
      $scope.deposit_types = [
          {name:"depôt fixe", target:"dépôt de libraire"},
          {name:"depôt libraire", target:"dépôt de distributeur"},
          {name:"distributeur", target:"dépôt de distributeur"}
      ];

      $scope.deposit_type = $scope.deposit_types[0];
      $scope.deposit_name = undefined;
      $scope.initial_nb = 1;
      $scope.minimal_nb = 1;
      $scope.auto_command = undefined;

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
                  "distributor": $scope.distributor,
              }})
              .then(function(response){ // "then", not "success"
                  return response.data.map(function(item){
                      // give a string representation for each object (result)
                      // xxx: take the repr from django
                      // return item.title + ", " + item.authors + ", éd. " + item.publishers;
                      var repr = item.title + ", " + item.authors + ", éd. " + item.publishers;
                      $scope.cards_fetched.push({"repr": repr, "id": item.id});
                      return {"repr": repr,
                              "id": item.id};
                  });
              });
      };

      $scope.addDeposit = function() {
          var cards_id = [];
          // get the selected card's id TODO:
          if ($scope.cards_selected.length > 0) {
              cards_id = _.map($scope.cards_selected, function(card) {
                  return card.id;
              });
          }
          var params = {"cards_id": cards_id,
                        "distributor_name": $scope.distributor,
                        "name": $scope.deposit_name,
                        "initial_nb": $scope.initial_nb,
                        "minimal_nb": $scope.minimal_nb,
                        "auto_command": $scope.auto_command,
                       };
          // needed for Django to process the params to its request.POST dict.
          $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8';

          // We need not to pass the parameters encoded as json to Django.
          // Encode them like url parameters.
          // xxx: put in service
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

          return $http.post("/api/deposits", params)
              .then(function(response){
                  return response.data;
              });
      };

      $scope.add_selected_card = function(card_repr){
          $scope.cards_selected.push(card_repr);
          $scope.copy_selected = "";
      };

      $scope.remove_from_selection = function(index_to_rm){
          $scope.cards_selected.splice(index_to_rm, 1);
      };

  }]);
