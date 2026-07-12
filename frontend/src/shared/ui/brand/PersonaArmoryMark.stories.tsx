import type { Meta, StoryObj } from "@storybook/react-vite";

import { PersonaArmoryMark } from "./PersonaArmoryMark";

const meta = {
  title: "shared/ui/brand/PersonaArmoryMark",
  component: PersonaArmoryMark,
  parameters: { layout: "centered" },
  tags: ["autodocs"],
} satisfies Meta<typeof PersonaArmoryMark>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: { size: 64 } };
