module.exports = function(grunt) {
  grunt.initConfig({
    sass: {
      options: {
        sourceMap: true,
        includePaths: ['node_modules/bootstrap/scss']
      },
      // this is the "dev" Sass config used with "grunt watch" command
      dev: {
        options: {
          outputStyle: 'expanded'
        },
        files: {
          'temboardui/static/css/temboard.css': 'temboardui/static/src/temboard.scss'
        }
      },
      dist: {
        options: {
          outputStyle: 'compressed'
        },
        files: {
          'temboardui/static/css/temboard.css': 'temboardui/static/src/temboard.scss'
        }
      }
    },
    postcss: {
      options: {
        map: true,
        processors: require('autoprefixer')({browsers: 'last 2 versions'})
      },
      dist: {
        src: 'temboardui/static/css/temboard.css'
      }
    },
    copy: {
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
        files: 'temboardui/static/src/*.scss',
        tasks: ['sass:dist']
      }
    }
  });
  grunt.loadNpmTasks('grunt-sass');
  grunt.loadNpmTasks('grunt-postcss');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-copy');

  grunt.registerTask('bootstrap', [
    'copy:bootstrapjs',
    'sass:dist',
    'postcss:dist'
  ]);
};
