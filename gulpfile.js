// Include gulp
var gulp = require('gulp');

// Include Our Plugins
var rapyd = require("gulp-rapyd");  // install with npm install path/to/project or http/gitlab/...
var args   = require('yargs').argv;
var gutil = require('gulp-util');
var less = require('gulp-less');
// var karma = require('gulp-karma');
var concat = require('gulp-concat');
var uglify = require('gulp-uglify');
var jshint = require('gulp-jshint');
var bg = require("gulp-bg");

var vendorJsFiles = [
  // 'static/bower_components/jquery/jquery.min.js', // load separately and first (needed by autocomplete_light and django_bootstrap).
  'static/bower_components/angularjs/angular.min.js',
  'static/bower_components/angular-resource/angular-resource.min.js',
  'static/bower_components/angular-route/angular-route.min.js',
  'static/bower_components/angular-sanitize/angular-sanitize.min.js',
  'static/bower_components/angular-cookies/angular-cookies.min.js',
  'static/bower_components/angular-ui-router/release/angular-ui-router.min.js',
  'static/bower_components/bootstrap/**/*.js',
];

var appFiles = [
  'static/js/app/**/*.js'
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

// Compile the Less files
gulp.task('less', function() {
    return gulp.src('static/css/*.less')
        .pipe(less())
        .pipe(gulp.dest('static/css'));
});

gulp.task('compile:rapyd', function() {
  gulp.src('static/js/app/**/*.pyj')
    .pipe(rapyd({bare: true}).on('error', gutil.log))
    .pipe(gulp.dest('static/js/build/rapyd/'))
});

// Concatenate pyj compiled files
gulp.task('concatjs:rapyd', function () {
  return gulp.src("static/js/build/rapyd/**/*js")
    .pipe(concat('abelujo.js'))
    // .pipe(uglify())
    .pipe(gulp.dest('static/js/build'));
});

// Concatenate js vendor files
gulp.task('concatjs:vendor', function () {
  return gulp.src(vendorJsFiles)
    .pipe(concat('vendor.js'))
    // .pipe(uglify())
    .pipe(gulp.dest('static/js/build'));
});

// Concatenate js app files
gulp.task('concatjs:app', function () {
  return gulp.src(appFiles)
    // .pipe(jshint('.jshintrc'))
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
gulp.task("server", bg("bin/django-manage", "runserver", "0.0.0.0:"+port));
gulp.task("run", bg("bin/django-manage", "runserver", "0.0.0.0:"+port));

// Watch Files For Changes
gulp.task('watch', function() {
    gulp.watch('static/css/*.less', ['less']);
    gulp.watch(testFiles, ['test']);
    gulp.watch(appFiles, ['concatjs:app']);
});

// Default Task
// gulp.task('default', ['less', 'test', 'concat']);
gulp.task('default', ['less', 'concat']);

// compile only RapydScript files
gulp.task('rapyd', ['less', 'compile:rapyd', 'concatjs:rapyd']);
