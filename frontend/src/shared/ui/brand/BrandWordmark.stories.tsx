import type { Meta, StoryObj } from "@storybook/react-vite";

import { BrandWordmark } from "./BrandWordmark";

const meta = {
  title: "shared/ui/brand/BrandWordmark",
  component: BrandWordmark,
  parameters: { layout: "centered" },
  tags: ["autodocs"],
} satisfies Meta<typeof BrandWordmark>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Careero: Story = { args: { variant: "careero" } };
export const Admin: Story = { args: { variant: "careero-admin" } };
