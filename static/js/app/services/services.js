/* Services */

// Demonstrate how to register services
// In this case it is a simple value service.
angular.module('abelujo.services', []).
  value('version', '0.1');

var utils = angular.module('abelujo.services', []);
utils.factory('utils', function() {
  return {
      // We need not to pass the parameters encoded as json to Django,
      // because it re-encodes everything in json and the result is horrible.
      // Encode them like url parameters.
      transformRequestAsFormPost: function(obj){
          // obj: a list of simple types. Not a list of dictionnaries.
          var str = [];
          for(var p in obj)
              str.push(encodeURIComponent(p) + "=" + encodeURIComponent(obj[p]));
          return str.join("&");
      }
  };

});
