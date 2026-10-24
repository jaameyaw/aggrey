import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Aggrey",
  description:
    "Text Aggrey to find out what's being served at the caf and when, without downloading an app.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
