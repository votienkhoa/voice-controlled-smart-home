import { useState, useEffect } from "react";
import { ref, set } from "firebase/database";
import { database } from "../config/firebase";

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

const DoorsControls = ({ devices = [], room }) => {
  const [doors, setDoors] = useState(normalizeDoors(devices));

  useEffect(() => {
    setDoors(normalizeDoors(devices));
  }, [devices]);

  const toggleDoor = async (index) => {
    const newDoors = [...doors];
    newDoors[index].open = !newDoors[index].open;
    setDoors(newDoors);
    // Update the door status in Firebase (customize path as needed)
    await set(
      ref(database, `devices/${room}/door`), {
            open: newDoors[index].open
    });
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
            >
              {door.open ? "Close" : "Open"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DoorsControls;
