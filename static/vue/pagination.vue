<template>
  <nav aria-label="pagination" style="float: right;">
    <ul class="pagination">
      <li>
        <a href="#" aria-label="First page" @click="first_page">
          <span aria-hidden="true"> &laquo; </span> </a>
        <a href="#" aria-label="Previous page" @click="previous_page">
          <span aria-hidden="true"> < </span> </a>
      </li>
      <li> <a href="#"> {{ text() }} </a></li>
      <li>
        <a href="#" aria-label="Next" @click="next_page">
          <span aria-hidden="true"> > </span> </a>
        <a href="#" aria-label="Last" @click="last_page">
          <span aria-hidden="true"> &raquo; </span> </a>
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
      first_page: function () {
        this.$emit("first_page");
      },

      previous_page: function () {
        this.$emit("previous_page");
      },

      next_page: function () {
        this.$emit("next_page");
      },

      last_page: function () {
        this.$emit("last_page");
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
