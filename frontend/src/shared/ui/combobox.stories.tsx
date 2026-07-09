import { useState } from "react";

import type { Meta, StoryObj } from "@storybook/react-vite";

import { Combobox } from "./combobox";

const meta = {
  title: "shared/ui/Combobox",
  component: Combobox,
  parameters: { layout: "centered" },
  tags: ["autodocs"],
} satisfies Meta<typeof Combobox>;

export default meta;
type Story = StoryObj<typeof meta>;

const OPTIONS = ["Python", "TypeScript", "React", "FastAPI", "PostgreSQL", "Docker", "Tailwind"];

function ControlledCombobox() {
  const [value, setValue] = useState("");
  return (
    <div className="w-72">
      <Combobox value={value} onChange={setValue} options={OPTIONS} placeholder="Python" />
      <p className="mt-2 text-xs text-muted-foreground">Type to filter — free text is allowed.</p>
    </div>
  );
}

export const Default: Story = {
  args: { value: "", onChange: () => {}, options: OPTIONS },
  render: () => <ControlledCombobox />,
};
