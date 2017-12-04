<template>
  <div>
    <td v-if="show_images" >
      <img :src="card.img" :height="card_height"/>
    </td>
    <td>
      <a :href="card.search_url"> {{ card.title }} </a>
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
    },

    data: function () {
      return {
      }
    },

    methods: {
    },

    mounted: function () {
    },
  }
</script>
