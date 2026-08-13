import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ahara",
  description: "Food that fits your moment.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
