import { useEffect, useState } from "react";
import { ref, onValue } from "firebase/database";
import { database } from "../config/firebase";
import AppliancesControls from "./AppliancesControls.jsx";
import LightsControls from "./LightsControls.jsx";
import DoorsControls from "./DoorsControls.jsx";
import axios from "axios";
import { getAuth } from "firebase/auth";

const API_PORT = 3000; // Keep in sync with backend server.js
// const API_BASE = `http://localhost:${API_PORT}`;
const API_BASE = "https://api.kdth-smarthome.space";


const RoomDevicesView = ({ room }) => {
    const [devices, setDevices] = useState({});
    const [allowedRooms, setAllowedRooms] = useState([]);
    const [user, setUser] = useState(null);

    // Fetch user access rights
    useEffect(() => {
        const auth = getAuth();
        const unsubscribe = auth.onAuthStateChanged((firebaseUser) => {
            setUser(firebaseUser);
            if (firebaseUser) {
                const accessRef = ref(database, `userAccess/${firebaseUser.uid}`);
                onValue(accessRef, (snapshot) => {
                    const data = snapshot.val();
                    setAllowedRooms(Array.isArray(data) ? data : (data ? Object.values(data) : []));
                });
            } else {
                setAllowedRooms([]);
            }
        });
        return () => unsubscribe();
    }, []);

    // Poll the backend every 5 seconds to trigger device value update from Raspberry Pi
    useEffect(() => {
        if (!room) return;
        const interval = setInterval(() => {
            if (devices["Temperature & Humidity Sensor"]) {
                axios.get(`${API_BASE}/dht11/temp`);
                axios.get(`${API_BASE}/dht11/hum`);
            }
            if (devices["Gas Sensor"]) {
                axios.get(`${API_BASE}/mq2`);
            }
        }, 5000);
        return () => clearInterval(interval);
    }, [room, devices]);

    useEffect(() => {
        if (!room) return;
        const roomRef = ref(database, `devices/${room}`);
        const unsubscribe = onValue(roomRef, (snapshot) => {
            setDevices(snapshot.val() || {});
        });
        return () => unsubscribe();
    }, [room]);

    const applianceDevices = Object.entries(devices)
        .filter(([key, value]) => key !== 'light' && key !== 'door' && value && ((Array.isArray(value) && value.length > 0) || (typeof value === 'object' && Object.keys(value).length > 0)))
        .map(([key, value]) => ({ type: key, ...value }));

    const hasAppliances = applianceDevices.length > 0;
    const hasLights = devices.light && ((Array.isArray(devices.light) && devices.light.length > 0) || (typeof devices.light === 'object' && Object.keys(devices.light).length > 0));
    const hasDoors = devices.door && ((Array.isArray(devices.door) && devices.door.length > 0) || (typeof devices.door === 'object' && Object.keys(devices.door).length > 0));

    // Only allow control if user is allowed for this room
    const canControl = allowedRooms.includes(room);

    return (
        <div className="flex flex-col md:flex-row gap-6 w-full">
            {hasAppliances && (
                <div className="md:w-1/2 w-full">
                    <AppliancesControls devices={applianceDevices} canControl={canControl} room={room} />
                </div>
            )}
            <div className="md:w-1/2 w-full flex flex-col gap-6">
                {hasLights && <LightsControls devices={devices.light} room={room} canControl={canControl} />}
                {hasDoors && <DoorsControls devices={devices.door} room={room} canControl={canControl} />}
            </div>
        </div>
    )
}

export default RoomDevicesView