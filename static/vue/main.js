"use strict";
/* eslint-disable no-new */

import Vue from "vue";
const VueResource = require('vue-resource');
const VueProgressBar = require('vue-progressbar');
const VueResourceProgressBarInterceptor = require('vue-resource-progressbar-interceptor');

const options = {
  color: '#bffaf3',
  failedColor: '#874b4b',
  thickness: '5px',
  transition: {
    speed: '0.2s',
    opacity: '0.6s',
    termination: 300
  },
  autoRevert: true,
  location: 'left',
  inverse: false,
  latencyThreshold: 100,
}

Vue.use(VueResource);
Vue.use(VueProgressBar, options);
Vue.use(VueResourceProgressBarInterceptor); // unsure it's working

import Baskets from "./baskets.vue"

if (document.getElementById("abelujo")) {
  new Vue({
    el: "#abelujo",
    components: {
      Hello,
    },
    data: {
    },
  });
}

if (document.getElementById("baskets")) {
  new Vue({
    el: "#baskets",
    components: {
      Baskets,
    },
    data: {},
  });
}
