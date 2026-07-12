import type { Meta, StoryObj } from "@storybook/react-vite";

import { Button } from "@/shared/ui/button";
import { AuthShell } from "./AuthShell";

const meta = {
  title: "shared/ui/brand/AuthShell",
  component: AuthShell,
  parameters: { layout: "fullscreen" },
  tags: ["autodocs"],
} satisfies Meta<typeof AuthShell>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Careero: Story = {
  args: {
    children: <Button className="w-full">Continue</Button>,
  },
};

export const Admin: Story = {
  args: {
    variant: "personaarmory-admin",
    title: "PersonaArmory Admin",
    subtitle: "Operate the platform and support students.",
    children: <Button className="w-full">Sign in</Button>,
  },
};
