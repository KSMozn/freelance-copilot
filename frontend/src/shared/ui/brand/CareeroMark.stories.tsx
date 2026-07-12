import type { Meta, StoryObj } from "@storybook/react-vite";

import { CareeroMark } from "./CareeroMark";

const meta = {
  title: "shared/ui/brand/CareeroMark",
  component: CareeroMark,
  parameters: { layout: "centered" },
  tags: ["autodocs"],
} satisfies Meta<typeof CareeroMark>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: { size: 64 } };
