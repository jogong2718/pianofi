"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { User as UserIcon } from "lucide-react";
import { toast } from "sonner";
import { User } from "../types";

import { useUpdateProfile } from "@/hooks/useUpdateProfile";

interface ProfileSectionProps {
  user: User;
}

export function ProfileSection({ user }: ProfileSectionProps) {
  const [saving, setSaving] = useState(false);

  const {
    callUploadProfile,
    loading: loadingUploadUrl,
    error: uploadUrlError,
  } = useUpdateProfile();

  const handleSave = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSaving(true);

    const firstName = (e.currentTarget.firstName as HTMLInputElement).value;
    const lastName = (e.currentTarget.lastName as HTMLInputElement).value;

    if (!firstName || !lastName) {
      toast.error("Please fill in all fields.");
      setSaving(false);
      return;
    }

    const {
      success,
      message,
      user: updatedUser,
    } = await callUploadProfile({
      first_name: firstName,
      last_name: lastName,
    });

    if (!success) {
      toast.error(message || "Failed to update profile.");
      setSaving(false);
      return;
    }

    toast.success("Profile updated successfully!");
    setSaving(false);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <UserIcon className="h-5 w-5" />
          Personal Information
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSave} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="firstName">First Name</Label>
              <Input
                id="firstName"
                defaultValue={user?.user_metadata?.first_name || ""}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="lastName">Last Name</Label>
              <Input
                id="lastName"
                defaultValue={user?.user_metadata?.last_name || ""}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={user?.email || ""}
              disabled
              className="bg-muted"
            />
            <p className="text-xs text-muted-foreground">
              Email cannot be changed. Contact support if needed.
            </p>
          </div>

          <Button type="submit" disabled={saving}>
            {saving ? "Saving..." : "Save Changes"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
