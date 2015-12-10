// Application's starting point.

'use strict';

// Declare app level module which depends on filters, and services
angular.module('abelujo', [
    'ngRoute',
    'ngCookies',
    'ngResource',
    'ngSanitize',
    'ui.router',
    'ui.select',
    'ui.bootstrap',

    // application level:
    'abelujo.filters',
    'abelujo.services',
    'abelujo.directives',
    'abelujo.controllers'
]);

// Angularjs and Django both use double brackets for variable interpolation.
// We can change angular's symbols, but it breaks 3rd party packages integration that ship with their own directives, like a ui-bootstrap calendar. Too bad.
// Check https://stackoverflow.com/questions/8302928/angularjs-with-django-conflicting-template-tags for change ?
// angular.module('abelujo').config(function($interpolateProvider) {
  // $interpolateProvider.startSymbol('<<');
  // $interpolateProvider.endSymbol('>>');
// });
