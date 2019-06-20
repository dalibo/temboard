const path = require('path');
const webpack = require('webpack');
const AssetsPlugin = require('assets-webpack-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const MomentLocalesPlugin = require('moment-locales-webpack-plugin');

module.exports = {
  mode: 'production',
  entry: {
    activity: './temboardui/plugins/activity/static/js/activity.js',
    dashboard: './temboardui/plugins/dashboard/static/js/dashboard.js',
    home: './temboardui/static/js/home.js',
    maintenance: './temboardui/plugins/maintenance/static/js/maintenance.js',
    'maintenance.database': './temboardui/plugins/maintenance/static/js/maintenance.database.js',
    'maintenance.schema': './temboardui/plugins/maintenance/static/js/maintenance.schema.js',
    'maintenance.table': './temboardui/plugins/maintenance/static/js/maintenance.table.js',
    monitoring: './temboardui/plugins/monitoring/static/js/monitoring.js',
    'monitoring.checks': './temboardui/plugins/monitoring/static/js/checks.js',
    'monitoring.check': './temboardui/plugins/monitoring/static/js/check.js',
    notifications: './temboardui/static/js/notifications.js',
    pgconf: './temboardui/plugins/pgconf/static/js/pgconf.js',
    'settings.group': './temboardui/static/js/settings.group.js',
    'settings.user': './temboardui/static/js/settings.user.js',
    'settings.instance': './temboardui/static/js/settings.instance.js',
    'settings.notifications': './temboardui/static/js/settings.notifications.js',
  },
  output: {
    path: path.resolve(__dirname, 'temboardui/static/js/build'),
    publicPath: '/js/build',
    filename: '[name].[chunkhash:8].js',
    chunkFilename: '[name].[chunkhash:8].js'
  },
  optimization: {
    // one runtime for all entrypoints
    //runtimeChunk: 'single',
    // readable chunk ids even in production mode
    chunkIds: 'named',
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        // create a chunk with the most often used packages
        commons: {
          test: /[\\/]node_modules[\\/](jquery|lodash)[\\/]/,
          name: 'commons',
          chunks: 'all',
        }
      }
    },
  },
  module: {
    rules: [
      // Disable AMD
      // https://gist.github.com/jrunestone/2fbe5d6d5e425b7c046168b6d6e74e95
      {
        test: /datatables\.net.*/,
        loader: 'imports-loader?define=>false'
      },
      {
        test: /\.css$/i,
        use: ['style-loader', 'css-loader'],
      },
      // Expose jQuery as window.$ so that it's available in unbuilt js
      // (inlined in templates)
      // https://github.com/webpack-contrib/expose-loader
      {
        test: require.resolve('jquery'),
        use: [{
          loader: 'expose-loader',
          options: '$'
        }]
      }
    ]
  },
  plugins: [
    new CleanWebpackPlugin(),
    new webpack.NamedModulesPlugin(),
    new AssetsPlugin({
      prettyPrint: true,
      entrypoints: true
    }),
    new webpack.ProvidePlugin({
      $: 'jquery',
      jQuery: 'jquery',
      'window.jQuery': 'jquery'
    }),
    // To strip all locales except “en”
    new MomentLocalesPlugin()
  ],
  resolve: {
    alias: {
      'vue$': 'vue/dist/vue.esm.js',
      'base$': path.resolve(__dirname, 'temboardui/static/js/base.js'),
    }
  },
  performance: {
    maxEntrypointSize: 600000
  }
};
