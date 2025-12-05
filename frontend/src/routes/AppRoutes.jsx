import React from "react";
import { Routes, Route } from "react-router-dom";

import SignUpLanding from "../auth/pages/SignUpLanding";
import PhoneAuthPage from "../auth/pages/PhoneOtpPage";
import ProfileSetupPage from "../profile/pages/ProfileSetupPage";
import ProfilePage from "../profile/pages/ProfilePage";

import AuthedAppLayout from "../layouts/AuthedAppLayout";
import SparkViewPage from "../profile/pages/SparkViewPage";
import ChatListPage from "../profile/pages/ChatListPage";
import SettingsPage from "../profile/pages/SettingsPage";

// Dev only pages
import DevOnboardingPreview from "../profile/pages/DevOnboardingPreview";

export default function AppRoutes() {
  return (
    <Routes>
      {/* Public / auth flow */}
      <Route path="/" element={<SignUpLanding />} />
      <Route path="/auth/phone" element={<PhoneAuthPage />} />
      <Route path="/onboarding" element={<ProfileSetupPage />} />

      {/* Authed app shell with bottom nav */}
      <Route element={<AuthedAppLayout />}>
        <Route path="/spark" element={<SparkViewPage />} />
        <Route path="/chats" element={<ChatListPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>

      {/* Dev only routes */}
      <Route path="/dev/onboarding" element={<DevOnboardingPreview />} />
    </Routes>
  );
}
