"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { CloseIcon, FolderIcon, GridIcon, LayersIcon, UploadIcon } from "@/components/icons";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: GridIcon },
  { href: "/upload", label: "Upload Document", icon: UploadIcon },
  { href: "/records", label: "Land Records", icon: FolderIcon },
];

interface SidebarProps {
  mobileOpen: boolean;
  onClose: () => void;
}

function isActive(pathname: string, href: string) {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(href + "/");
}

function SidebarContent({ pathname, onNavigate }: { pathname: string; onNavigate?: () => void }) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex h-16 shrink-0 items-center gap-2.5 border-b border-border px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-brand-600 text-white">
          <LayersIcon className="h-[18px] w-[18px]" />
        </div>
        <div className="leading-tight">
          <p className="text-sm font-semibold text-ink-900">LandRecord</p>
          <p className="text-[11px] text-ink-300">Digital Registry</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto p-3 thin-scroll" aria-label="Primary">
        {NAV_ITEMS.map((item) => {
          const active = isActive(pathname, item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              aria-current={active ? "page" : undefined}
              className={`flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors ${
                active
                  ? "bg-brand-50 font-medium text-brand-700"
                  : "text-ink-500 hover:bg-canvas hover:text-ink-900"
              }`}
            >
              <Icon className="h-[18px] w-[18px] shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-border p-4">
        <p className="text-xs leading-relaxed text-ink-300">
          Intelligent Land Record Digitization &mdash; MVP frontend
        </p>
      </div>
    </div>
  );
}

export default function Sidebar({ mobileOpen, onClose }: SidebarProps) {
  const pathname = usePathname();

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden w-60 shrink-0 border-r border-border bg-surface lg:block">
        <SidebarContent pathname={pathname} />
      </aside>

      {/* Mobile drawer */}
      <div
        className={`fixed inset-0 z-40 lg:hidden ${mobileOpen ? "" : "pointer-events-none"}`}
        aria-hidden={!mobileOpen}
      >
        <div
          onClick={onClose}
          className={`absolute inset-0 bg-ink-900/40 transition-opacity ${
            mobileOpen ? "opacity-100" : "opacity-0"
          }`}
        />
        <div
          className={`absolute inset-y-0 left-0 w-72 max-w-[80vw] bg-surface shadow-raised transition-transform duration-200 ${
            mobileOpen ? "translate-x-0" : "-translate-x-full"
          }`}
          role="dialog"
          aria-modal="true"
          aria-label="Navigation menu"
        >
          <button
            onClick={onClose}
            aria-label="Close menu"
            className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-md text-ink-500 hover:bg-canvas"
          >
            <CloseIcon className="h-5 w-5" />
          </button>
          <SidebarContent pathname={pathname} onNavigate={onClose} />
        </div>
      </div>
    </>
  );
}
