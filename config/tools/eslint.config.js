import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";

export default tseslint.config(
  {
    ignores: [
      "dist",
      "build",
      ".next",
      "out",
      "**/*.d.ts",
      "src/vite-env.d.ts",
      "**/*.generated.ts",
      "**/*.auto.ts",
      "**/generated/",
      "**/auto-generated/",
      "**/vendor/",
      "**/lib/",
      "**/libs/",
      "**/third-party/",
      "coverage/",
      ".nyc_output/",
      "**/coverage/",
      ".cache/",
      "*.tmp",
      "*.temp",
      ".temp/",
      ".tmp/",
      "docs/build/",
      "storybook-static/",
      ".eslintcache",
      "*.tsbuildinfo",
      "tests/**/*.js",
      "tests/**/*.cjs",
      "**/*.cjs",
      "playwright-report/**/*",
      "test-results/**/*",
      "**/playwright-report/**",
      "**/test-results/**",
      "**/*.html",
      "**/assets/**/*.js"
    ]
  },

  // Configuration for src files (main app - uses tsconfig.app.json)
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ["src/**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        project: ["../../tsconfig.app.json"],
        tsconfigRootDir: import.meta.dirname,
      },
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],
      "@typescript-eslint/no-unused-vars": "off",

      // Phase 4: Strict type enforcement rules (after AI agent swarm completion)

      // ZERO TOLERANCE: No explicit any types (100% completion achieved)
      "@typescript-eslint/no-explicit-any": "error",

      // Enforce type-only imports (prevents circular dependencies)
      "@typescript-eslint/consistent-type-imports": [
        "error",
        {
          "prefer": "type-imports",
          "disallowTypeAnnotations": false,
          "fixStyle": "separate-type-imports"
        }
      ],

      // Enforce type-only exports where applicable
      "@typescript-eslint/consistent-type-exports": [
        "error",
        {
          "fixMixedExportsWithInlineTypeSpecifier": true
        }
      ],

      // Prevent unnecessary type assertions
      "@typescript-eslint/no-unnecessary-type-assertion": "error",

      // Enforce consistent type definitions (interfaces over types)
      "@typescript-eslint/consistent-type-definitions": ["error", "interface"],

      // Array type consistency
      "@typescript-eslint/array-type": ["error", {
        "default": "array-simple"
      }],

      // Require explicit return types on exported functions
      "@typescript-eslint/explicit-module-boundary-types": "warn", // Start as warn, can upgrade to error later

      // Prevent empty interfaces
      "@typescript-eslint/no-empty-interface": "error",
    },
  },

  // Configuration for Node/build files (uses tsconfig.node.json)
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ["vite.config.ts", "vitest.config.ts"],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.node,
      parserOptions: {
        project: ["../../tsconfig.node.json"],
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      "@typescript-eslint/no-unused-vars": "off",
      "@typescript-eslint/no-explicit-any": "error",
    },
  },

  // Configuration for other TypeScript files (no type checking)
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: [
      "**/*.{ts,tsx}",
      "!src/**/*",
      "!vite.config.ts",
      "!vitest.config.ts"
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: { ...globals.browser, ...globals.node },
    },
    rules: {
      "@typescript-eslint/no-unused-vars": "off",
      "@typescript-eslint/no-explicit-any": "error",

      // Basic rules without type information
      "@typescript-eslint/consistent-type-definitions": ["error", "interface"],
      "@typescript-eslint/array-type": ["error", {
        "default": "array-simple"
      }],
      "@typescript-eslint/no-empty-interface": "error",
    },
  }
);
