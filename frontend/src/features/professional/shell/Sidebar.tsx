import {
  BarChart3,
  Briefcase,
  FileText,
  FolderGit2,
  Github,
  Heart,
  LayoutDashboard,
  Sparkles,
  Settings,
  UserCog,
} from "lucide-react";
import { NavLink } from "react-router-dom";

import { BrandWordmark } from "@/shared/ui/brand/BrandWordmark";
import { cn } from "@/shared/lib/utils";

const links = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/jobs", label: "Jobs", icon: Briefcase },
  { to: "/career-fitness", label: "Career Fitness", icon: Heart },
  { to: "/personas", label: "Personas", icon: UserCog },
  { to: "/sources", label: "Sources", icon: Sparkles },
  { to: "/portfolio", label: "Portfolio", icon: FolderGit2 },
  { to: "/repositories", label: "Repositories", icon: Github },
  { to: "/resumes", label: "Resumes", icon: FileText },
  { to: "/applications", label: "Applications", icon: BarChart3 },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="hidden w-60 shrink-0 border-r bg-card md:flex md:flex-col">
      <div className="flex h-14 items-center px-6">
        <BrandWordmark variant="careero" size={22} />
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {links.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:bg-accent/50 hover:text-foreground",
              )
            }
          >
            <Icon className="h-4 w-4" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="border-t px-6 py-3 text-xs text-muted-foreground">v0.1.0 · Phase 1</div>
    </aside>
  );
}
