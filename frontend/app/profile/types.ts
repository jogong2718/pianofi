export type SidebarSection = "profile" | "billing" | "settings";

export interface User {
  id: string;
  email?: string | undefined;
  user_metadata?: {
    first_name?: string;
    last_name?: string;
  };
}