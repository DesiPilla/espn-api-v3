import React, { useState } from 'react';
import { usePlayoffPoolAuth } from './AuthContext';

const RegisterForm = ({ onToggleLogin }) => {
    const [formData, setFormData] = useState({
        username: "",
        email: "",
        password: "",
        confirmPassword: "",
        display_name: "",
    });
    const [showPassword, setShowPassword] = useState(false);
    const [errors, setErrors] = useState({});

    const { register, loading, error, clearError } = usePlayoffPoolAuth();

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value,
        });
        // Clear errors when user starts typing
        if (error) clearError();
        if (errors[e.target.name]) {
            setErrors({ ...errors, [e.target.name]: "" });
        }
    };

    const validateForm = () => {
        const newErrors = {};

        if (!formData.username.trim()) {
            newErrors.username = "Username is required";
        }

        if (!formData.email.trim()) {
            newErrors.email = "Email is required";
        } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
            newErrors.email = "Email is invalid";
        }

        if (!formData.password) {
            newErrors.password = "Password is required";
        } else if (formData.password.length < 6) {
            newErrors.password = "Password must be at least 6 characters";
        }

        if (formData.password !== formData.confirmPassword) {
            newErrors.confirmPassword = "Passwords do not match";
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!validateForm()) return;

        const registerData = {
            username: formData.username,
            email: formData.email,
            password: formData.password,
            display_name: formData.display_name,
        };

        await register(registerData);
    };

    return (
        <div
            style={{
                backgroundColor: "white",
                boxShadow:
                    "0 4px 6px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0, 0, 0, 0.1)",
                border: "1px solid #e2e8f0",
                borderRadius: "12px",
                padding: "32px",
                width: "100%",
                maxWidth: "400px",
            }}
        >
            {/* Header Section */}
            <div style={{ textAlign: "center", marginBottom: "32px" }}>
                <div
                    style={{
                        width: "48px",
                        height: "48px",
                        backgroundColor: "#10b981",
                        borderRadius: "12px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        margin: "0 auto 16px",
                    }}
                >
                    <span style={{ fontSize: "24px", color: "white" }}>🏈</span>
                </div>
                <h2
                    style={{
                        fontSize: "28px",
                        fontWeight: "700",
                        color: "#1a202c",
                        margin: "0 0 8px 0",
                        lineHeight: "1.2",
                    }}
                >
                    Create Account
                </h2>
                <p
                    style={{
                        fontSize: "15px",
                        color: "#64748b",
                        margin: "0",
                        lineHeight: "1.4",
                    }}
                >
                    Join your playoff pool today
                </p>
            </div>

            {/* Error Message */}
            {error && (
                <div
                    style={{
                        backgroundColor: "#fef2f2",
                        border: "1px solid #fecaca",
                        borderRadius: "8px",
                        padding: "12px 16px",
                        marginBottom: "24px",
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                    }}
                >
                    <div
                        style={{
                            width: "16px",
                            height: "16px",
                            borderRadius: "50%",
                            backgroundColor: "#ef4444",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            fontSize: "11px",
                            fontWeight: "bold",
                            color: "white",
                            flexShrink: 0,
                        }}
                    >
                        !
                    </div>
                    <span
                        style={{
                            fontSize: "14px",
                            color: "#dc2626",
                            fontWeight: "500",
                        }}
                    >
                        {error}
                    </span>
                </div>
            )}

            <form onSubmit={handleSubmit}>
                {/* Username Field */}
                <div style={{ marginBottom: "20px" }}>
                    <label
                        style={{
                            display: "block",
                            fontSize: "14px",
                            fontWeight: "600",
                            color: "#374151",
                            marginBottom: "6px",
                        }}
                        htmlFor="username"
                    >
                        Username <span style={{ color: "#ef4444" }}>*</span>
                    </label>
                    <input
                        type="text"
                        id="username"
                        name="username"
                        value={formData.username}
                        onChange={handleChange}
                        required
                        style={{
                            width: "100%",
                            padding: "12px 16px",
                            fontSize: "15px",
                            border: errors.username
                                ? "2px solid #ef4444"
                                : "2px solid #e2e8f0",
                            borderRadius: "8px",
                            backgroundColor: "#ffffff",
                            color: "#1a202c",
                            transition:
                                "border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out",
                            outline: "none",
                            boxSizing: "border-box",
                        }}
                        placeholder="Choose a username"
                        onFocus={(e) => {
                            if (!errors.username) {
                                e.target.style.borderColor = "#10b981";
                                e.target.style.boxShadow =
                                    "0 0 0 3px rgba(16, 185, 129, 0.1)";
                            }
                        }}
                        onBlur={(e) => {
                            if (!errors.username) {
                                e.target.style.borderColor = "#e2e8f0";
                                e.target.style.boxShadow = "none";
                            }
                        }}
                    />
                    {errors.username && (
                        <p
                            style={{
                                fontSize: "13px",
                                color: "#ef4444",
                                marginTop: "6px",
                                fontWeight: "500",
                            }}
                        >
                            {errors.username}
                        </p>
                    )}
                </div>

                {/* Email Field */}
                <div style={{ marginBottom: "20px" }}>
                    <label
                        style={{
                            display: "block",
                            fontSize: "14px",
                            fontWeight: "600",
                            color: "#374151",
                            marginBottom: "6px",
                        }}
                        htmlFor="email"
                    >
                        Email <span style={{ color: "#ef4444" }}>*</span>
                    </label>
                    <input
                        type="email"
                        id="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        required
                        style={{
                            width: "100%",
                            padding: "12px 16px",
                            fontSize: "15px",
                            border: errors.email
                                ? "2px solid #ef4444"
                                : "2px solid #e2e8f0",
                            borderRadius: "8px",
                            backgroundColor: "#ffffff",
                            color: "#1a202c",
                            transition:
                                "border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out",
                            outline: "none",
                            boxSizing: "border-box",
                        }}
                        placeholder="Enter your email"
                        onFocus={(e) => {
                            if (!errors.email) {
                                e.target.style.borderColor = "#10b981";
                                e.target.style.boxShadow =
                                    "0 0 0 3px rgba(16, 185, 129, 0.1)";
                            }
                        }}
                        onBlur={(e) => {
                            if (!errors.email) {
                                e.target.style.borderColor = "#e2e8f0";
                                e.target.style.boxShadow = "none";
                            }
                        }}
                    />
                    {errors.email && (
                        <p
                            style={{
                                fontSize: "13px",
                                color: "#ef4444",
                                marginTop: "6px",
                                fontWeight: "500",
                            }}
                        >
                            {errors.email}
                        </p>
                    )}
                </div>

                {/* Display Name Field */}
                <div style={{ marginBottom: "20px" }}>
                    <label
                        style={{
                            display: "block",
                            fontSize: "14px",
                            fontWeight: "600",
                            color: "#374151",
                            marginBottom: "6px",
                        }}
                        htmlFor="display_name"
                    >
                        Display Name{" "}
                        <span style={{ fontSize: "13px", color: "#9ca3af" }}>
                            (optional)
                        </span>
                    </label>
                    <input
                        type="text"
                        id="display_name"
                        name="display_name"
                        value={formData.display_name}
                        onChange={handleChange}
                        style={{
                            width: "100%",
                            padding: "12px 16px",
                            fontSize: "15px",
                            border: "2px solid #e2e8f0",
                            borderRadius: "8px",
                            backgroundColor: "#ffffff",
                            color: "#1a202c",
                            transition:
                                "border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out",
                            outline: "none",
                            boxSizing: "border-box",
                        }}
                        placeholder="Your display name"
                        onFocus={(e) => {
                            e.target.style.borderColor = "#10b981";
                            e.target.style.boxShadow =
                                "0 0 0 3px rgba(16, 185, 129, 0.1)";
                        }}
                        onBlur={(e) => {
                            e.target.style.borderColor = "#e2e8f0";
                            e.target.style.boxShadow = "none";
                        }}
                    />
                </div>

                {/* Password Field */}
                <div style={{ marginBottom: "20px" }}>
                    <label
                        style={{
                            display: "block",
                            fontSize: "14px",
                            fontWeight: "600",
                            color: "#374151",
                            marginBottom: "6px",
                        }}
                        htmlFor="password"
                    >
                        Password <span style={{ color: "#ef4444" }}>*</span>
                    </label>
                    <div style={{ position: "relative" }}>
                        <input
                            type={showPassword ? "text" : "password"}
                            id="password"
                            name="password"
                            value={formData.password}
                            onChange={handleChange}
                            required
                            style={{
                                width: "100%",
                                padding: "12px 16px",
                                paddingRight: "48px",
                                fontSize: "15px",
                                border: errors.password
                                    ? "2px solid #ef4444"
                                    : "2px solid #e2e8f0",
                                borderRadius: "8px",
                                backgroundColor: "#ffffff",
                                color: "#1a202c",
                                transition:
                                    "border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out",
                                outline: "none",
                                boxSizing: "border-box",
                            }}
                            placeholder="Choose a password (min. 6 characters)"
                            onFocus={(e) => {
                                if (!errors.password) {
                                    e.target.style.borderColor = "#10b981";
                                    e.target.style.boxShadow =
                                        "0 0 0 3px rgba(16, 185, 129, 0.1)";
                                }
                            }}
                            onBlur={(e) => {
                                if (!errors.password) {
                                    e.target.style.borderColor = "#e2e8f0";
                                    e.target.style.boxShadow = "none";
                                }
                            }}
                        />
                        <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            style={{
                                position: "absolute",
                                right: "12px",
                                top: "50%",
                                transform: "translateY(-50%)",
                                background: "none",
                                border: "none",
                                cursor: "pointer",
                                padding: "4px",
                                borderRadius: "4px",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                transition:
                                    "background-color 0.15s ease-in-out",
                            }}
                            onMouseEnter={(e) =>
                                (e.target.style.backgroundColor = "#f1f5f9")
                            }
                            onMouseLeave={(e) =>
                                (e.target.style.backgroundColor = "transparent")
                            }
                        >
                            <span style={{ fontSize: "18px" }}>
                                {showPassword ? "🙈" : "👁️"}
                            </span>
                        </button>
                    </div>
                    {errors.password && (
                        <p
                            style={{
                                fontSize: "13px",
                                color: "#ef4444",
                                marginTop: "6px",
                                fontWeight: "500",
                            }}
                        >
                            {errors.password}
                        </p>
                    )}
                </div>

                {/* Confirm Password Field */}
                <div style={{ marginBottom: "24px" }}>
                    <label
                        style={{
                            display: "block",
                            fontSize: "14px",
                            fontWeight: "600",
                            color: "#374151",
                            marginBottom: "6px",
                        }}
                        htmlFor="confirmPassword"
                    >
                        Confirm Password{" "}
                        <span style={{ color: "#ef4444" }}>*</span>
                    </label>
                    <input
                        type={showPassword ? "text" : "password"}
                        id="confirmPassword"
                        name="confirmPassword"
                        value={formData.confirmPassword}
                        onChange={handleChange}
                        required
                        style={{
                            width: "100%",
                            padding: "12px 16px",
                            fontSize: "15px",
                            border: errors.confirmPassword
                                ? "2px solid #ef4444"
                                : "2px solid #e2e8f0",
                            borderRadius: "8px",
                            backgroundColor: "#ffffff",
                            color: "#1a202c",
                            transition:
                                "border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out",
                            outline: "none",
                            boxSizing: "border-box",
                        }}
                        placeholder="Confirm your password"
                        onFocus={(e) => {
                            if (!errors.confirmPassword) {
                                e.target.style.borderColor = "#10b981";
                                e.target.style.boxShadow =
                                    "0 0 0 3px rgba(16, 185, 129, 0.1)";
                            }
                        }}
                        onBlur={(e) => {
                            if (!errors.confirmPassword) {
                                e.target.style.borderColor = "#e2e8f0";
                                e.target.style.boxShadow = "none";
                            }
                        }}
                    />
                    {errors.confirmPassword && (
                        <p
                            style={{
                                fontSize: "13px",
                                color: "#ef4444",
                                marginTop: "6px",
                                fontWeight: "500",
                            }}
                        >
                            {errors.confirmPassword}
                        </p>
                    )}
                </div>

                {/* Submit Button */}
                <button
                    type="submit"
                    disabled={loading}
                    style={{
                        width: "100%",
                        padding: "14px 20px",
                        fontSize: "15px",
                        fontWeight: "600",
                        borderRadius: "8px",
                        border: "none",
                        cursor: loading ? "not-allowed" : "pointer",
                        transition: "all 0.15s ease-in-out",
                        backgroundColor: loading ? "#9ca3af" : "#10b981",
                        color: "white",
                        boxShadow: loading
                            ? "none"
                            : "0 1px 3px rgba(0, 0, 0, 0.1)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: "8px",
                    }}
                    onMouseEnter={(e) => {
                        if (!loading) {
                            e.target.style.backgroundColor = "#059669";
                            e.target.style.boxShadow =
                                "0 4px 6px rgba(0, 0, 0, 0.1)";
                            e.target.style.transform = "translateY(-1px)";
                        }
                    }}
                    onMouseLeave={(e) => {
                        if (!loading) {
                            e.target.style.backgroundColor = "#10b981";
                            e.target.style.boxShadow =
                                "0 1px 3px rgba(0, 0, 0, 0.1)";
                            e.target.style.transform = "translateY(0)";
                        }
                    }}
                >
                    {loading && (
                        <div
                            style={{
                                width: "16px",
                                height: "16px",
                                border: "2px solid transparent",
                                borderTop: "2px solid #ffffff",
                                borderRadius: "50%",
                                animation: "spin 1s linear infinite",
                            }}
                        />
                    )}
                    {loading ? "Creating Account..." : "Create Account"}
                </button>
            </form>

            {/* Login Link */}
            {onToggleLogin && (
                <div style={{ textAlign: "center", marginTop: "24px" }}>
                    <button
                        onClick={onToggleLogin}
                        style={{
                            background: "none",
                            border: "none",
                            color: "#10b981",
                            fontSize: "14px",
                            fontWeight: "500",
                            cursor: "pointer",
                            padding: "8px",
                            borderRadius: "4px",
                            transition: "all 0.15s ease-in-out",
                            textDecoration: "none",
                        }}
                        onMouseEnter={(e) => {
                            e.target.style.color = "#059669";
                            e.target.style.backgroundColor = "#f1f5f9";
                        }}
                        onMouseLeave={(e) => {
                            e.target.style.color = "#10b981";
                            e.target.style.backgroundColor = "transparent";
                        }}
                    >
                        Already have an account? Sign in
                    </button>
                </div>
            )}

            {/* Add loading animation keyframes */}
            <style jsx>{`
                @keyframes spin {
                    0% {
                        transform: rotate(0deg);
                    }
                    100% {
                        transform: rotate(360deg);
                    }
                }
            `}</style>
        </div>
    );
};

export default RegisterForm;