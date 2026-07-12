import type { Meta, StoryObj } from "@storybook/react-vite";

import { Input } from "./input";

const meta = {
  title: "shared/ui/Input",
  component: Input,
  parameters: { layout: "centered" },
  tags: ["autodocs"],
} satisfies Meta<typeof Input>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: { placeholder: "jane.student@school.edu", className: "w-72" },
};

export const Disabled: Story = {
  args: { placeholder: "Disabled", disabled: true, className: "w-72" },
};
