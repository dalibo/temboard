module.exports = function(grunt) {
  grunt.initConfig({
    sass: {
      options: {
        sourceMap: true,
        includePaths: ['node_modules/bootstrap-sass/assets/stylesheets']
      },
      // this is the "dev" Sass config used with "grunt watch" command
      dev: {
        options: {
          outputStyle: 'expanded'
        },
        files: {
          'temboardui/static/css/temboard.css': 'temboardui/static/sass/temboard.scss'
        }
      },
      dist: {
        options: {
          outputStyle: 'compressed'
        },
        files: {
          'temboardui/static/css/temboard.css': 'temboardui/static/sass/temboard.scss'
        }
      }
    },
    copy: {
      bootstrapfonts: {
        expand: true,
        cwd: 'node_modules/bootstrap-sass/assets/fonts/bootstrap/',
        src: ['*'],
        dest: 'temboardui/static/fonts/'
      },
      bootstrapjs: {
        expand: true,
        cwd: 'node_modules/bootstrap-sass/assets/javascripts/',
        src: ['bootstrap.min.js'],
        dest: 'temboardui/static/js/'
      }
    },
    // configure the "grunt watch" task
    watch: {
      sass: {
        files: 'temboardui/static/sass/*.scss',
        tasks: ['sass:dev']
      }
    }
  });
  grunt.loadNpmTasks('grunt-sass');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-copy');

  grunt.registerTask('bootstrap', [
    'copy:bootstrapfonts',
    'copy:bootstrapjs',
    'sass:dist'
  ]);
};
