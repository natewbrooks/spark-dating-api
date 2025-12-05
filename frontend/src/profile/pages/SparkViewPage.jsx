import React from "react";

export default function SparkViewPage() {
  // Later these will trigger API calls to create/join sessions
  function handleNormalMode() {
    console.log("TODO: start normal Spark session");
    alert("Normal mode coming soon ✨");
  }

  function handleSpeedDatingMode() {
    console.log("TODO: start speed-dating session");
    alert("Speed dating mode coming soon ⚡");
  }

  return (
    <div className="h-full w-full flex items-center justify-center px-6">
      <div className="w-full max-w-md space-y-6">
        <h1 className="text-2xl font-semibold">Choose your Spark</h1>
        <p className="text-sm text-neutral-400">
          Pick how you want to meet people today.
        </p>

        <div className="space-y-4 mt-4">
          {/* Normal mode card */}
          <button
            onClick={handleNormalMode}
            className="w-full text-left rounded-2xl border border-neutral-700 px-4 py-4 hover:border-amber-400 transition"
          >
            <h2 className="text-lg font-semibold text-white">Normal mode</h2>
            <p className="text-sm text-neutral-400">
              Join a room, get matched, and chat
              without the rush.
            </p>
          </button>

          {/* Speed dating card */}
          <button
            onClick={handleSpeedDatingMode}
            className="w-full text-left rounded-2xl border border-neutral-700 px-4 py-4 hover:border-amber-400 transition"
          >
            <h2 className="text-lg font-semibold text-white">Speed dating mode</h2>
            <p className="text-sm text-neutral-400">
              Short timed sessions to see
              where the sparks fly.
            </p>
          </button>
        </div>
      </div>
    </div>
  );
}
