/* Services */

// Demonstrate how to register services
// In this case it is a simple value service.
angular.module('abelujo.services', []).
  value('version', '0.1');

var utils = angular.module('abelujo.services', []);
utils.factory('utils', function() {
  return {
      // We need not to pass the parameters encoded as json to Django.
      // Encode them like url parameters.
      transformRequestAsFormPost: function(obj){
          //factory function body that constructs shinyNewServiceInstance
          var str = [];
          for(var p in obj)
              str.push(encodeURIComponent(p) + "=" + encodeURIComponent(obj[p]));
          return str.join("&");
      }
  }

});
