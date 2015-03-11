var gulp = require('gulp');
var concat = require('gulp-concat');
var uglify = require('gulp-uglify');

module.exports = function() {
    var jsFiles = ['js/compatibility.js', 'js/util.js', 'js/uri.js',
                   'js/xhr.js', 'js/ui.js', 'js/file_browser.js',
                   'js/common.js', 'js/record/admin.js', 'js/record/model.js',
                   'js/record/keymap.js', 'js/record/view.js', 'js/record/tabs.js',
                   'js/record/app.js'];
    gulp.src(jsFiles)
        .pipe(concat('bundle.js'))
        .pipe(uglify())
        .pipe(gulp.dest('public/record'));
};