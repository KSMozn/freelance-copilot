// Flat ESLint config (ESLint 9). Ports the legacy .eslintrc.cjs rules and
// adds the feature-driven-architecture boundary zones copied from the
// reference project (eslint-plugin-import-x no-restricted-paths):
//
//   shared/                 sink — may not import app/ or features/
//   features/auth           foundation — may not import sibling features
//   features/professional   DORMANT — nothing outside it may import it,
//                           and it may not import the live features
//
// `@/` imports resolve through the TypeScript resolver so the zones see
// real file paths.
import js from "@eslint/js";
import tsPlugin from "@typescript-eslint/eslint-plugin";
import tsParser from "@typescript-eslint/parser";
import importX from "eslint-plugin-import-x";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import globals from "globals";

export default [
  // scripts/ holds Node maintenance scripts (not app code); .storybook and
  // storybook-static are tooling/output — all outside the lint surface,
  // matching the reference project's ignore list.
  { ignores: ["dist", "node_modules", "*.config.js", "scripts", ".storybook", "storybook-static"] },
  js.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
        ecmaFeatures: { jsx: true },
      },
      globals: { ...globals.browser, ...globals.es2021 },
    },
    plugins: {
      "@typescript-eslint": tsPlugin,
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
      "import-x": importX,
    },
    settings: {
      "import-x/resolver": { typescript: { project: "./tsconfig.json" } },
    },
    rules: {
      ...tsPlugin.configs["eslint-recommended"].overrides[0].rules,
      ...tsPlugin.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      // No feature-level re-export barrels — import the concrete file.
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@/features/*/index", "@/features/*/index.*", "@/features/*/*/index"],
              message: "Feature barrels are banned — import the concrete file.",
            },
          ],
        },
      ],
      "import-x/no-restricted-paths": [
        "error",
        {
          zones: [
            {
              target: "./src/shared",
              from: ["./src/app", "./src/features"],
              message: "shared/ is a sink — it must not import from app/ or features/.",
            },
            {
              target: "./src/features/auth",
              from: [
                "./src/features/student-wizard",
                "./src/features/admin",
                "./src/features/professional",
              ],
              message: "auth is the foundation feature — it must not import other features.",
            },
            // The professional/career-OS surface is dormant. Nothing in the
            // live app may import it; mounting it again is a deliberate act
            // (restore the routes from git history), not an accidental import.
            {
              target: "./src/app",
              from: "./src/features/professional",
              message: "features/professional is dormant — do not register or mount it.",
            },
            {
              target: "./src/features/student-wizard",
              from: "./src/features/professional",
              message: "features/professional is dormant — live features must not import it.",
            },
            {
              target: "./src/features/admin",
              from: "./src/features/professional",
              message: "features/professional is dormant — live features must not import it.",
            },
            {
              target: "./src/features/professional",
              from: ["./src/features/student-wizard", "./src/features/admin"],
              message: "the dormant professional surface must not depend on live features.",
            },
          ],
        },
      ],
    },
  },
  // Storybook stories export a default meta object (framework requirement),
  // which react-refresh's only-export-components heuristic misreads.
  {
    files: ["**/*.stories.tsx"],
    rules: {
      "react-refresh/only-export-components": "off",
    },
  },
];
