import React, { useState, useEffect } from 'react';
import { Route, Routes, Navigate } from 'react-router-dom';
import { onAuthStateChanged } from "firebase/auth";
import { auth } from './config/firebase';
import Navbar from './components/Navbar.jsx';
import Dashboard from './components/Dashboard.jsx';
import DeviceList from './components/DeviceList.jsx';
import Login from './components/Login.jsx';
import Register from './components/Register.jsx';

const App = () => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, (user) => {
            setIsAuthenticated(!!user);
            setIsLoading(false);
        });

        // Cleanup subscription on unmount
        return () => unsubscribe();
    }, []);

    const handleLoginSuccess = (user) => {
        setIsAuthenticated(true);
    };

    const handleRegisterSuccess = (user) => {
        setIsAuthenticated(true);
    };

    if (isLoading) {
        return <div>Loading...</div>; // Or your loading component
    }

    return (
        <>
            <Navbar isAuthenticated={isAuthenticated} />
            <Routes>
                <Route 
                    path="/" 
                    element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" replace />} 
                />
                <Route 
                    path="/devices" 
                    element={isAuthenticated ? <DeviceList /> : <Navigate to="/login" replace />} 
                />
                <Route 
                    path="/login" 
                    element={!isAuthenticated ? <Login onLoginSuccess={handleLoginSuccess} /> : <Navigate to="/" replace />} 
                />
                <Route 
                    path="/register" 
                    element={!isAuthenticated ? <Register onRegisterSuccess={handleRegisterSuccess} /> : <Navigate to="/" replace />} 
                />
            </Routes>
        </>
    );
};

export default App;