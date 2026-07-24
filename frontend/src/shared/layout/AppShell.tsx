import type { ReactNode } from "react";

import { cn } from "@/shared/lib/utils";

import { PageContainer } from "./PageContainer";

interface AppShellProps {
  sidebar?: ReactNode;
  header?: ReactNode;
  children: ReactNode;
  contained?: boolean;
  mainClassName?: string;
}

export function AppShell({
  sidebar,
  header,
  children,
  contained = true,
  mainClassName,
}: AppShellProps) {
  return (
    <div className="flex h-dvh overflow-hidden bg-background text-foreground">
      {sidebar}
      <div className="flex min-h-0 flex-1 flex-col">
        {header}
        <main
          className={cn("min-h-0 flex-1 overflow-y-auto [scrollbar-gutter:stable]", mainClassName)}
        >
          {contained ? <PageContainer>{children}</PageContainer> : children}
        </main>
      </div>
    </div>
  );
}
