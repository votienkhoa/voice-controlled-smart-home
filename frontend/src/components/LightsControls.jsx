import { useState, useEffect } from "react";
import axios from 'axios';
import { ref, set } from "firebase/database";
import { auth, database } from "../config/firebase";

const API_PORT = 3000; // Keep in sync with backend server.js
// const API_BASE = `http://localhost:${API_PORT}`;
const API_BASE = "https://api.kdth-smarthome.space";

const normalizeDevices = (devices) => {
  // If devices is an array, return as is
  if (Array.isArray(devices)) return devices;
  // If devices is an object with a 'status' property, treat as a single light
  if (devices && typeof devices === 'object' && 'status' in devices) return [devices];
  // If devices is an object with keys (e.g., { light: { status: 0 } }), extract the light object
  if (devices && typeof devices === 'object' && Object.values(devices).length === 1 && 'status' in Object.values(devices)[0]) {
    return [Object.values(devices)[0]];
  }
  return [];
};

const LightsControls = ({ devices = [], room, canControl }) => {
  const [lights, setLights] = useState(normalizeDevices(devices));

  const toggleLight = async (index) => {
    if (!canControl) return;
    let url = "";
    if (room === "Living Room") {
      url = `${API_BASE}/led/3/`;
    } else if (room === "Guest Room") {
      url = `${API_BASE}/led/1/`;
    } else if (room === "Master Bedroom") {
      url = `${API_BASE}/led/2/`;
    }
    // ...add more room logic as needed

    const newLights = [...lights];
    try {
        // Toggle logic (example, adjust as needed)
        if (lights[index].status === 0){
          newLights[index].status = 1;
          url += "on";
        }
        else{
          newLights[index].status = 0;
          url += "off";
        }
        setLights(newLights);
        await set(ref(database, `devices/${room}/light`), {
            status: newLights[index].status
        });
        // Get Firebase ID token
        const user = auth.currentUser;
        if (!user) throw new Error("User not authenticated");
        const token = await user.getIdToken();
        // POST to backend with Authorization header
        await axios.post(url, { room }, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        return;
    } catch (error) {
        console.error("Error toggling light:", error);
        return;
    }
  };

  useEffect(() => {
    setLights(normalizeDevices(devices));
  }, [devices]);

  return (
        <div className="mt-8">
        <h2 className="text-xl mb-4">Light</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {lights.map((light, index) => (
            <div key={index} className="bg-gray-800 p-4 rounded-lg flex justify-between items-center">
              <div>
                <div className="text-lg">{light.name || `Light ${index + 1}`}</div>
                <div className="text-gray-400">{light.status ? "On" : "Off"}</div>
              </div>
              <button className="text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 me-2 mb-2 dark:bg-blue-600 dark:hover:bg-blue-700 focus:outline-none dark:focus:ring-blue-800" onClick={() => toggleLight(index)} disabled={!canControl}>
                Turn {light.status===0?"on":"off"}
              </button>
              {!canControl && <div className="text-xs text-gray-500">View only</div>}
            </div>
          ))}
        </div>
      </div>
    )
}

export default LightsControls