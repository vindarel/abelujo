<template>
  <div class="row">
    <div class="col-md-4">
      <search-panel
          :url="api_cards"
          @onAddCard="onAddCard">
      </search-panel>
    </div>

    <div class="col-md-8">
      <div v-for="it in baskets" :key="it.id">
        <div> {{ it.name }} </div>
      </div>
    </div>

    <table class="table-condensed">
      <tbody>
        <tr v-for="it in cards">
          <card-item :card="it"/>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
  import SearchPanel from "./searchPanel.vue"
  import CardItem from "./cardItem";

  // todo: a simple list view of all the cards with some succinct info, like Deposits.
  // It's still possible to easily switch of baskets from within one.

  export default {
    name: 'Baskets',
    props: {
      baskets_url: {
        String,
        required: true,
      },
    },
    components: {
      SearchPanel,
      CardItem,
    },

    data: function () {
      return {
        baskets: [],
        /* api_cards: "/api/cards",*/
        api_cards: "/api/datasource/search",
        cards: [], // list of dicts
      }
    },

    methods: {
      onAddCard: function (card) {
        console.log("-- received ", card);
        this.cards.push(card);
      },

    },

    mounted: function () {
      console.log("--- Baskets component is mounted");
      $.ajax({
        url: this.baskets_url,
        success: res => {
          console.log("--- baskets", res);
          this.baskets = res.data;
        }
      });
    },
  }
</script>
