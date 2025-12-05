import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

/**
 * AuthContext
 * - Manages phone-based OTP auth flow
 * - Persists auth session
 * - Exposes a fetch helper that injects the Bearer token
 *
 * Usage:
 *   <AuthProvider>
 *     <App />
 *   </AuthProvider>
 *
 *   const { isAuthenticated, user, session, requestOtp, verifyOtp, fetchWithAuth, signOut } = useAuth();
 */

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [session, setSession] = useState(null); // { access_token, ... }
    const [user, setUser] = useState(null);       // { id, ... }
    const [otpSent, setOtpSent] = useState(false);

    // Rehydrate from localStorage on mount
    useEffect(() => {
        try {
            const raw = localStorage.getItem("authData");
        if (!raw) return;
            const parsed = JSON.parse(raw);
            if (parsed?.session?.access_token) {
                setSession(parsed.session);
                setUser(parsed.user ?? null);
            }
        } catch (_) {}
    }, []);

    const persist = useCallback((data) => {
        try {
            localStorage.setItem("authData", JSON.stringify(data));
        } catch (_) {}
    }, []);

    // --- API Helpers ---
    const apiUrl = typeof __API_URL__ !== "undefined" ? __API_URL__ : ""; // use api url env variable defined in vite.config.js

    const requestOtp = useCallback(async (phone) => {
        setError("");
        if (!phone) {
            setError("Phone number can't be blank!")
            throw new Error("Phone number can't be blank!");
        }
        setLoading(true);
        try {
            const res = await fetch(`${apiUrl}/auth/phone/otp?phone=${encodeURIComponent(phone)}`);
            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}));
                setError(errorData.message || res.statusText || "Failed to send OTP");
                throw new Error(errorData.message || res.statusText || "Failed to send OTP");
            }
            await res.json().catch(() => ({}));
            setOtpSent(true);
        } catch (e) {
            setError(e?.message || "Failed to send OTP. Please try again.");
            throw e;
        } finally {
            setLoading(false);
        }
    }, [apiUrl]);

    const verifyOtp = useCallback(async ({ phone, code }) => {
        setError("");
        if (!phone || !code) {
            setError("Phone and 6-digit code are required");
            throw new ("Phone and 6-digit code are required");
        }
        if (String(code).length < 6) {
            setError("OTP codes are 6 digits!");
            throw new ("OTP codes are 6 digits!");
        }
        setLoading(true);
        try {
            const res = await fetch(`${apiUrl}/auth/phone/otp`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ phone, code })
            });
            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}));
                setError(errorData.message || `Authentication failed with status ${res.status}`);
                throw new Error(errorData.message || `Authentication failed with status ${res.status}`);
            }
            const data = await res.json();
            setSession(data?.session ?? null);
            setUser(data?.user ?? null);
            persist(data);
            return data;
        } catch (e) {
            setError(e?.message || "Failed to verify OTP");
            throw e;
        } finally {
            setLoading(false);
        }
    }, [apiUrl, persist]);

    // Add authorization header automatically using current token
    const fetchWithAuth = useCallback(async (path, init = {}) => {
        const token = session?.access_token;
        const headers = new Headers(init.headers || {});
        if (token) headers.set("Authorization", `Bearer ${token}`);
        return fetch(`${apiUrl}${path.startsWith("/") ? path : `/${path}`}`, { ...init, headers });
    }, [apiUrl, session?.access_token]);

    const signOut = useCallback(() => {
        setSession(null);
        setUser(null);
        setOtpSent(false);
        setError("");
        try { localStorage.removeItem("authData"); } catch (_) {}
    }, []);

    const value = useMemo(() => ({
        // state
        loading,
        error,
        session,
        user,
        otpSent,

        // derived
        isAuthenticated: Boolean(session?.access_token),

        // actions
        requestOtp,
        verifyOtp,
        fetchWithAuth,
        signOut,
        setError,
    }), [loading, error, session, user, otpSent, requestOtp, verifyOtp, fetchWithAuth, signOut]);

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
    return ctx;
}
