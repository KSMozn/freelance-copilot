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

/**
 * Split-screen shell used by /login, /register, /admin/login. Left column
 * is brand-forward and only appears at md+; on mobile the whole surface
 * collapses to the form with a small logo header. The form column stays
 * neutral so shadcn Card inside `children` reads unchanged.
 */
export function AuthShell({
  variant = "careero",
  title = "Your AI Career Intelligence Platform",
  subtitle = "Careero helps you build the career you're capable of — from skills to opportunities, resumes to interviews.",
  slogan = BRAND.tagline,
  children,
}: Props) {
  const Mark = variant === "careero" ? CareeroMark : PersonaArmoryMark;
  const brandName = variant === "careero" ? BRAND.product : BRAND.company;

  return (
    <div className="grid min-h-screen grid-cols-1 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
      {/* Brand column — hidden below md, becomes a slim topbar there. */}
      <aside className="relative hidden overflow-hidden bg-[hsl(226_33%_8%)] md:flex md:flex-col md:justify-between md:p-12">
        {/* Ambient gradient wash — subtle, per the "gradients emphasize, not
            dominate" note in the brief. */}
        <div
          aria-hidden
          className="absolute -top-1/3 left-1/2 h-[640px] w-[640px] -translate-x-1/2 rounded-full bg-brand-gradient opacity-25 blur-3xl"
        />
        <div className="relative z-10 flex items-center gap-3 text-white">
          <Mark size={40} />
          <span className="text-lg font-semibold tracking-tight">
            {brandName}
          </span>
        </div>
        <div className="relative z-10 max-w-md text-white">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/60">
            {slogan}
          </p>
          <h1 className="mt-3 text-4xl font-semibold leading-tight tracking-tight">
            {title}
          </h1>
          <p className="mt-4 text-base text-white/70">{subtitle}</p>
        </div>
        <p className="relative z-10 text-xs text-white/40">
          © {new Date().getFullYear()} {BRAND.company}
        </p>
      </aside>

      {/* Form column */}
      <main className="flex flex-col items-center justify-center bg-background p-6">
        <div className="mb-8 flex items-center gap-2 md:hidden">
          <Mark size={26} />
          <span className="font-semibold tracking-tight">{brandName}</span>
        </div>
        <div className="w-full max-w-sm">{children}</div>
        <AboutFooter className="mt-8" />
      </main>
    </div>
  );
}
