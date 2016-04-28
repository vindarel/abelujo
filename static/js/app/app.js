// Application's starting point.

'use strict';

// Declare app level module which depends on filters, and services
angular.module('abelujo', [
    'ngRoute',
    'ngCookies',
    'ngResource',
    'ngSanitize',
    'ngAnimate',
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
