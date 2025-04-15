import axios from 'axios';

const API_URL = 'https://localhost:3000'; // Replace with your actual API URL

export const fetchDevices = async () => {
    try {
        const response = await axios.get(`${API_URL}/devices`);
        return response.data;
    } catch (error) {
        console.error("Error fetching devices:", error);
        return []; // Return an empty array on error
    }
};