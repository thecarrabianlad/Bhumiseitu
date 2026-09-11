"use client";

import { usePathname } from "next/navigation";
import { MenuIcon, UserIcon } from "@/components/icons";

const PAGE_TITLES: { match: (path: string) => boolean; title: string; subtitle: string }[] = [
  { match: (p) => p === "/", title: "Dashboard", subtitle: "Overview of land record digitization" },
  { match: (p) => p === "/upload", title: "Upload Document", subtitle: "Add a new record document for processing" },
  { match: (p) => p === "/records", title: "Land Records", subtitle: "Search and manage digitized records" },
  { match: (p) => p.startsWith("/records/"), title: "Record Detail", subtitle: "Official land record" },
];

function getPageMeta(pathname: string) {
  return (
    PAGE_TITLES.find((entry) => entry.match(pathname)) ?? {
      title: "LandRecord",
      subtitle: "",
    }
  );
}

interface HeaderProps {
  onMenuClick: () => void;
}

export default function Header({ onMenuClick }: HeaderProps) {
  const pathname = usePathname();
  const { title, subtitle } = getPageMeta(pathname);

  return (
    <header className="flex h-16 shrink-0 items-center justify-between gap-4 border-b border-border bg-surface px-4 sm:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <button
          onClick={onMenuClick}
          aria-label="Open menu"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md text-ink-500 hover:bg-canvas lg:hidden"
        >
          <MenuIcon className="h-5 w-5" />
        </button>
        <div className="min-w-0">
          <h1 className="truncate text-base font-semibold text-ink-900">{title}</h1>
          {subtitle && <p className="hidden truncate text-xs text-ink-300 sm:block">{subtitle}</p>}
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-3">
        <div className="hidden text-right sm:block">
          <p className="text-sm font-medium leading-tight text-ink-900">Anjali Kulkarni</p>
          <p className="text-xs leading-tight text-ink-300">Revenue Dept. Admin</p>
        </div>
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-100 text-brand-700">
          <UserIcon className="h-[18px] w-[18px]" />
        </div>
      </div>
    </header>
  );
}
