// Include gulp
var gulp = require('gulp');

// Include Our Plugins
var livescript = require("gulp-ls");
var args   = require('yargs').argv;
var gutil = require('gulp-util');
var less = require('gulp-less');
var minifyCss = require('gulp-minify-css');
// var karma = require('gulp-karma');
var concat = require('gulp-concat');
var uglify = require('gulp-uglify');
var jshint = require('gulp-jshint');
var bg = require("gulp-bg");

var vendorJsFiles = [
  // 'static/bower_components/jquery/jquery.min.js', // load separately and first (needed by autocomplete_light and django_bootstrap).
    // jquery: for bootstrap and datatables.
    // to load before bootstrap.
    // jquery must come before angular and datatables.
    'static/bower_components/jquery/dist/jquery.min.js',
    'static/bower_components/datatables/media/js/jquery.dataTables.min.js',
  'static/bower_components/angularjs/angular.min.js',
  'static/bower_components/angular-bootstrap/ui-bootstrap.min.js',
  'static/bower_components/angular-bootstrap/ui-bootstrap-tpls.min.js',
  'static/bower_components/angular-resource/angular-resource.min.js',
  'static/bower_components/angular-route/angular-route.min.js',
  'static/bower_components/angular-sanitize/angular-sanitize.min.js',
  'static/bower_components/angular-cookies/angular-cookies.min.js',
  'static/bower_components/angular-animate/angular-animate.min.js',
  'static/bower_components/angular-i18n/angular-locale_fr-fr.js',
  'static/bower_components/angular-i18n/angular-locale_es-es.js',
  'static/bower_components/angular-i18n/angular-locale_de-de.js',
  'static/bower_components/angular-i18n/angular-locale_en-gb.js',
  'static/bower_components/angular-dynamic-locale/tmhDynamicLocale.min.js',
  'static/bower_components/angular-ui-router/release/angular-ui-router.min.js',
  'static/bower_components/angular-ui-select/dist/select.js',
  'static/bower_components/underscore/underscore-min.js',
  'static/bower_components/underscore/underscore-min.js',
  'static/bower_components/prelude-ls/browser/prelude-browser-min.js',
  // 'static/bower_components/bootstrap/**/*.js',
    'static/bower_components/datejs/build/production/date.min.js',
    'static/bower_components/c3/c3.min.js',
    'static/bower_components/d3/d3.min.js',
    'static/bower_components/angular-smart-table/dist/smart-table.min.js',
    'static/bower_components/angular-datatables/dist/angular-datatables.min.js',
    'static/bower_components/angular-loading-bar/build/loading-bar.min.js',
    'static/bower_components/angular-hotkeys/build/hotkeys.min.js',
    'static/bower_components/bootstrap-tour/build/js/bootstrap-tour.min.js',
];

var appFiles = [
    'static/js/app/**/*.js',
    'static/js/build/livescript/**/*.js'
];

var vendorCSSFiles = [
    'static/bower_components/angular-ui-select/dist/select.min.css',
    'static/bower_components/c3/c3.min.css',
    'static/bower_components/bootstrap-tour/build/css/bootstrap-tour.min.css',
    // warning: set headers in base.jade !
];

// Include files to test with karma
var testFiles = [
  'static/bower_components/angular/angular.js',
  'static/bower_components/angular-route/angular-route.js',
  'static/bower_components/angular-mocks/angular-mocks.js',
  'static/js/app/**/*.js',
  'static/js/app/controllers/**/*.js',
  'static/js/test/unit/**/*.js'
];

// Minify vendor css files
gulp.task('css', function() {
    return gulp.src(vendorCSSFiles)
        .pipe(minifyCss())
        .pipe(gulp.dest('static/css/'));
});

// Compile the Less files
gulp.task('less', function() {
    return gulp.src('static/css/*.less')
        .pipe(less())
        .pipe(gulp.dest('static/css'));
});

// Compile livescript
gulp.task('compile:livescript', function () {
    return gulp.src('static/js/app/**/*.ls')
        .pipe(livescript({bare: true}))
        .pipe(gulp.dest('static/js/build/livescript/'));
});

// gulp.task('concat:livescript', function () {
//     return gulp.src("static/js/build/livescript/**/*js")
//         .pipe(concat("abelujo.js"))
//         .pipe(gulp.dest('static/js/build'));
// })

// Concatenate js vendor files
gulp.task('concatjs:vendor', function () {
  return gulp.src(vendorJsFiles)
    .pipe(concat('vendor.js'))
    // .pipe(uglify())
    .pipe(gulp.dest('static/js/build'));
});


// Concatenate js app files
gulp.task('concatjs:app', ['compile:livescript'], function () {
  console.log("warning: we deactived jshint.");
  return gulp.src(appFiles)
    // .pipe(jshint('.jshintrc'))  // many errors are ls's boilerplate.
    // .pipe(jshint.reporter('default'))
    .pipe(concat('abelujo.js'))
    // .pipe(uglify())
    .pipe(gulp.dest('static/js/build'));
});

// Unit testing with karma
gulp.task('karma', function() {
  // Be sure to return the stream
  return gulp.src(testFiles)
    .pipe(karma({
      configFile: 'static/js/test/karma.conf.js',
      action: 'run'
    }))
    .on('error', function(err) {
      // Make sure failed tests cause gulp to exit non-zero
      throw err;
    });
});

// Unit testing with karma and watching for changes
gulp.task('karma:watch', function () {
  return gulp.src(testFiles)
    .pipe(karma({
      configFile: 'karma.conf.js',
      action: 'watch'
    }))
    .on('error', function(e) {throw e});
});

// Concatenations
gulp.task('concat', ['concatjs:app', 'concatjs:vendor']);

// Tests
gulp.task('test', ['karma']);

// Serve django project
var port = args.port || '8000';
// gulp.task("server", bg("bin/django-manage", "runserver", "0.0.0.0:"+port));
gulp.task("server", bg("./manage.py", "runserver", "0.0.0.0:"+port));
gulp.task("run", bg("bin/django-manage", "runserver", "0.0.0.0:"+port));

// Watch Files For Changes
gulp.task('watch', function() {
    gulp.watch('static/css/*.less', ['less']);
    gulp.watch(testFiles, ['test']);
    gulp.watch(appFiles, ['concatjs:app']);
});

gulp.task('livescript', ['compile:livescript']);

// Default Task
// gulp.task('default', ['less', 'test', 'concat']);
//XXX warning of mixing ls and js for same file.
gulp.task('default', ['css', 'less', 'concat',]);
