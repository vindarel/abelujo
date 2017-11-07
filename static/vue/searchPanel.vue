<template>
  <div class="row">
    <form action="" method="get" @submit="search">
      <input id="GET-name" type="text" name="name" v-model="query">
      <input type="submit" value="Search">
    </form>

    <div v-for="(it, index) in cards" :key="it.id">
      <span> Title: {{ it.title }} </span>
      <button @click="addCard(index)"> Add => </button>
    </div>
  </div>
</template>

<script>

  export default {
    name: 'SearchPanel',
    props: {
      url: String, // search api url.
    },

    data: function () {
      return {
        cards: [],  // list of search results. Certainly with a title, authors etc.
        searchterm: "",
        datasource: 'librairiedeparis',
      }
    },

    methods: {
      addCard: function (index) {
        console.log("--- add ", this.cards[index]);
        this.$emit("onAddCard", this.cards[index]);
      },

      search: function (e) {
        e.preventDefault();
        let url;
        url = this.url + "?" + this.query;
        console.log("-- searching: ", url);
        $.ajax({
          data: {
            query: this.query,
            datasource: this.datasource,
          },
          url: url,
          success: res => {
            console.log("--- cards", res);
            // todo: error handling, show alerts, etc.
            this.cards = res.data;
          }
        });
      },
    },

    mounted: function () {
    },
  }
</script>
