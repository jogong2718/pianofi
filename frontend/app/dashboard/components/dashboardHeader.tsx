import { FC } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Music, User, LogOut, Sparkles } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Alert, AlertDescription } from "@/components/ui/alert";


interface DashboardHeaderProps {
  user: any;
  onLogout: () => void;
  onUpgradeClick: () => void;
}

const DashboardHeader: FC<DashboardHeaderProps> = ({
  user,
  onLogout,
  onUpgradeClick,
}) => {
  const router = useRouter();

  return (
    <>
    {/* Announcement Banner */}
      <Alert className="rounded-none border-x-0 border-t-0 bg-gradient-to-r from-purple-500/15 to-blue-500/15 dark:from-purple-500/20 dark:to-blue-500/20">
        <div className="flex items-center justify-center gap-2 w-full">
          <span>We're currently building our next generation of bigger and better models — stay tuned!</span>
          <span className="sr-only">Announcement: building next-generation models</span>
        </div>
      </Alert>
    <header className="border-b">
      <div className="flex h-16 items-center px-4 lg:px-6">
        <div className="flex items-center space-x-4">
          <Music className="h-8 w-8 text-primary" />
          <span className="text-2xl font-bold">PianoFi</span>
        </div>

        <div className="ml-auto flex items-center space-x-4">
          <ThemeToggle />
          {/* <Button variant="default" size="sm" onClick={onUpgradeClick}>
            Upgrade
          </Button> */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                <Avatar className="h-8 w-8">
                  <AvatarImage
                    src="/middlegura.svg?height=32&width=32"
                    alt="User"
                  />
                  <AvatarFallback>
                    {user?.user_metadata?.first_name?.[0] ||
                      user?.email?.[0] ||
                      "U"}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" forceMount>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">
                    {user?.user_metadata?.first_name &&
                    user?.user_metadata?.last_name
                      ? `${user.user_metadata.first_name} ${user.user_metadata.last_name}`
                      : user?.email}
                  </p>
                  <p className="text-xs leading-none text-muted-foreground">
                    {user?.email}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => router.push("/profile")}>
                <User className="mr-2 h-4 w-4" />
                <span>Profile</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={onLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                <span>Log out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
    </>
  );
};

export default DashboardHeader;
