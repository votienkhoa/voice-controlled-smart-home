import axios from 'axios';

const API_URL = 'https://localhost:3000'; // Replace with your actual API URL

// Authentication API functions
export const login = async (email, password) => {
    try {
        const response = await axios.post(`${API_URL}/auth/login`, { email, password });
        if (response.data.token) {
            localStorage.setItem('token', response.data.token);
        }
        return response.data;
    } catch (error) {
        console.error("Error during login:", error);
        throw error;
    }
};

export const register = async (name, email, password) => {
    try {
        const response = await axios.post(`${API_URL}/auth/register`, { name, email, password });
        return response.data;
    } catch (error) {
        console.error("Error during registration:", error);
        throw error;
    }
};

export const fetchDevices = async () => {
    try {
        const response = await axios.get(`${API_URL}/devices`);
        return response.data;
    } catch (error) {
        console.error("Error fetching devices:", error);
        return []; // Return an empty array on error
    }
};