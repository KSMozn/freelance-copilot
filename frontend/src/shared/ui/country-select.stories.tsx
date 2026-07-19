import { useState } from "react";

import type { Meta, StoryObj } from "@storybook/react-vite";

import type { CountryCode } from "@/shared/lib/phone";

import { CountrySelect } from "./country-select";

const meta = {
  title: "shared/ui/CountrySelect",
  component: CountrySelect,
  parameters: { layout: "centered" },
  tags: ["autodocs"],
} satisfies Meta<typeof CountrySelect>;

export default meta;
type Story = StoryObj<typeof meta>;

function Controlled({
  variant,
  showCallingCode = true,
  initial = "EG",
}: {
  variant: "compact" | "full";
  showCallingCode?: boolean;
  initial?: CountryCode | "";
}) {
  const [country, setCountry] = useState<CountryCode | "">(initial);
  return (
    <div className="w-72 space-y-2">
      <CountrySelect
        value={country}
        onChange={setCountry}
        variant={variant}
        showCallingCode={showCallingCode}
      />
      <p className="text-xs text-muted-foreground">
        Selected: <span className="font-mono">{country || "—"}</span> — search by name (“Egypt”),
        ISO code (“EG”), or calling code (“+20”).
      </p>
    </div>
  );
}

export const Full: Story = {
  args: { value: "EG", onChange: () => {} },
  render: () => <Controlled variant="full" />,
};

export const Compact: Story = {
  args: { value: "EG", onChange: () => {} },
  render: () => <Controlled variant="compact" />,
};

export const CountryPicker: Story = {
  args: { value: "EG", onChange: () => {} },
  render: () => <Controlled variant="full" showCallingCode={false} />,
};

export const Empty: Story = {
  args: { value: "", onChange: () => {} },
  render: () => <Controlled variant="full" showCallingCode={false} initial="" />,
};

export const Disabled: Story = {
  args: { value: "SA", onChange: () => {}, disabled: true },
};
