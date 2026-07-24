import { useState } from "react";

import type { Meta, StoryObj } from "@storybook/react-vite";

import type { GeoCity } from "@/shared/lib/geo";
import type { CountryCode } from "@/shared/lib/phone";

import { CitySelect } from "./city-select";

const meta = {
  title: "shared/ui/CitySelect",
  component: CitySelect,
  parameters: { layout: "centered" },
  tags: ["autodocs"],
} satisfies Meta<typeof CitySelect>;

export default meta;
type Story = StoryObj<typeof meta>;

// Fixtures — stories inject these via `loadCities` so they never pull the real
// 17 MB `cities.json` dataset.
const EG_CITIES: GeoCity[] = [
  { name: "Alexandria", country: "EG", lat: 31.2, lng: 29.92 },
  { name: "Cairo", country: "EG", lat: 30.06, lng: 31.25 },
  { name: "Giza", country: "EG", lat: 30.01, lng: 31.21 },
  { name: "Mansoura", country: "EG", lat: 31.04, lng: 31.38 },
  { name: "Port Said", country: "EG", lat: 31.26, lng: 32.28 },
];

// Two cities that share a name — disambiguated by region.
const US_DUPLICATES: GeoCity[] = [
  { name: "Portland", country: "US", region: "Oregon", lat: 45.52, lng: -122.68 },
  { name: "Portland", country: "US", region: "Maine", lat: 43.66, lng: -70.26 },
  { name: "Springfield", country: "US", region: "Illinois", lat: 39.8, lng: -89.64 },
  { name: "Springfield", country: "US", region: "Missouri", lat: 37.22, lng: -93.29 },
];

function Controlled({
  country,
  loadCities,
  invalid,
  disabled,
}: {
  country: CountryCode | "";
  loadCities?: (iso: CountryCode) => Promise<GeoCity[]>;
  invalid?: boolean;
  disabled?: boolean;
}) {
  const [city, setCity] = useState<GeoCity | null>(null);
  return (
    <div className="w-72 space-y-2">
      <CitySelect
        country={country}
        value={city?.name ?? ""}
        onChange={setCity}
        loadCities={loadCities}
        invalid={invalid}
        disabled={disabled}
      />
      <p className="text-xs text-muted-foreground">
        Selected: <span className="font-mono">{city?.name || "—"}</span>
        {city?.region ? ` (${city.region})` : ""}
      </p>
    </div>
  );
}

export const Populated: Story = {
  args: { country: "EG", value: "", onChange: () => {} },
  render: () => <Controlled country="EG" loadCities={async () => EG_CITIES} />,
};

export const DuplicateNames: Story = {
  args: { country: "US", value: "", onChange: () => {} },
  render: () => <Controlled country="US" loadCities={async () => US_DUPLICATES} />,
};

export const Loading: Story = {
  args: { country: "EG", value: "", onChange: () => {} },
  render: () => (
    <Controlled
      country="EG"
      loadCities={() =>
        new Promise<GeoCity[]>((resolve) => setTimeout(() => resolve(EG_CITIES), 4000))
      }
    />
  ),
};

export const NoCities: Story = {
  args: { country: "AX", value: "", onChange: () => {} },
  render: () => <Controlled country="AX" loadCities={async () => []} />,
};

export const DisabledUntilCountry: Story = {
  args: { country: "", value: "", onChange: () => {} },
  render: () => <Controlled country="" />,
};

export const Invalid: Story = {
  args: { country: "EG", value: "", onChange: () => {} },
  render: () => <Controlled country="EG" loadCities={async () => EG_CITIES} invalid />,
};
