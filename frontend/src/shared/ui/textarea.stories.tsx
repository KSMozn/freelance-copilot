import type { Meta, StoryObj } from "@storybook/react-vite";

import { Textarea } from "./textarea";

const meta = {
  title: "shared/ui/Textarea",
  component: Textarea,
  parameters: { layout: "centered" },
  tags: ["autodocs"],
} satisfies Meta<typeof Textarea>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: { placeholder: "A short paragraph about who you are…", className: "w-96" },
};

export const Disabled: Story = {
  args: { placeholder: "Disabled", disabled: true, className: "w-96" },
};
