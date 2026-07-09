import type { Meta, StoryObj } from "@storybook/react-vite";

import { Button } from "./button";

const meta = {
  title: "shared/ui/Button",
  component: Button,
  parameters: { layout: "centered" },
  tags: ["autodocs"],
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: { children: "Button" } };

export const Brand: Story = {
  args: { variant: "brand", children: "Download CV" },
};

export const Outline: Story = { args: { variant: "outline", children: "Outline" } };

export const Secondary: Story = { args: { variant: "secondary", children: "Secondary" } };

export const Ghost: Story = { args: { variant: "ghost", children: "Ghost" } };

export const Destructive: Story = { args: { variant: "destructive", children: "Delete" } };

export const LinkVariant: Story = { args: { variant: "link", children: "Link" } };

export const Small: Story = { args: { size: "sm", children: "Small" } };

export const Large: Story = { args: { size: "lg", children: "Large" } };

export const Disabled: Story = { args: { disabled: true, children: "Disabled" } };

// Exercises the asChild path — the Base UI `render`-prop mechanism that
// replaced the Radix Slot implementation. The button's classes must land
// on the anchor element.
export const AsChild: Story = {
  args: {
    asChild: true,
    variant: "outline",
    children: <a href="#as-child">Renders as an anchor</a>,
  },
};
