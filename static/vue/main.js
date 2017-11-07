"use strict";
/* eslint-disable no-new */

import Vue from "vue";
Vue.use(require("vue-resource"));

import Hello from "./hello.vue"
import CardAdd from "./cardAdd.vue"
import Baskets from "./baskets.vue"

if (document.getElementById("abelujo")) {
  new Vue({
    el: "#abelujo",
    components: {
      Hello,
      CardAdd,
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
