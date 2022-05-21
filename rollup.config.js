import typescript from '@rollup/plugin-typescript'

export default [
  {
    input: 'src/ts/index.ts',
    output: {
      sourcemap: true,
      format: 'iife',
      file: 'src/addon/web/editor/editor.js'
    },
    plugins: [
      typescript({
        sourceMap: true,
        inlineSources: true
      })
    ]
  }
]
