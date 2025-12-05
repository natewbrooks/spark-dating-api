import React from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  SparkIcon,
  ChatIcon,
  ProfileIcon,
  SettingsIcon,
} from "../auth/components/NavIcons.jsx";

export default function AuthedAppLayout() {
  return (
    <div className="min-h-screen w-full flex flex-col text-white">
      {/* Top bar (logo) */}
      <header className="h-14 flex items-center px-4 border-b border-neutral-800">
        <img src="/spark.svg" alt="Spark logo" className="h-16 w-16" />
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>

      {/* Bottom nav */}
      <div className="border-t border-neutral-800 bg-black"></div>
      <nav className="h-14 border-top border-neutral-800 flex items-center justify-around">
        <BottomNavLink to="/spark">
          <SparkIcon />
        </BottomNavLink>
        <BottomNavLink to="/chats">
          <ChatIcon />
        </BottomNavLink>
        <BottomNavLink to="/profile">
          <ProfileIcon />
        </BottomNavLink>
        <BottomNavLink to="/settings">
          <SettingsIcon />
        </BottomNavLink>
      </nav>
    </div>
  );
}

function BottomNavLink({ to, label, children }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        [
          "flex flex-col items-center justify-center text-xs gap-0.5",
          isActive ? "text-amber-400" : "text-neutral-400",
        ].join(" ")
      }
    >
      {children}
      <span>{label}</span>
    </NavLink>
  );
}
