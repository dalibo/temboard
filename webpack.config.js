const path = require('path');
const webpack = require('webpack');
const AssetsPlugin = require('assets-webpack-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');

module.exports = {
  mode: 'production',
  entry: {
    foo: './temboardui/static/js/foo.js',
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
  plugins: [
    new CleanWebpackPlugin(),
    new webpack.NamedModulesPlugin(),
    new AssetsPlugin({
      prettyPrint: true
    })
  ]
};
