"use client";

import { User, CreditCard, Settings } from "lucide-react";
import { cn } from "@/lib/utils";
import { SidebarSection } from "../types";

interface ProfileSidebarProps {
  activeSection: SidebarSection;
  onSectionChange: (section: SidebarSection) => void;
}

export function ProfileSidebar({
  activeSection,
  onSectionChange,
}: ProfileSidebarProps) {
  const sidebarItems = [
    {
      id: "profile" as SidebarSection,
      label: "Profile",
      icon: User,
      description: "Personal information and account details",
    },
    // {
    //   id: "billing" as SidebarSection,
    //   label: "Billing",
    //   icon: CreditCard,
    //   description: "Subscription and payment management",
    // },
    {
      id: "settings" as SidebarSection,
      label: "Settings",
      icon: Settings,
      description: "App preferences and notifications",
    },
  ];

  return (
    <aside className="w-64 border-r min-h-[calc(100vh-4rem)] bg-muted/30">
      <nav className="p-4 space-y-2">
        {sidebarItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => onSectionChange(item.id)}
              className={cn(
                "w-full flex items-start gap-3 p-3 rounded-lg text-left transition-colors",
                activeSection === item.id
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-muted"
              )}
            >
              <Icon className="h-5 w-5 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium">{item.label}</p>
                <p
                  className={cn(
                    "text-xs mt-1",
                    activeSection === item.id
                      ? "text-primary-foreground/80"
                      : "text-muted-foreground"
                  )}
                >
                  {item.description}
                </p>
              </div>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
