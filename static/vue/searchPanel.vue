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
              show_images="true"
              card_height="100px">
          </card-item>
          <td class="col-md-1" >
            <button @click="addCard(index)" class="btn btn-small">
              <i class="glyphicon glyphicon-plus"/>
            </button>
          </td></tr>
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
