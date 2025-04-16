import React from 'react';
import {Route, Routes } from 'react-router-dom';
import Navbar from './components/Navbar.jsx';
import Dashboard from './components/Dashboard.jsx';
import DeviceList from './components/DeviceList.jsx';
import Login from './components/Login.jsx';
import Register from './components/Register.jsx';

const App = () => {
    return (
        <>
            <Navbar/>
            <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/devices" element={<DeviceList />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
            </Routes>
        </>
    );
};

export default App;