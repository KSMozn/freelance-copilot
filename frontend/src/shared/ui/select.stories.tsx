import { useState } from "react";

import type { Meta, StoryObj } from "@storybook/react-vite";

import { Select } from "./select";

const meta = {
  title: "shared/ui/Select",
  component: Select,
  parameters: { layout: "centered" },
  tags: ["autodocs"],
} satisfies Meta<typeof Select>;

export default meta;
type Story = StoryObj<typeof meta>;

const OPTIONS = [
  { value: "", label: "—" },
  { value: "bachelor", label: "Bachelor's" },
  { value: "master", label: "Master's" },
  { value: "phd", label: "PhD" },
];

function ControlledSelect({ disabled }: { disabled?: boolean }) {
  const [value, setValue] = useState("");
  return (
    <Select
      value={value}
      onChange={(e) => setValue(e.target.value)}
      options={OPTIONS}
      placeholder="Select a degree…"
      disabled={disabled}
      className="w-64"
    />
  );
}

export const Default: Story = {
  args: { value: "", onChange: () => {}, options: OPTIONS },
  render: () => <ControlledSelect />,
};

export const Disabled: Story = {
  args: { value: "", onChange: () => {}, options: OPTIONS },
  render: () => <ControlledSelect disabled />,
};
