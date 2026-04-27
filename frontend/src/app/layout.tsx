import type { Metadata } from "next";
import { IBM_Plex_Sans, Orbitron } from "next/font/google";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ReactQueryProvider } from "@/components/providers/ReactQueryProvider";
import "./globals.css";

const ibmPlexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-ibm",
  display: "swap",
});

const orbitron = Orbitron({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "900"],
  variable: "--font-orbitron",
  display: "swap",
});

export const metadata: Metadata = {
  title: { default: "Akshi", template: "%s · Akshi" },
  description: "Akshi — The Eye That Sees Systems. Observability beyond vision.",
  icons: { icon: "/favicon_akshi.png" },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${ibmPlexSans.variable} ${orbitron.variable} h-full antialiased`}
    >
      <body className="h-full bg-background text-foreground font-[var(--font-ibm)]">
        <ReactQueryProvider>
          <TooltipProvider>{children}</TooltipProvider>
        </ReactQueryProvider>
      </body>
    </html>
  );
}
      