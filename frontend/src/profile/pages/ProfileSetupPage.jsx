import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@contexts/AuthContext.jsx";

export default function ProfileSetupPage() {
  const navigate = useNavigate();
  const { fetchWithAuth, isAuthenticated } = useAuth();

  const [firstName, setFirstName]     = useState("");
  const [lastName, setLastName]       = useState("");
  const [birthdate, setBirthdate]     = useState("");
  const [gender, setGender]           = useState("");
  const [orientation, setOrientation] = useState("");

  const [genderOptions, setGenderOptions] = useState([]);
  const [orientationOptions, setOrientationOptions] = useState([]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving]   = useState(false);
  const [error, setError]     = useState("");

  // If not logged in → send back to phone auth
  useEffect(() => {
    if (!isAuthenticated) {
      navigate("/auth/phone");
    }
  }, [isAuthenticated, navigate]);

  // Load genders, orientations, and existing user info
  useEffect(() => {
    async function loadData() {
      if (!isAuthenticated) return;

      setLoading(true);
      try {
        // Load user info
        const resUser = await fetchWithAuth("/user/me");
        if (resUser.ok) {
          const data = await resUser.json();
          if (data.first_name) setFirstName(data.first_name);
          if (data.last_name)  setLastName(data.last_name);
          if (data.birthdate)  setBirthdate(data.birthdate);
          if (data.gender)     setGender(data.gender);
          if (data.orientation) setOrientation(data.orientation);
        }

        // Load gender options
        const resGender = await fetchWithAuth("/profile/genders");
        if (resGender.ok) {
          const genderData = await resGender.json();
          setGenderOptions(genderData);
        }

        // Load orientation options
        const resOrient = await fetchWithAuth("/profile/orientations");
        if (resOrient.ok) {
          const orientData = await resOrient.json();
          setOrientationOptions(orientData);
        }
      } catch (err) {
        console.error("Error loading onboarding data:", err);
        setError("Failed to load your info. Please try again.");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [fetchWithAuth, isAuthenticated]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (!firstName || !lastName || !birthdate || !gender || !orientation) {
      setError("Please fill out all fields.");
      return;
    }

    setSaving(true);
    try {
      const res = await fetchWithAuth("/user/me", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          first_name: firstName.trim(),
          last_name:  lastName.trim(),
          birthdate,
          gender,
          orientation,
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.message || "Failed to save your profile.");
        return;
      }

      navigate("/profile");
    } catch (err) {
      console.error(err);
      setError("Something went wrong.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen w-full flex items-center justify-center p-6">
        <p>Loading…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-6">
      <div className="w-full max-w-md space-y-6">
        {/* Back */}
        <button
          onClick={() => navigate("/auth/phone")}
          className="text-sm text-neutral-500 hover:text-neutral-800"
        >
          ← Back
        </button>

        <h1 className="text-3xl font-semibold mb-2">Welcome to Spark ✨</h1>
        <p className="text-neutral-600">
          Tell us a bit about you.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4" onChange={() => setError("")}>
          {/* First + Last */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">First name</label>
            <input
              type="text"
              className="w-full rounded-xl border border-neutral-300 px-3 py-2"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              disabled={saving}
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium">Last name</label>
            <input
              type="text"
              className="w-full rounded-xl border border-neutral-300 px-3 py-2"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              disabled={saving}
            />
          </div>

          {/* Birthdate */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">Birthdate</label>
            <input
              type="date"
              className="w-full rounded-xl border border-neutral-300 px-3 py-2"
              value={birthdate}
              onChange={(e) => setBirthdate(e.target.value)}
              disabled={saving}
            />
          </div>

          {/* Gender SELECT (dynamic) */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">Gender</label>
            <select
              className="w-full rounded-xl border border-neutral-300 px-3 py-2 bg-white"
              value={gender}
              onChange={(e) => setGender(e.target.value)}
              disabled={saving}
            >
              <option value="">Select your gender</option>
              {genderOptions.map((g) => (
                <option key={g.id ?? g.name} value={g.name}>
                  {g.name}
                </option>
              ))}
            </select>
          </div>

          {/* Orientation SELECT (dynamic) */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">Orientation</label>
            <select
              className="w-full rounded-xl border border-neutral-300 px-3 py-2 bg-white"
              value={orientation}
              onChange={(e) => setOrientation(e.target.value)}
              disabled={saving}
            >
              <option value="">Select your orientation</option>
              {orientationOptions.map((o) => (
                <option key={o.id ?? o.name} value={o.name}>
                  {o.name}
                </option>
              ))}
            </select>
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <button
            type="submit"
            className="w-full rounded-2xl px-6 py-3 bg-black text-white font-semibold"
            disabled={saving}
          >
            {saving ? "Saving…" : "Continue"}
          </button>
        </form>
      </div>
    </div>
  );
}
