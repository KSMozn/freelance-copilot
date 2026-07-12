import type { Meta, StoryObj } from "@storybook/react-vite";

import { AboutFooter } from "./AboutFooter";

const meta = {
  title: "shared/ui/brand/AboutFooter",
  component: AboutFooter,
  parameters: { layout: "centered" },
  tags: ["autodocs"],
} satisfies Meta<typeof AboutFooter>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
