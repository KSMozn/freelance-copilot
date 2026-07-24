import { useState } from "react";

import type { Meta, StoryObj } from "@storybook/react-vite";

import type { PhoneValue } from "@/shared/lib/phone";
import { Label } from "@/shared/ui/label";

import { PhoneInput } from "./phone-input";

const meta = {
  title: "shared/ui/PhoneInput",
  component: PhoneInput,
  parameters: { layout: "centered" },
  tags: ["autodocs"],
} satisfies Meta<typeof PhoneInput>;

export default meta;
type Story = StoryObj<typeof meta>;

function Controlled(props: Partial<React.ComponentProps<typeof PhoneInput>>) {
  const [value, setValue] = useState(props.value ?? "");
  const [meta, setMeta] = useState<PhoneValue | null>(null);
  return (
    <div className="w-80 space-y-2">
      <Label htmlFor="story-phone">Phone</Label>
      <PhoneInput
        {...props}
        id="story-phone"
        value={value}
        onChange={(stored, next) => {
          setValue(stored);
          setMeta(next);
        }}
      />
      <pre className="overflow-x-auto rounded-md bg-muted p-2 text-xs text-muted-foreground">
        {JSON.stringify(meta ?? { stored: value }, null, 2)}
      </pre>
    </div>
  );
}

export const Default: Story = {
  args: { value: "", onChange: () => {} },
  render: () => <Controlled defaultCountry="EG" />,
};

export const Prefilled: Story = {
  args: { value: "+12025550123", onChange: () => {} },
  render: () => <Controlled value="+12025550123" />,
};

export const Required: Story = {
  args: { value: "", onChange: () => {}, required: true },
  render: () => <Controlled required showErrorsWhen="always" defaultCountry="SA" />,
};

export const ReadOnly: Story = {
  args: { value: "+201012345678", onChange: () => {}, readOnly: true },
  render: () => <Controlled value="+201012345678" readOnly />,
};

export const Disabled: Story = {
  args: { value: "+441632960961", onChange: () => {}, disabled: true },
  render: () => <Controlled value="+441632960961" disabled />,
};
