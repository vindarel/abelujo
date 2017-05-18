// Include gulp
var gulp = require('gulp');

// Include Our Plugins
var livescript = require("gulp-ls");
var args   = require('yargs').argv;
var gutil = require('gulp-util');
var less = require('gulp-less');
var minifyCss = require('gulp-clean-css');
var concat = require('gulp-concat');
var uglify = require('gulp-uglify');
var jshint = require('gulp-jshint');
var bg = require("gulp-bg");

var vendorJsFiles = [
  // 'static/bower_components/jquery/jquery.min.js', // load separately and first (needed by django_bootstrap).
    // jquery: for bootstrap and datatables.
    // to load before bootstrap.
    // jquery must come before angular and datatables.
    'node_modules/jquery/jquery.min.js',
    'node_modules/datatables/media/js/jquery.dataTables.min.js',
  'node_modules/angular/angular.min.js',
  'node_modules/bootstrap/dist/js/bootstrap.min.js',
  'node_modules/bootstrap-tour/build/js/bootstrap-tour.min.js',
  'node_modules/angular-ui-bootstrap/ui-bootstrap.min.js',
  'node_modules/angular-ui-bootstrap/ui-bootstrap-tpls.min.js',
  'node_modules/angular-resource/angular-resource.min.js',
  'node_modules/angular-route/angular-route.min.js',
  'node_modules/angular-sanitize/angular-sanitize.min.js',
  'node_modules/angular-cookies/angular-cookies.min.js',
  'node_modules/angular-animate/angular-animate.min.js',
  'node_modules/angular-dynamic-locale/tmhDynamicLocale.min.js',
  'node_modules/angular-ui-router/release/angular-ui-router.min.js',
  'node_modules/angular-ui-select/select.js',
  'node_modules/underscore/underscore-min.js',
  'node_modules/underscore/underscore-min.js',
  // 'node_modules/prelude-ls/**/*.js', // see issue #62. To be removed from bower eventually.
  'static/bower_components/prelude-ls/browser/prelude-browser-min.js', // xxx bower here
    'node_modules/bootstrap/js/*.js', // needed despite of settings.py

    'node_modules/datejs/build/production/date.min.js',  // XXX
    'node_modules/c3/c3.min.js',
    'node_modules/d3/d3.min.js',
    'node_modules/angular-smart-table/dist/smart-table.min.js',
    'node_modules/angular-datatables/dist/angular-datatables.min.js',
    'node_modules/angular-loading-bar/build/loading-bar.min.js',
    'node_modules/angular-hotkeys/build/hotkeys.min.js',
];

var appFiles = [
    'static/js/app/**/*.js',
    'static/js/build/livescript/**/*.js'
];

var vendorCSSFiles = [
    // warning: also set headers in base.jade !
    'node_modules/angular-ui-select/select.min.css',
    'node_modules/c3/c3.min.css',
    'node_modules/bootstrap/dist/css/bootstrap.min.css',
    'node_modules/bootstrap/dist/css/bootstrap-theme.min.css',
    'node_modules/bootstrap-tour/build/css/bootstrap-tour.min.css',
    'node_modules/datatables/media/css/jquery.dataTables.min.css',
    'node_modules/angular-loading-bar/build/loading-bar.min.css',
    'node_modules/angular-hotkeys/build/hotkeys.min.css',
];

// Include files to test with karma
var testFiles = [
  'node_modules/angular/angular.js',
  'node_modules/angular-route/angular-route.js',
  'node_modules/angular-mocks/angular-mocks.js',
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
