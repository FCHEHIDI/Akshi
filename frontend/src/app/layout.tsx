import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ReactQueryProvider } from "@/components/providers/ReactQueryProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Akshi", template: "%s · Akshi" },
  description: "Akshi — the eye that never closes. B2B observability, incident management & alerting.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${GeistSans.variable} ${GeistMono.variable} h-full antialiased`}
    >
      <body className="h-full bg-background text-foreground">
        <ReactQueryProvider>
          <TooltipProvider>{children}</TooltipProvider>
        </ReactQueryProvider>
      </body>
    </html>
  );
}
      