import React from "react";
import { useNavigate } from "react-router-dom";

export default function SignUpLanding() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen w-full text-white flex items-center justify-center p-6">
      <div className="w-full max-w-sm text-center">
        {/* Logo */}
        <div className="flex items-center justify-center mb-10">
          <img
            src="/spark-logo-gold.svg"
            alt="Spark logo"
            className="h-40 w-40"
          />
        </div>

        {/* Heading */}
        <h1 className="text-xl font-medium tracking-tight mb-8 text-neutral-200">
          Sign up to continue
        </h1>

        {/* Primary CTA */}
        <button
          onClick={() => navigate("/auth/phone")}
          className="w-full rounded-2xl px-6 py-4 bg-white text-base font-semibold text-black transition-colors shadow-md hover:bg-neutral-200"
        >
          Use phone number
        </button>

        <div className="h-8" />
      </div>
    </div>
  );
}
