<template>
  <div class="row">
    <div class="col-md-4">
      <search-panel
          :url="api_cards"
          @onAddCard="onAddCard">
      </search-panel>
    </div>

    <div class="col-md-8">
      <div class="btn-group">
        <div class="dropdown">
          <button id="actions" class="btn btn-info dropdown-toggle" type="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"> List
            <span class="caret"></span>
          </button>
          <ul class="dropdown-menu">
            <li>
              <a href="#" title="" @click="mark_command()"> Command all
                <i class="glyphicon glyphicon-right"> </i>
              </a>
            </li>
            <li>
              <a href="#" title="" @click="receive_command()"> Receive a parcel…
                <i class="glyphicon glyphicon-right"> </i>
              </a>
            </li>
            <li class="divider" role="separator"></li>
            <li>
              <a href="#" title="" @click="not_implemented()"> Transform as deposit…
                <i class="glyphicon glyphicon-right"> </i>
              </a>
            </li>
          </ul>
        </div>
      </div>
      <div class="btn-group">
        <div class="dropdown">
          <button id="actions" class="btn btn-success dropdown-toggle" type="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"> Export
            <span class="caret"></span>
          </button>
          <ul class="dropdown-menu">
            <li>
              <a :href="export_url('?format=txt&report=listing')" title=""> txt
                <i class="glyphicon glyphicon-right"> </i>
              </a>
            </li>
            <li>
              <a :href="export_url('?format=csv&report=listing')" title=""> csv (Excel, LibreOffice)
                <i class="glyphicon glyphicon-right"> </i>
              </a>
            </li>
            <li>
              <a :href="export_url('?format=pdf&report=listing')" title=""> pdf
                <i class="glyphicon glyphicon-right"> </i>
              </a>
            </li>
            <li>
              <a :href="export_url('?format=pdf&report=listing&barcodes=true')" title=""> pdf, with barcodes
                <i class="glyphicon glyphicon-right"> </i>
              </a>
            </li>
            <li>
              <a :href="export_url('?format=pdf&report=listing&barcodes=false&covers=true')"" title=""> pdf, with covers
                <i class="glyphicon glyphicon-right"> </i>
              </a>
            </li>
          </ul>
        </div>
      </div>

      <div class="btn-group">
        <button class="btn btn-default" @click="toggle_images" >
          <i class="glyphicon glyphicon-th-list"/>
        </button>
        <button class="btn btn-default">
          <i class="glyphicon glyphicon-pencil"/>
        </button>
        <a href="http://abelujo.cc/docs/lists/" target="_blank"
            class="btn btn-default">
          <i class="glyphicon glyphicon-info-sign"/>
        </a>
        <button class="btn btn-default">
          <i class="glyphicon glyphicon-question-sign"/>
        </button>
      </div>

      <div class="row">
        <h3 class="col-md-8" > {{ basket_name }} </h3>
        <pagination-bullets
            class="col-md-4"
            :current_page="page"
            :page_count="page_count"
            :data_length="data_length"
            @first_page="first_page"
            @previous_page="previous_page"
            @next_page="next_page"
            @last_page="last_page" >
        </pagination-bullets>
      </div>

      <table class="table table-condensed table-striped">
        <thead>
          <th> Title </th>
          <th> Publisher </th>
          <th> In stock </th>
          <th> </th>
          <td> </td>
          <th></th>
          <th></th>
        </thead>
        <tbody>
          <tr v-for="(it, index) in cards">
            <card-item :card="it"
                :show_images="show_images"
                card_height="150px"/>
            <td> {{ it.pubs_repr }} </td>
            <td> {{ it.quantity }} </td>
            <td> {{ it.price }} € </td> <!--TODO: currency -->
            <td>
              <input class="my-number-input"
                  type="number"
                  min="0" max="9999"
                  v-model="it.basket_qty"
                  @click="basket_qty_updated(it)">
            </td>
            <td>
              <i class="glyphicon glyphicon-remove mouse-pointer"
                  @click="remove_card(it, index)"></i>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- component but still duplicated call to it ! -->
      <pagination-bullets
          :current_page="page"
          :page_count="page_count"
          :data_length="data_length"
          @first_page="first_page"
          @previous_page="previous_page"
          @next_page="next_page"
          @last_page="last_page" >
      </pagination-bullets>

    </div>


  </div>
</template>

