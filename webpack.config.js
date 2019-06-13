const path = require('path');
const webpack = require('webpack');
const AssetsPlugin = require('assets-webpack-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');

module.exports = {
  mode: 'production',
  entry: {
    foo: './temboardui/static/js/foo.js',
    activity: './temboardui/plugins/activity/static/js/temboard.activity.js',
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
    ]
  },
  plugins: [
    new CleanWebpackPlugin(),
    new webpack.NamedModulesPlugin(),
    new AssetsPlugin({
      prettyPrint: true
    })
  ]
};
