import type { Meta, StoryObj } from "@storybook/react-vite";

import { Input } from "./input";
import { Label } from "./label";

const meta = {
  title: "shared/ui/Label",
  component: Label,
  parameters: { layout: "centered" },
  tags: ["autodocs"],
} satisfies Meta<typeof Label>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: { children: "Full name" } };

export const WithInput: Story = {
  render: () => (
    <div className="w-72 space-y-2">
      <Label htmlFor="sb-name">Full name</Label>
      <Input id="sb-name" placeholder="Jane Student" />
    </div>
  ),
};