<script>
  var _ = require('lodash');

  import SearchPanel from "./searchPanel.vue"
  import CardItem from "./cardItem";
  import PaginationBullets from "./pagination";

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
      PaginationBullets,
    },

    data: function () {
      return {
        baskets: [],
        /* api_cards: "/api/cards",*/
        api_cards: "/api/datasource/search",
        cards: [], // list of dicts
        show_images: false,
        page: 1,
        page_count: undefined,
        data_length: 0,
        basket_name: "",
      }
    },

    methods: {
      onAddCard: function (card) {
        this.save_card_to_basket(card);
      },

      save_card_to_basket: function (card) {
        const url = "/api/v2/baskets/{}/add".replace("{}", this.id);
        $.ajax({
          url: url,
          type: 'POST',
          contentType: "application/json; charset=utf-8",
          data: JSON.stringify(card),
          success: res => {
            card.id = res.data.card.id;
            if (res.data.created) {
              this.cards.splice(0, 0, card);
            } else {
              let index = _.findIndex(this.cards, ['id', res.data.card.id]);
              this.cards[index].basket_qty = res.data.basket_qty;
            }
            // xxx: notification
            console.log("added card succesfully. id: ", res.data.card.id, "created ? ", res.data.created);
          }
        });
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
            page: this.page,
          },
          success: res => {
            // We get the list of copies, no other basket info.
            this.cards = res.data;
            this.page_count = res.page_count;
            this.data_length = res.data_length;
            this.basket_name = res.basket_name;
          }
        });
      },

      remove_card: function (card, index) {
        console.log("got ", card);
        let sure = confirm("Are you sure to remove the card from the selection ?");
        if (sure) {
          let card_id = card.id;
          $.ajax({
            url: "/api/baskets/{ID}/remove/{card_id}/".replace("{ID}", this.id).replace("{card_id}", card_id),
            type: 'POST',
            success: res => {
              console.log("card deleted: ", card.id, card.title);
              this.cards.splice(index, 1);
            }
          });
        }
      },

      first_page: function () {
        this.page = 1;
        this.get_cards();
      },

      next_page: function () {
        if (this.page < this.page_count) {
          this.page += 1;
          this.get_cards();
        }
      },

      previous_page: function () {
        if (this.page > 1) {
          this.page -= 1;
          if (this.page > 0) {
            this.get_cards();
          }
        }
      },

      last_page: function () {
        this.page = this.page_count;
        this.get_cards();
      },

      basket_qty_updated: function (card) {
        "API call. Update the card's quantity."
        const url = "/api/baskets/{}/update".replace("{}", this.id);
        $.ajax({
          url: url,
          type: 'POST',
          contentType: "application/json; charset=utf-8",
          data: JSON.stringify({
            card_id: card.id,
            quantity: card.basket_qty,
          }),
          success: res => {
            console.log("updated card quantity to ", card.basket_qty, "( ", card.title, " )");
            // xxx: notification and message from server.
          }
        });
      },

      export_url: function (tail) {
        // default argument to "" ?
        if (typeof tail == 'undefined') {
          tail = "";
        }
        return "/baskets/" + this.id + "/export" + tail;
      },

      mark_command: function () {
        if (! this.cards.length) {
          // xxx notification
          alert("This basket has no copies to command.");
        }

        const url = "/api/baskets/1/add/";  // default to_command basket.
        $.ajax({
          url: url,
          type: 'POST',
          contentType: 'application/json; charset=utf-8',
          data: JSON.stringify({
            'cards': this.cards,
          }),
          success: res => {
            console.log("success ", res); // xxx notification
          }
        });
      },

      receive_command: function () {
        // Get or create an inventory, redirect to that inventory page.
        const url = "/api/baskets/{id}/inventories/".replace('{id}', this.id);
        let res = window.location.pathname.match("/([a-z][a-z])/");
        let lang;
        if (res) {
          lang = res[1];
        }
        console.log("lang: ", lang, res);
        $.ajax({
          url: url,
          success: res => {
            console.log("success ", res);
            if (res.status && lang) {
              window.location.href = "/{lang}/inventories/{id}/".replace('{lang}', lang).replace('{id}', res.data.inv_id);
            }
          }
        })
      },

      not_implemented: function () {
        alert("We have to finish this !");
      },

    },

    mounted: function () {
      // Read from localStorage.
      if (typeof (Storage) !== 'undefined') {
        this.show_images = JSON.parse(localStorage.getItem('show_images'));
      }

      this.get_cards();
    },
  }
</script>
