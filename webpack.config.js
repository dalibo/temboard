const path = require('path');
const webpack = require('webpack');
const AssetsPlugin = require('assets-webpack-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const MomentLocalesPlugin = require('moment-locales-webpack-plugin');

module.exports = {
  mode: 'production',
  entry: {
    activity: './temboardui/plugins/activity/static/js/temboard.activity.js',
    base: './temboardui/static/js/base.js',
    dashboard: './temboardui/plugins/dashboard/static/js/temboard.dashboard.js',
    home: './temboardui/static/js/temboard.home.js',
    monitoring: './temboardui/plugins/monitoring/static/js/temboard.monitoring.js',
    notifications: './temboardui/static/js/temboard.notifications.js',
    'settings.group': './temboardui/static/js/temboard.settings.group.js',
    'settings.user': './temboardui/static/js/temboard.settings.user.js',
    'settings.instance': './temboardui/static/js/temboard.settings.instance.js',
  },
  output: {
    path: path.resolve(__dirname, 'temboardui/static/js/build'),
    publicPath: '/js/build',
    filename: '[name].[chunkhash:8].js',
    chunkFilename: '[name].[chunkhash:8].js'
  },
  optimization: {
    // one runtime for all entrypoints
    runtimeChunk: 'single',
    // readable chunk ids even in production mode
    chunkIds: 'named',
    splitChunks: {
      chunks: 'all'
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
      }
    ]
  },
  plugins: [
    new CleanWebpackPlugin(),
    new webpack.NamedModulesPlugin(),
    new AssetsPlugin({
      prettyPrint: true
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
      'vue$': 'vue/dist/vue.esm.js'
    }
  }
};
