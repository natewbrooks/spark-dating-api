import React, { useEffect, useState } from "react";
import { useAuth } from "@contexts/AuthContext.jsx";

export default function ProfilePage() {
  const { fetchWithAuth, isAuthenticated } = useAuth();
  const [me, setMe] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadUser() {
      if (!isAuthenticated) {
        setLoading(false);
        return;
      }
      try {
        const res = await fetchWithAuth("/user/me");
        if (!res.ok) {
          console.error("Failed to load /user/me in /profile", res.status);
          setLoading(false);
          return;
        }
        const data = await res.json();
        setMe(data);
      } catch (err) {
        console.error("Error loading /user/me in /profile", err);
      } finally {
        setLoading(false);
      }
    }

    loadUser();
  }, [fetchWithAuth, isAuthenticated]);

  if (loading) {
    return (
      <div className="min-h-screen w-full flex items-center justify-center text-black">
        <p>Loading your profile…</p>
      </div>
    );
  }

  if (!me) {
    return (
      <div className="min-h-screen w-full flex items-center justify-center">
        <p>Could not load your profile.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center text-black p-6">
      <div className="w-full max-w-md space-y-4">
        <h1 className="text-3xl font-semibold">Your Profile</h1>
        <p className="text-neutral-700">
          This is where you’ll finish setting up your account (photos, bio, preferences, etc.).
        </p>

        <div className="rounded-xl border border-neutral-200 p-4 bg-neutral-50 space-y-2">
          <p><strong>Name:</strong> {me.first_name} {me.last_name}</p>
          <p><strong>Phone:</strong> {me.phone_number || "unknown"}</p>
          {/* Add more fields later */}
        </div>
      </div>
    </div>
  );
}
