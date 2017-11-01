"use strict";

import Vue from "vue";
/* import Vue from "vue/dist/vue.js";*/
// warning: https://stackoverflow.com/questions/39488660/vue-js-2-0-not-rendering-anything

import Hello from "./hello.vue"

console.log("----- init vue !")

/* eslint-disable no-new */
new Vue({
  el: "#abelujo",
  components: {
    Hello,
  },
  data: {
  },
});
