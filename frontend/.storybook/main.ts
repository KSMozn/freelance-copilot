import type { StorybookConfig } from "@storybook/react-vite";

// Stories live co-located with the shared/ui components they document —
// same convention as the reference design system (adapted: our components
// live in src/shared/ui, not a top-level lib/). The react-vite framework
// auto-loads vite.config.ts, so the @/ alias resolves inside stories.
const config: StorybookConfig = {
  stories: ["../src/shared/ui/**/*.stories.@(ts|tsx)"],
  addons: ["@storybook/addon-docs", "@storybook/addon-a11y"],
  framework: {
    name: "@storybook/react-vite",
    options: {},
  },
};

export default config;
