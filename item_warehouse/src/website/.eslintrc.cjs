/* eslint-env node */
module.exports = {
  extends: [
    "eslint:recommended",
    "prettier",
    "plugin:@typescript-eslint/strict-type-checked",
    "plugin:@typescript-eslint/stylistic-type-checked",
  ],
  plugins: ["@typescript-eslint", "import"],
  parser: "@typescript-eslint/parser",
  parserOptions: {
    project: true,
    tsconfigRootDir: __dirname,
  },
  rules: {
    // "import/no-unused-modules": [1, { unusedExports: true }],
    "no-unused-vars": "error",
  },
  root: true,
  env: {
    node: true,
  },
};
