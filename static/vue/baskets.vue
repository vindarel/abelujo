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

      <div class="btn-group">
        <button class="btn btn-default" @click="toggle_images" >
          <i class="glyphicon glyphicon-th-list"/>
        </button>
        <button class="btn btn-default">
          <i class="glyphicon glyphicon-pencil"/>
        </button>
        <button class="btn btn-default">
          <i class="glyphicon glyphicon-info-sign"/>
        </button>
        <button class="btn btn-default">
          <i class="glyphicon glyphicon-question-sign"/>
        </button>
      </div>

      <table class="table table-condensed table-striped">
        <thead>
          <th> Title </th>
          <th> Publisher </th>
          <th> In stock </th>
          <th> Price </th>
          <th></th>
        </thead>
        <tbody>
          <tr v-for="it in cards">
            <card-item :card="it"
                :show_images="show_images"
                card_height="150px"/>
            <td> {{ it.pubs_repr }} </td>
            <td> {{ it.quantity }} </td>
            <td> {{ it.price }} </td>
          </tr>
        </tbody>
      </table>
    </div>


  </div>
</template>

<script>
  import SearchPanel from "./searchPanel.vue"
  import CardItem from "./cardItem";

  export default {
    name: 'Baskets',
    props: {
      id: undefined,  // current basket id.
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
        show_images: false,
        page: 1,
      }
    },

    methods: {
      onAddCard: function (card) {
        console.log("-- received ", card);
        this.cards.push(card);
      },

      toggle_images: function () {
        this.show_images = ! this.show_images;
        if (typeof (Storage) !== "undefined") {
          localStorage.setItem("show_images", JSON.stringify(this.show_images));
        }
      },

      get_cards: function () {
        const url = "/api/baskets/" + this.id;
        $.ajax({
          url: url,
          data: {
            /* page: this.page,*/
          },
          success: res => {
            console.log("--- current basket ", res);
            // We get the list of copies, no other basket info.
            this.cards = res;
            console.log("Got cards: ", this.cards);
          }
        });
      },

      next_page: function () {
        this.get_cards();
        this.page += 1;
      },

    },

    mounted: function () {
      console.log("--- Baskets component is mounted");

      // Read from localStorage.
      if (typeof (Storage) !== 'undefined') {
        this.show_images = JSON.parse(localStorage.getItem('show_images'));
      }

      this.get_cards();

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
