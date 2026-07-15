import type { ReactNode } from "react";

import { BRAND } from "@/shared/config/brand";

import { AboutFooter } from "./AboutFooter";
import { CareeroMark } from "./CareeroMark";
import { PersonaArmoryMark } from "./PersonaArmoryMark";

interface Props {
  variant?: "careero" | "personaarmory-admin";
  title?: string;
  subtitle?: string;
  slogan?: string;
  children: ReactNode;
}

export function AuthShell({
  variant = "careero",
  title = "Build your first student CV with confidence",
  subtitle = "Turn your education, projects, internships, and skills into an ATS-friendly CV you can download as PDF or DOCX.",
  slogan = BRAND.tagline,
  children,
}: Props) {
  const Mark = variant === "careero" ? CareeroMark : PersonaArmoryMark;
  const brandName = variant === "careero" ? BRAND.product : BRAND.company;

  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      <div
        aria-hidden
        className="bg-brand-gradient pointer-events-none absolute -top-1/3 left-1/4 h-[640px] w-[640px] -translate-x-1/2 rounded-full opacity-25 blur-3xl"
      />

      <div className="relative z-10 mx-auto flex min-h-screen max-w-6xl items-center justify-center gap-10 px-6 py-12 md:justify-between">
        <div className="hidden max-w-md text-white md:block">
          <div className="flex items-center gap-3">
            <Mark size={40} />
            <span className="text-xl font-semibold tracking-tight">{brandName}</span>
          </div>
          <p className="mt-10 text-xs font-semibold uppercase tracking-[0.2em] text-white/60">
            {slogan}
          </p>
          <h1 className="mt-3 text-4xl font-semibold leading-tight tracking-tight">{title}</h1>
          <p className="mt-4 text-base text-white/70">{subtitle}</p>
        </div>

        <div className="flex w-full flex-col items-center md:w-auto">
          <div className="mb-8 flex items-center gap-2 text-white md:hidden">
            <Mark size={26} />
            <span className="font-semibold tracking-tight">{brandName}</span>
          </div>
          <div className="w-full max-w-sm">{children}</div>
          <AboutFooter className="mt-8" />
        </div>
      </div>

      <p className="pointer-events-none absolute bottom-6 left-6 z-10 hidden text-xs text-white/40 md:block">
        © {new Date().getFullYear()} {BRAND.company}
      </p>
    </div>
  );
}
