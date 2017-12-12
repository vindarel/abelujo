<template>
  <div>
    <td v-if="show_images" >
      <img :src="card.img" :height="card_height"/>
    </td>
    <td>
      <a :href="url"> {{ card.title }} </a>
      <div v-if="show_images" > {{ card.authors_repr }} </div>
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
      show_images: {
        type: Boolean,
        default: false,
      },
      external_url: {
        type: Boolean,
        default: false,
      },
    },

    data: function () {
      return {
      }
    },

    computed: {
      url() {
        if (this.external_url) {
          return this.card.details_url;
        }
        return this.card.get_absolute_url;
      },
    },

    methods: {
    },

    mounted: function () {
    },
  }
</script>
