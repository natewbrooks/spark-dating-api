import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function DevOnboardingPreview() {
  const navigate = useNavigate();

  const [firstName, setFirstName]     = useState("");
  const [lastName, setLastName]       = useState("");
  const [birthdate, setBirthdate]     = useState("");
  const [gender, setGender]           = useState("");
  const [orientation, setOrientation] = useState("");
  const [error, setError]             = useState("");

  // For preview, hardcode some orientation options
  const orientationOptions = [
    "straight",
    "gay",
    "lesbian",
    "bisexual",
    "pansexual",
    "queer",
    "asexual",
    "demisexual",
    "questioning",
  ];

  function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (!firstName || !lastName || !birthdate || !gender || !orientation) {
      setError("Please fill out all fields.");
      return;
    }

    // Just log for now so you can see it's working
    console.log("DEV SUBMIT:", {
      firstName,
      lastName,
      birthdate,
      gender,
      orientation,
    });

    alert("Dev submit OK! Check console for values.");
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-6">
      <div className="w-full max-w-md space-y-6">
        {/* Back to landing just for preview */}
        <button
          type="button"
          className="text-sm text-neutral-500 hover:text-neutral-800"
          onClick={() => navigate("/")}
        >
          ← Back
        </button>

        <h1 className="text-3xl font-semibold mb-2">Welcome to Spark ✨</h1>
        <p className="text-neutral-600">
          DEV PREVIEW ONLY
        </p>

        <form
          onSubmit={handleSubmit}
          onChange={() => setError("")}
          className="space-y-4"
        >
          {/* First name */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">
              First name
            </label>
            <input
              type="text"
              className="w-full rounded-xl border border-neutral-300 px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-black"
              placeholder="e.g. John"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
            />
          </div>

          {/* Last name */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">
              Last name
            </label>
            <input
              type="text"
              className="w-full rounded-xl border border-neutral-300 px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-black"
              placeholder="e.g. Doe"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
            />
          </div>

          {/* Birthday */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">
              Birthday
            </label>
            <input
              type="date"
              className="w-full rounded-xl border border-neutral-300 px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-black"
              value={birthdate}
              onChange={(e) => setBirthdate(e.target.value)}
            />
          </div>

          {/* Gender */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">
              Gender
            </label>
            <select
              className="w-full rounded-xl border border-neutral-300 px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-black bg-white text-black"
              value={gender}
              onChange={(e) => setGender(e.target.value)}
            >
              <option value="">Select your gender</option>
              <option value="man">Man</option>
              <option value="woman">Woman</option>
              <option value="non_binary">Non-binary</option>
              <option value="other">Other</option>
              <option value="prefer_not_say">Prefer not to say</option>
            </select>
          </div>

          {/* Orientation */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">
              Orientation
            </label>
            <select
              className="w-full rounded-xl border border-neutral-300 px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-black bg-white text-black"
              value={orientation}
              onChange={(e) => setOrientation(e.target.value)}
            >
              <option value="">Select your orientation</option>
              {orientationOptions.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </div>

          {error && (
            <p className="text-sm text-red-500">
              {error}
            </p>
          )}

          <button
            type="submit"
            className="w-full mt-4 rounded-2xl px-6 py-3 bg-black font-semibold"
            style={{ color: 'white'}}
          >
            Continue
          </button>
        </form>
      </div>
    </div>
  );
}
