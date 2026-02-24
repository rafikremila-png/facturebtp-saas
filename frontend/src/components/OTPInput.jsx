import { useState, useRef, useEffect } from "react";
import { Input } from "@/components/ui/input";

export default function OTPInput({ length = 6, value, onChange, disabled = false }) {
    const [otp, setOtp] = useState(new Array(length).fill(""));
    const inputRefs = useRef([]);

    useEffect(() => {
        if (value) {
            const otpArray = value.split("").slice(0, length);
            while (otpArray.length < length) otpArray.push("");
            setOtp(otpArray);
        }
    }, [value, length]);

    const handleChange = (index, e) => {
        const val = e.target.value;
        if (isNaN(val)) return;

        const newOtp = [...otp];
        newOtp[index] = val.slice(-1);
        setOtp(newOtp);

        const otpString = newOtp.join("");
        onChange(otpString);

        // Move to next input
        if (val && index < length - 1) {
            inputRefs.current[index + 1]?.focus();
        }
    };

    const handleKeyDown = (index, e) => {
        if (e.key === "Backspace" && !otp[index] && index > 0) {
            inputRefs.current[index - 1]?.focus();
        }
    };

    const handlePaste = (e) => {
        e.preventDefault();
        const pasteData = e.clipboardData.getData("text").slice(0, length);
        if (!/^\d+$/.test(pasteData)) return;

        const newOtp = pasteData.split("");
        while (newOtp.length < length) newOtp.push("");
        setOtp(newOtp);
        onChange(pasteData);

        // Focus last filled input or next empty
        const lastIndex = Math.min(pasteData.length, length) - 1;
        inputRefs.current[lastIndex]?.focus();
    };

    return (
        <div className="flex gap-2 justify-center" data-testid="otp-input">
            {otp.map((digit, index) => (
                <Input
                    key={index}
                    ref={(el) => (inputRefs.current[index] = el)}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleChange(index, e)}
                    onKeyDown={(e) => handleKeyDown(index, e)}
                    onPaste={handlePaste}
                    disabled={disabled}
                    className="w-12 h-12 text-center text-xl font-bold"
                    data-testid={`otp-digit-${index}`}
                />
            ))}
        </div>
    );
}
