<template>
  <nav aria-label="pagination" style="float: right;">
    <ul class="pagination">
      <li>
        <a href="#" aria-label="Previous" @click="previous_page">
          <span aria-hidden="true">&laquo;</span> </a>
      </li>
      <li> <a href="#"> {{ text() }} </a></li>
      <li>
        <a href="#" aria-label="Next" @click="next_page">
          <span aria-hidden="true">&raquo;</span> </a>
      </li>
    </ul>
  </nav>

</template>

<script>
  // A component just for that O_o ?
  export default {
    name: 'PaginationBullets',
    props: {
      current_page: undefined,
      page_count: undefined,
      data_length: {
        required: false,
      },
    },

    methods: {
      previous_page: function () {
        this.$emit("previous_page");
      },

      next_page: function () {
        this.$emit("next_page");
      },

      text: function () {
        // Better with element-ui.
        let txt = this.current_page + " / " + this.page_count;
        if (typeof this.data_length != undefined) {
          txt += " (" + this.data_length + ")";
        }
        return txt;
      },
    }
  }
</script>
