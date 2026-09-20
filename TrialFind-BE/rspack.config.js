const { rspack } = require('@rspack/core');
const { RunScriptWebpackPlugin } = require('run-script-webpack-plugin');

/** @type {import('@rspack/cli').Configuration} */

const config = {

    node: {
        __dirname: true,
    },
    context: __dirname,
    target: 'node',
    entry: {
        main: ['@rspack/core/hot/poll?100', './src/main.ts'],
    },
    resolve: {
        extensions: ['...', '.ts', '.tsx', '.jsx'],
    },
    module: {
        rules: [
            {
                test: /\.ts$/,
                use: {
                    loader: 'builtin:swc-loader',
                    options: {
                        jsc: {
                            parser: {
                                syntax: 'typescript',
                                decorators: true,
                            },
                            transform: {
                                legacyDecorator: true,
                                decoratorMetadata: true,
                            },
                        },
                    },
                },
            },
            {
                test: /\.node$/,
                use: [
                    {
                        loader: 'node-loader',
                        options: {
                            name: '[path][name].[ext]',
                        },
                    },
                ],
            },
        ],
    },
    optimization: {
        minimize: false,
    },
    externalsType: 'commonjs',
    plugins: [
        new rspack.HotModuleReplacementPlugin(),
        !process.env.BUILD &&

        new RunScriptWebpackPlugin({
            name: 'main.js',
            autoRestart: false,
        }),
    ].filter(Boolean),

    devServer: {
        devMiddleware: {
            writeToDisk: true,
        },
        hot: false,
    },
    externals: [
        function (obj, callback) {
            const resource = obj.request;
            const lazyImports = [
                '@nestjs/core',
                'mock-aws-s3',
                'aws-sdk',
                'nock',
                '@nestjs/common',
                '@nestjs/microservices',
                '@nestjs/platform-express',
                'cache-manager',
                'class-validator',
                'class-transformer',
                'class-transformer/storage',
                // ADD THIS
                '@nestjs/microservices/microservices-module',
                '@nestjs/websockets',
                'socket.io-adapter',
                'utf-8-validate',
                'bufferutil',
                'kerberos',
                '@mongodb-js/zstd',
                'snappy',
                '@aws-sdk/credential-providers',
                'mongodb-client-encryption',
                '@nestjs/websockets/socket-module',
                'bson-ext',
                'snappy/package.json',
                'aws4',
            ];
            if (!lazyImports.includes(resource)) {
                return callback();
            }
            try {
                require.resolve(resource);
            } catch (err) {
                callback(null, resource);
            }
            callback();
        },
    ],
};
module.exports = config;
