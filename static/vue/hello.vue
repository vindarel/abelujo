<template>
</template>

<script>

 console.log("------ Vue + brunch = bright future.");

 export default {
   name: 'Hello',
   props: {
     title: String,
   },

   mounted: function () {
     console.log("Vue component is mounted ! Let's go ! Proof: ", this.title);
   }

 }
</script>
