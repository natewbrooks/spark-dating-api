import React from "react";

export function SparkIcon({ className = "w-6 h-6" }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M13 2L5 13h5l-2 9 9-12h-5l1-10z" />
    </svg>
  );
}

export function ChatIcon({ className = "w-6 h-6" }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M6 6h12a3 3 0 0 1 3 3v4a3 3 0 0 1-3 3h-5.2L9 19.8V16H6a3 3 0 0 1-3-3V9a3 3 0 0 1 3-3z" />
    </svg>
  );
}

export function ProfileIcon({ className = "w-6 h-6" }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Head */}
      <circle cx="12" cy="8" r="3.2" />
      {/* body */}
      <path d="M6.2 18.5C7.2 15.8 9.3 14 12 14s4.8 1.8 5.8 4.5c.2.6-.2 1.5-1 1.5H7.2c-.8 0-1.3-.9-1-1.5z" />
    </svg>
  );
}

export function SettingsIcon({ className = "w-6 h-6" }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Outer gear shape */}
      <path d="M20 13.3v-2.6l-1.7-.4a6.5 6.5 0 0 0-.7-1.7l1-1.5-1.8-1.8-1.5 1a6.5 6.5 0 0 0-1.7-.7L13.3 4h-2.6l-.4 1.7a6.5 6.5 0 0 0-1.7.7l-1.5-1-1.8 1.8 1 1.5c-.3.5-.5 1.1-.7 1.7L4 10.7v2.6l1.7.4c.2.6.4 1.2.7 1.7l-1 1.5 1.8 1.8 1.5-1c.5.3 1.1.5 1.7.7l.4 1.7h2.6l.4-1.7c.6-.2 1.2-.4 1.7-.7l1.5 1 1.8-1.8-1-1.5c.3-.5.5-1.1.7-1.7l1.7-.4z" />
      {/* Inner hole */}
      <circle cx="12" cy="12" r="3.2" fill="black" />
    </svg>
  );
}
