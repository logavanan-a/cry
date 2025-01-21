var webpack = require('webpack');
var path = require('path');

module.exports = {
    devtool: 'inline-source-map',
    // devServer:{
    //     headers: {
    //   "Access-Control-Allow-Origin": "*",
    //   "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
    //   "Access-Control-Allow-Headers": "X-Requested-With, content-type, Authorization"
    // }
    // },
    //cache: true,
    entry: {
    LoginBundle: './src/login.js',
    ListingBundle:'./src/listing.js',
    bundle : './src/index.js',

    // AdminBundle: './React/AdminView.js',
    // RegisterBundle: './React/Registration.js',        
  },
    output: {
path:path.join(__dirname, 'public/static/Bundles'),
      filename: '[name].js',
},
     devServer: {
        inline: false,
    },

    module: {
        loaders: [
        {
             test: /\.jsx?$/,
             exclude: /node_modules/,
             loaders: ['babel?presets[]=react,presets[]=es2015']
             
        }
        
         
        ]
    },
    resolveLoader: {
    moduleExtensions: ['-loader']
  },
     /*resolve: {
        extensions: ["", ".js", ".jsx"],
        root: path.resolve(__dirname, "client"),
        modulesDirectories: ["node_modules"]
    },*/
    watch:true


};
