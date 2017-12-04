<template>
  <div>
    <td class="col-md-4">
      <img :src="card.img" :height="card_height"/>
    </td>
    <td class="col-md-8">
      <a :href="card.search_url"> {{ card.title }} </a>
      <div> {{ card.authors_repr }} </div>
      <button @click="clicked"> Add </button>
    </td>
  </div>
</template>

<script>

  /* Print a card inside a table.*/

  export default {
    name: 'CardItem',
    props: {
      card: {
        required: true,
      },
      card_height: {
        type: String,
        required: false,
      },
    },

    data: function () {
      return {
      }
    },

    methods: {
      clicked: function (e) {
        console.log("--- card item clicked ", this.card);
        this.$emit("clicked", this.card);
      },
    },

    mounted: function () {
    },
  }
</script>
