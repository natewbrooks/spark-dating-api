import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import TitleBarComponent from "../components/TitleBarComponent";
import PhoneAuthFormComponent from "../components/PhoneAuthFormComponent";
import { useAuth } from "@contexts/AuthContext.jsx";

export default function PhoneOtpPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/onboarding");
    }
  }, [isAuthenticated, navigate]);

  return (
    <section className="flex flex-col w-full min-h-screen text-white">
      <header className="p-4">
        <TitleBarComponent />
      </header>
      <main className="flex w-full justify-center p-4">
        <PhoneAuthFormComponent />
      </main>
      <footer className="h-8" />
    </section>
  );
}