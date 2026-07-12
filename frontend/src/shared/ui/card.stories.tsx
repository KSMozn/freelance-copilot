import type { Meta, StoryObj } from "@storybook/react-vite";

import { Button } from "./button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./card";

const meta = {
  title: "shared/ui/Card",
  component: Card,
  parameters: { layout: "centered" },
  tags: ["autodocs"],
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Composed: Story = {
  render: () => (
    <Card className="w-96">
      <CardHeader>
        <CardTitle>Card title</CardTitle>
        <CardDescription>A short supporting description.</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm">Card body content goes here.</p>
      </CardContent>
      <CardFooter>
        <Button size="sm">Action</Button>
      </CardFooter>
    </Card>
  ),
};
