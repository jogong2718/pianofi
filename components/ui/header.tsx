import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Music } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";

interface HeaderProps {
  showNavigation?: boolean;
  showAuthButtons?: boolean;
}

export function Header({
  showNavigation = true,
  showAuthButtons = true,
}: HeaderProps) {
  return (
    <div className="fixed w-full z-20 bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg">
      <header className="px-4 lg:px-6 h-16 flex items-center border-b">
        <Link href="/" className="flex items-center justify-center">
          <Music className="h-8 w-8 text-primary" />
          <span className="ml-2 text-2xl font-bold">PianoFi</span>
        </Link>

        {showNavigation && (
          <nav className="ml-auto flex gap-4 sm:gap-6">
            <Link
              href="#features"
              className="text-sm font-medium hover:underline underline-offset-4"
            >
              Features
            </Link>
            <Link
              href="#pricing"
              className="text-sm font-medium hover:underline underline-offset-4"
            >
              Pricing
            </Link>
            <Link
              href="#about"
              className="text-sm font-medium hover:underline underline-offset-4"
            >
              About
            </Link>
          </nav>
        )}

        <div
          className={`${
            showNavigation ? "ml-6" : "ml-auto"
          } flex gap-2 items-center`}
        >
          <ThemeToggle />
          {showAuthButtons && (
            <>
              <Button variant="ghost" asChild>
                <Link href="/login">Login</Link>
              </Button>
              <Button asChild>
                <Link href="/signup">Sign Up</Link>
              </Button>
            </>
          )}
        </div>
      </header>
    </div>
  );
}
