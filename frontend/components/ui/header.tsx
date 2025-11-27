"use client";

import Link from "next/link";
import React, { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Menu, Music } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useIsMobile } from "@/hooks/use-mobile";
import { ThemeToggle } from "@/components/theme-toggle";

export function Header() {
  const router = useRouter();
  const pathname = usePathname();
  const isMobile = useIsMobile();
  const [isRedirecting, setIsRedirecting] = useState(false);

  const handleNavigation = (path: string) => {
    if (pathname === path) return;
    setIsRedirecting(true);
    router.push(path);
  };

  useEffect(() => {
    if (isRedirecting) setIsRedirecting(false);
  }, [pathname]);

  useEffect(() => {
    if (!isRedirecting) return;
    const prev = document.documentElement.style.overflow;
    document.documentElement.style.overflow = "hidden";
    return () => {
      document.documentElement.style.overflow = prev || "";
    };
  }, [isRedirecting]);

  if (isRedirecting) {
    return (
      <div className="fixed inset-0 z-[9999] bg-background flex items-center justify-center">
        <div className="text-center">
          <Music className="h-12 w-12 text-primary mx-auto mb-4 animate-spin" />
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  const navigationItems = [
    { href: "/#features", label: "Features" },
    // { href: "/#pricing", label: "Pricing" },
    { href: "/contact", label: "Contact" },
  ];

  return (
    <header className="sticky top-0 left-0 right-0 z-50 px-4 lg:px-6 h-20 flex items-center bg-white/40 dark:bg-black/40 backdrop-blur-md">
      <Link className="flex items-center justify-center space-x-4" href="/">
        <Music className="h-12 w-12 text-primary" />
        <span className="font-bold text-3xl">PianoFi</span>
      </Link>

      {isMobile ? (
        <div className="ml-auto flex items-center gap-2">
          <ThemeToggle />
          <Button
            variant="ghost"
            size="lg"
            className="border border-black text-black hover:bg-black/10 hover:text-black dark:border-white dark:text-white dark:hover:bg-white/10"
            onClick={() => handleNavigation("/login")}
          >
            Login
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="lg">
                <Menu className="h-6 w-6" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {navigationItems.map((item) => (
                <DropdownMenuItem key={item.href} asChild>
                  <Link href={item.href}>{item.label}</Link>
                </DropdownMenuItem>
              ))}
              <DropdownMenuItem onClick={() => handleNavigation("/signup")}>
                Sign Up
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      ) : (
        <>
          <nav className="ml-auto flex items-center gap-4 sm:gap-6">
            {navigationItems.map((item) => (
              <Link
                key={item.href}
                className="text-lg font-medium leading-none hover:underline underline-offset-4"
                href={item.href}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="flex items-center gap-3 ml-4">
            <ThemeToggle />
            <Button
              variant="ghost"
              size="lg"
              className="border border-black text-black hover:bg-black/10 hover:text-black dark:border-white dark:text-white dark:hover:bg-white/10"
              onClick={() => handleNavigation("/login")}
            >
              Login
            </Button>
            <Button size="lg" onClick={() => handleNavigation("/signup")}>
              Sign Up
            </Button>
          </div>
        </>
      )}
    </header>
  );
}
