'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import type { User } from '@supabase/supabase-js';
import { LayoutDashboard, Repeat, BarChart3, LogIn, Sun, Moon, SunMoon } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useTheme } from 'next-themes';
import { Button } from '@/components/ui/button';
import Image from 'next/image';
import { cn } from '@/lib/utils';

interface NavItem {
  href: string;
  label: string;
  icon: React.ElementType;
}

const navItems: NavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/trading', label: 'Trading', icon: Repeat },
  { href: '/strategy', label: 'Strategy', icon: BarChart3 },
];

export default function Sidebar({ className }: { className?: string }) {
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  useEffect(() => {
    const getSession = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      setUser(session?.user ?? null);
      setLoading(false);
    };

    getSession();

    const { data: authListenerData } = supabase.auth.onAuthStateChange(async (event, session) => {
      setUser(session?.user ?? null);
      setLoading(false);
    });

    return () => {
      authListenerData?.subscription?.unsubscribe();
    };
  }, []);

  const handleLogin = async () => {
    // Redirect to a login page or open a Supabase auth modal
    // For now, let's assume a redirect to a /login page
    // Or use Supabase UI for a quick modal:
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google', // or any other provider
      // options: { redirectTo: window.location.origin } // redirect back after login
    });
    if (error) console.error('Error logging in:', error.message);
  };

  const handleLogout = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) console.error('Error logging out:', error.message);
    // setUser(null); // Auth listener should handle this
  };
  
  // Placeholder for user name and avatar - adapt based on your Supabase user profile structure
  const userName = user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'User';
  const userAvatarUrl = user?.user_metadata?.avatar_url;

  if (!mounted) {
    // Avoid rendering theme-dependent UI until client is mounted
    // You can return a placeholder or null here if preferred
    return null; 
  }

  return (
    <aside className={cn(
      "w-32 h-screen bg-background dark:bg-background text-foreground flex flex-col fixed top-0 left-0 z-40 border-r border-border",
      className
    )}>
      {/* Logo and Name */}
      <div className="p-4 border-b border-border flex flex-col items-center space-y-2">
        <Image src="/logo.png" alt="Alpha Seek Logo" width={32} height={32} className="w-8 h-8 flex-shrink-0" />
        <h1 className="font-brand text-base leading-tight text-center text-foreground font-[800] italic">
          AlphaSeek
        </h1>
      </div>

      {/* Navigation */}
      <nav className="flex-grow p-2 space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.label}
            href={item.href}
            className={`flex flex-col items-center justify-center text-center space-y-1 p-2 rounded-lg transition-colors h-20 font-brand ${pathname === item.href 
                          ? 'bg-primary text-primary-foreground dark:bg-primary dark:text-primary-foreground font-medium' 
                          : 'hover:bg-accent hover:text-accent-foreground dark:hover:bg-accent dark:hover:text-accent-foreground'}`}
          >
            <item.icon size={20} />
            <span className="text-sm">{item.label}</span>
          </Link>
        ))}
      </nav>

      {/* Theme Toggle Buttons */}
      {mounted && (
        <div className="p-2 border-b border-border">
          <div className="flex justify-around items-center">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme('light')}
              className={`h-8 w-8 rounded-full font-brand ${theme === 'light' ? 'bg-accent dark:bg-accent' : ''} text-muted-foreground hover:bg-accent dark:hover:bg-accent`}
              title="Light Mode"
            >
              <Sun size={18} />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme('dark')}
              className={`h-8 w-8 rounded-full font-brand ${theme === 'dark' ? 'bg-accent dark:bg-accent' : ''} text-muted-foreground hover:bg-accent dark:hover:bg-accent`}
              title="Dark Mode"
            >
              <Moon size={18} />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme('system')}
              className={`h-8 w-8 rounded-full font-brand ${theme === 'system' ? 'bg-accent dark:bg-accent' : ''} text-muted-foreground hover:bg-accent dark:hover:bg-accent`}
              title="System Default"
            >
              <SunMoon size={18} />
            </Button>
          </div>
        </div>
      )}

      {/* User Section */}
      <div className="p-2">
        {loading ? (
          <div className="h-20 w-full bg-muted dark:bg-muted animate-pulse rounded-md"></div>
        ) : user ? (
          <div className="flex flex-col items-center space-y-2">
            <Avatar className="h-10 w-10 border-2 border-border">
              <AvatarImage src={userAvatarUrl} alt={userName} />
              <AvatarFallback className="bg-muted text-muted-foreground dark:bg-muted dark:text-muted-foreground font-brand">
                {userName.substring(0, 1).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <button 
              onClick={handleLogout} 
              className="text-xs text-muted-foreground hover:text-primary dark:hover:text-primary transition-colors w-full text-center py-1 rounded hover:bg-accent dark:hover:bg-accent font-brand"
            >
              Log Out
            </button>
          </div>
        ) : (
          <button
            onClick={handleLogin}
            className="w-full flex flex-col items-center justify-center space-y-1 p-2 rounded-lg font-medium transition-colors h-20 
                       text-foreground font-brand
                       hover:bg-accent dark:hover:bg-accent"
          >
            <LogIn size={20} />
            <span className="text-xs">Log In</span>
          </button>
        )}
      </div>
    </aside>
  );
} 