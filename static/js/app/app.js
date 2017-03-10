// Application's starting point.

'use strict';

// Declare app level module which depends on filters, and services
angular.module('abelujo', [
    'ngRoute',
    'ngCookies',
    'ngResource',
    'ngSanitize',
    'ngAnimate',
    'ngLocale',
    'tmh.dynamicLocale',
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

// Tell the dynamic locale provider where to find translation files.
// (a bit later: for bootstrap datepicker I guess).
angular.module('abelujo').config(function (tmhDynamicLocaleProvider) {
    tmhDynamicLocaleProvider.localeLocationPattern('/static/bower_components/angular-i18n/angular-locale_{{locale}}.js');
    tmhDynamicLocaleProvider.defaultLocale('fr'); // default locale
    tmhDynamicLocaleProvider.useCookieStorage('NG_TRANSLATE_LANG_KEY');
});
