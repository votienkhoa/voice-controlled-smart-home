import React from 'react';
import { Link } from 'react-router-dom';

const Navbar = () => {
    return (
        <>
        <nav className="bg-gray-900 text-white px-6 py-3 flex items-center justify-between shadow-md">
            <div className="flex items-center gap-3">
                <span className="text-2xl font-bold tracking-wide text-blue-400">Cloud IoT</span>
            </div>
            <ul className="flex gap-6 text-lg font-semibold">
                <li>
                    <Link to="/" className="hover:text-blue-400 text-whitex transition-colors duration-200 decoration-blue-400">Dashboard</Link>
                </li>
                <li>
                    <Link to="/devices" className="hover:text-blue-400 text-white transition-colors duration-200 decoration-blue-400">Devices</Link>
                </li>
            </ul>
        </nav>
        <hr className="border-t border-white opacity-60" />
        </>
    );
};

export default Navbar;