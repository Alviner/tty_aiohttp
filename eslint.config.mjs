import path from "node:path";
import { fileURLToPath } from "node:url";
import js from "@eslint/js";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const compat = new FlatCompat({
    baseDirectory: __dirname,
    recommendedConfig: js.configs.recommended,
    allConfig: js.configs.all
});

export default [{
    ignores: [
        "**/vendor.*",
        "**/es-module-shims.*",
        "**/env/",
        "**/.pnp.*",
        "**/.venv/",
        "!**/vendor.js",
        "**/buildVendor.js",
    ],
}, ...compat.extends("plugin:vue/vue3-recommended", "eslint:recommended"), {
    rules: {
        "vue/multi-word-component-names": ["error", {
            ignores: ["Home"],
        }],

        "vue/html-self-closing": ["error", {
            html: {
                void: "never",
                normal: "never",
                component: "never",
            },
        }],
    },
}, {
    files: ["**/*.js", "**/*.vue"],
}];
