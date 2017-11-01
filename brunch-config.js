module.exports = {
  paths: {
    watched: [
      'static/vue',
      'templates/search',
    ],
  },
  files: {
    javascripts: {joinTo: 'app.js'},
    stylesheets: {joinTo: 'app.css'}
  },
  npm: {
    aliases: {
      vue: "vue/dist/vue.js"
    }
  }
}
