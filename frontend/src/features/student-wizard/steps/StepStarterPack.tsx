import { CareerStarterPack } from "@/features/student-wizard/career-pack/CareerStarterPack";
import { AboutFooter } from "@/shared/ui/brand/AboutFooter";

export function StepStarterPack() {
  return (
    <div className="space-y-4">
      <CareerStarterPack />
      <AboutFooter className="pt-2" />
    </div>
  );
}
