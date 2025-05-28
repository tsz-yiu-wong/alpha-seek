import type { Metadata } from "next";
import { Space_Grotesk, IBM_Plex_Mono } from "next/font/google";
import localFont from 'next/font/local';
import "./globals.css";
import { cn } from "@/lib/utils";
import Sidebar from "@/components/layout/sidebar";
import { ThemeProvider } from "next-themes";
import { StagewiseToolbar } from '@stagewise/toolbar-next';

// 品牌字体（侧边栏、Logo）
const mapleMono = localFont({
  src: [
    {
      path: '../../public/fonts/MapleMono-Woff2/MapleMono-Bold.woff2',
      weight: '700',
      style: 'normal',
    },
    {
      path: '../../public/fonts/MapleMono-Woff2/MapleMono-ExtraBoldItalic.woff2',
      weight: '800',
      style: 'italic',
    },
  ],
  variable: '--font-maple-mono',
  display: 'swap',
});

// UI 界面字体
const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  variable: "--font-space-grotesk",
});

// 数据展示字体
const ibmPlexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-ibm-plex-mono",
});

export const metadata: Metadata = {
  title: "Alpha Seek",
  description: "AI Agent for DeFi",
};

const stagewiseConfig = {
  plugins: []
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={cn(
          "min-h-screen bg-background antialiased",
          mapleMono.variable,
          spaceGrotesk.variable,
          ibmPlexMono.variable
        )}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <div className="flex min-h-screen">
            <Sidebar className="font-brand" />
            <div className="flex-1 flex flex-col ml-32 font-heading">
              {/* Header Removed */}
              {/* Main Content */}
              <main className="flex-1 py-4 md:py-6 lg:py-8">
                {children}
              </main>
              {/* Footer */}
              <footer className="py-6 md:px-8 md:py-0">
                <div className="container flex flex-col items-center justify-between gap-4 md:h-24 md:flex-row">
                  <p className="text-center text-sm leading-loose text-muted-foreground md:text-left">
                    Built by Alpha Seek Team.
                  </p>
                </div>
              </footer>
            </div>
          </div>
        </ThemeProvider>
        {process.env.NODE_ENV === 'development' && (
          <StagewiseToolbar config={stagewiseConfig} />
        )}
      </body>
    </html>
  );
}
