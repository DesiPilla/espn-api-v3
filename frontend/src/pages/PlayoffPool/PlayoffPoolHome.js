import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { usePlayoffPoolAuth } from "../../components/PlayoffPool/AuthContext";
import LoginForm from "../../components/PlayoffPool/LoginForm";
import RegisterForm from "../../components/PlayoffPool/RegisterForm";
import Dashboard from "../../components/PlayoffPool/Dashboard";

const PlayoffPoolHome = () => {
    const { isAuthenticated, loading } = usePlayoffPoolAuth();
    const [showRegister, setShowRegister] = useState(false);
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();

    // Handle redirect after successful login
    useEffect(() => {
        if (isAuthenticated && !loading) {
            const redirectTo = searchParams.get("redirect");
            if (redirectTo === "join") {
                // Preserve league and team parameters
                const league = searchParams.get("league");
                const team = searchParams.get("team");
                let joinPath = "/playoff-pool/join";
                const params = new URLSearchParams();
                if (league) params.append("league", league);
                if (team) params.append("team", team);
                if (params.toString()) {
                    joinPath += "?" + params.toString();
                }
                navigate(joinPath);
            }
        }
    }, [isAuthenticated, loading, searchParams, navigate]);

    if (loading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="flex justify-center">
                    <div className="text-lg">Loading...</div>
                </div>
            </div>
        );
    }

    if (!isAuthenticated) {
        return (
            <div className="min-h-screen bg-gray-50 py-8">
                <div className="container mx-auto px-4">
                    <div className="text-center mb-8">
                        <h1 className="text-4xl font-bold text-gray-900 mb-4">
                            NFL Playoff Pool
                        </h1>
                        <p className="text-xl text-gray-600 mb-8">
                            Draft players from playoff teams and compete with
                            your friends!
                        </p>
                    </div>

                    <div className="max-w-md mx-auto">
                        {showRegister ? (
                            <div>
                                <RegisterForm
                                    onToggleLogin={() => setShowRegister(false)}
                                />
                            </div>
                        ) : (
                            <div>
                                <LoginForm
                                    onToggleRegister={() =>
                                        setShowRegister(true)
                                    }
                                />
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <Dashboard />
        </div>
    );
};

export default PlayoffPoolHome;
