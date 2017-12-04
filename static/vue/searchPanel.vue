<template>
  <div class="row">
    <form action="" method="get" @submit="search">
      <input id="GET-name" type="text" name="name" v-model="query">
      <input type="submit" value="Search">
    </form>

    <table>
      <tbody>
        <tr v-for="(it, index) in cards" :key="it.id">
          <card-item
              :card="it"
              card_height="100px"
              @clicked="addCard">
          </card-item>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>

  import CardItem from "./cardItem";

  export default {
    name: 'SearchPanel',
    props: {
      url: String, // search api url.
    },

    components: {
      CardItem,
    },

    data: function () {
      return {
        cards: [],  // list of search results. Certainly with a title, authors etc.
        searchterm: "",
        datasource: 'librairiedeparis',
      }
    },

    methods: {
      addCard: function (card) {
        console.log("--- add ", card);
        this.$emit("onAddCard", card);
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
