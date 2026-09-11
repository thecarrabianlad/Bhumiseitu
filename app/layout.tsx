import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "@/app/globals.css";
import AppShell from "@/components/AppShell";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "LandRecord — Digital Land Record Registry",
  description:
    "Intelligent Land Record Digitization MVP — search, verify, and manage digitized land records.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="font-sans text-ink-900 antialiased">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
