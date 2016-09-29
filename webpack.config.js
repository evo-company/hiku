var path = require('path'),
    webpack = require('webpack');

module.exports = {
  resolve: {
    fallback: process.env.NODE_PATH
  },
  resolveLoader: {
    fallback: process.env.NODE_PATH
  },
  plugins: [
    new webpack.ProvidePlugin({
      Promise: 'es6-promise',
      fetch: 'imports?this=>global!exports?global.fetch!whatwg-fetch'
    }),
    new webpack.DefinePlugin({
      'process.env': {
        'NODE_ENV': JSON.stringify('production')
      }
    }),
    new webpack.optimize.UglifyJsPlugin({
      compress: {
        warnings: false
      }
    })
  ],
  module: {
    loaders: [
      {
        test: /\.jsx$/,
        loader: 'babel',
        query: {
          presets: ['es2015', 'react']
        }
      },
      {
        test: /\.css$/,
        loader: "style-loader!css-loader"
      }
    ]
  },
  entry: './hiku/console/assets/console.jsx',
  output: {
    path: './hiku/console/assets',
    filename: 'console.js'
  }
};
