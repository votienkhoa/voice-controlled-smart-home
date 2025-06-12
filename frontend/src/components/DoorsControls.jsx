import { useState, useEffect } from "react";
import { ref, set } from "firebase/database";
import { database } from "../config/firebase";
import axios from "axios";

const API_PORT = 3000; // Keep in sync with backend server.js
// const API_BASE = `http://localhost:${API_PORT}`;
const API_BASE = "https://api.kdth-smarthome.space";


const normalizeDoors = (devices) => {
  if (Array.isArray(devices)) return devices;
  if (devices && typeof devices === "object" && ("status" in devices || "open" in devices))
    return [devices];
  if (
    devices &&
    typeof devices === "object" &&
    Object.values(devices).length === 1 &&
    (("status" in Object.values(devices)[0]) || ("open" in Object.values(devices)[0]))
  ) {
    return [Object.values(devices)[0]];
  }
  return [];
};

const DoorsControls = ({ devices = [], room, canControl }) => {

  let allDoors = normalizeDoors(devices);
  if (room === "Living Room") {
    allDoors = [
      { name: "Main Door", open: devices.open ?? false }
    ];
  }

  const [doors, setDoors] = useState(allDoors);

  useEffect(() => {
    setDoors(allDoors);
  }, [devices]);

  const toggleDoor = async (index) => {
    if (!canControl) return;
    let url = "";
    // Main Door logic for Living Room
    if (room === "Living Room" && doors[index].name === "Main Door") {
      url = `${API_BASE}/maindoor/` + (doors[index].open ? "off" : "on");
    } else if (room === "Guest Room") {
      url = `${API_BASE}/servo/1/angle/` + (doors[index].open ? "0" : "180");
    } else if (room === "Master Bedroom") {
      url = `${API_BASE}/servo/2/angle/` + (doors[index].open ? "180" : "0");
    }
    // ...add more room logic as needed

    const newDoors = [...doors];
    newDoors[index].open = !newDoors[index].open;
    setDoors(newDoors);
    // Update the door status in Firebase (customize path as needed)
    if (room === "Living Room" && doors[index].name === "Main Door") {
      await set(ref(database, `devices/${room}/door`), { open: newDoors[index].open });
    } else {
      await set(ref(database, `devices/${room}/door`), { open: newDoors[index].open });
    }
    // POST to backend
    await axios.post(url, { room });
  };

  return (
    <div className="mt-8">
      <h2 className="text-xl mb-4">Doors</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {doors.map((door, index) => (
          <div
            key={door.id || index}
            className="bg-gray-800 p-4 rounded-lg flex justify-between items-center"
          >
            <div>
              <div className="text-lg">{door.name || `Door ${index + 1}`}</div>
              <div className="text-gray-400">{door.open ? "Open" : "Closed"}</div>
            </div>
            <button
              className={`px-4 py-2 rounded ${
                door.open ? "bg-red-500" : "bg-green-500"
              } text-white`}
              onClick={() => toggleDoor(index)}
              disabled={!canControl}
            >
              {door.open ? "Close" : "Open"}
            </button>
            {!canControl && <div className="text-xs text-gray-500">View only</div>}
          </div>
        ))}
      </div>
    </div>
  );
};

export default DoorsControls;
