import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '@contexts/AuthContext'

export default function PhoneAuthFormComponent() {
    const { loading, error, setError, otpSent, session, user, requestOtp, verifyOtp, signOut } = useAuth();
    const [phone, setPhone] = useState("");
    const [code, setCode] = useState("");

    const onGetOtp = useCallback(async (e) => {
        e.preventDefault();
        await requestOtp(phone);
    }, [phone, requestOtp]);

    const onVerify = useCallback(async (e) => {
        e.preventDefault();
        await verifyOtp({ phone, code });
    }, [phone, code, verifyOtp]);

    return (
        <div className="flex flex-col justify-center space-y-12 max-w-98 font-normal">

            <form className="flex flex-col" onChange={() => setError("")} onSubmit={onGetOtp}>
                {error && <p className="text-red">{error}</p>}
                <h1 className="whitespace-nowrap">Enter phone number in +1 format:</h1>
                <input
                    name="phoneNumber"
                    type="tel"
                    className="outline-none text-center px-4 text-6xl"
                    placeholder="+1 123 456 7891"
                    onChange={(e) => setPhone(e.target.value)}
                    required
                    disabled={loading}
                />
                <button type="submit" className="bg-primary text-2xl" disabled={loading}>get otp code</button>
            </form>

            {otpSent && !session && (
                <div className="text-center">
                    <h1 className="whitespace-nowrap"><span className='text-primary'>code sent!</span> your phone should recieve an otp code shortly</h1>
                    <form className="flex flex-col" onSubmit={onVerify}>
                        <input
                            inputMode="numeric"
                            pattern="[0-9]*"
                            maxLength={6}
                            className="outline-none text-6xl tracking-[0.4em] text-center"
                            value={code}
                            // only allow numbers
                            onChange={(e) => {
                                const value = e.target.value;
                                if (/^\d*$/.test(value)) {
                                    setCode(value);
                                }
                            }}
                            required
                            disabled={loading}
                        />
                        <button type="submit" className="bg-green-400 text-2xl" disabled={loading}>submit</button>
                    </form>
                    <button onClick={() => requestOtp(phone)} disabled={loading}>resend otp</button>
                </div>
            )}

            {session && (
                <div>
                    <div className="w-fit break-all">
                        <h3 className="text-green-300">you are authorized!</h3>
                        <p>id: {user?.id || "none"}</p>
                        <p className="w-fit text-red">bearer token: <span className="text-primary">{session?.access_token || "none"}</span></p>
                    </div>
                    <button onClick={signOut} className='bg-red px-2'>Sign Out</button>
                </div>
            )}
        </div>
    );
}