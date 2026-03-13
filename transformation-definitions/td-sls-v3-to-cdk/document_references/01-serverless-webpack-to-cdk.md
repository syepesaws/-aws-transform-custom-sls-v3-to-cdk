# serverless-webpack → CDK NodejsFunction

## Serverless Config → CDK Mapping

```yaml
# serverless.yml
plugins:
  - serverless-webpack
custom:
  webpack:
    webpackConfig: 'webpack.config.js'
    includeModules:
      forceExclude: [aws-sdk]
```

```typescript
// CDK - Use esbuild (default, faster)
const fn = new NodejsFunction(this, 'MyFunction', {
  entry: 'src/handlers/myHandler.ts',
  bundling: {
    minify: true,
    sourceMap: true,
    target: 'es2020',
    externalModules: ['@aws-sdk/*'],  // Exclude AWS SDK v3
    format: OutputFormat.ESM,
  },
});
```

## Advanced esbuild Options

```typescript
bundling: {
  minify: true,
  sourceMap: true,
  sourceMapMode: SourceMapMode.INLINE,
  target: 'es2020',
  loader: { '.png': 'dataurl', '.graphql': 'text' },
  define: { 'process.env.API_KEY': JSON.stringify('value') },
  esbuildArgs: { '--tree-shaking': 'true' },
  mainFields: ['module', 'main'],
  nodeModules: ['native-module'],  // Include specific modules
}
```

## Custom Webpack (if required)

```typescript
// Build via package.json script: "build": "webpack --config webpack.config.js"
const fn = new Function(this, 'MyFunction', {
  runtime: Runtime.NODEJS_20_X,
  handler: 'index.handler',
  code: Code.fromAsset('dist', {
    bundling: {
      image: Runtime.NODEJS_20_X.bundlingImage,
      command: ['bash', '-c', 'npm install && npm run build && cp -r dist/* /asset-output/'],
    },
  }),
});
```

## Key Differences
- esbuild is 10-100x faster than webpack
- externalModules replaces includeModules.forceExclude
- aws-sdk → @aws-sdk/* (SDK v2 → v3)
