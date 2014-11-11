// Application's starting point.

'use strict';

// Declare app level module which depends on filters, and services
angular.module('abelujo', [
    'ngRoute',
    'ngCookies',
    'ngResource',
    'ngSanitize',
    'ui.router',
    'abelujo.filters',
    'abelujo.services',
    'abelujo.directives',
    'abelujo.controllers'
]);
