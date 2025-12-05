import React from "react";

export default function SettingsPage() {
  return (
    <div className="h-full w-full px-4 py-3 space-y-6">
      <h1 className="text-2xl font-semibold mb-2">Settings</h1>

      {/* Preferences */}
      <section className="space-y-2">
        <h2 className="text-sm font-semibold text-neutral-300">
          Match preferences
        </h2>
        <div className="rounded-2xl bg-neutral-900 px-3 py-3 text-sm space-y-2">
          <button className="w-full text-left hover:text-amber-400"
          style={{ color: 'white'}}>
            Edit age range
          </button>
          <button className="w-full text-left hover:text-amber-400"
          style={{ color: 'white'}}>
            Edit distance
          </button>
          <button className="w-full text-left hover:text-amber-400"
          style={{ color: 'white'}}>
            Edit gender/orientation preferences
          </button>
        </div>
      </section>

      {/* Account controls */}
      <section className="space-y-2">
        <h2 className="text-sm font-semibold text-neutral-300">
          Account
        </h2>
        <div className="rounded-2xl bg-neutral-900 px-3 py-3 text-sm space-y-2">
          <button className="w-full text-left hover:text-amber-400"
          style={{ color: 'white'}}>
            Pause account
          </button>
          <button className="w-full text-left hover:text-amber-400"
          style={{ color: 'white'}}>
            Notification settings
          </button>
          <button className="w-full text-left text-red-400 hover:text-red-300"
          style={{ color: 'white'}}>
            Delete account
          </button>
        </div>
      </section>
    </div>
  );
}
