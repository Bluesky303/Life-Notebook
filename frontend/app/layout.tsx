import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Life Notebook",
  description: "Personal AI-managed life notebook"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
