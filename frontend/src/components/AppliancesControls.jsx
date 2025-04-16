import { useState } from "react";

const AppliancesControls = () => {
  const [devices, setDevices] = useState([
    { name: "Smart TV", active: true, hours: 3, energy: "5kwh" },
    { name: "Speaker", active: true, hours: 3, energy: "5kwh" },
    { name: "Router", active: false, hours: 3, energy: "5kwh" },
    { name: "Wifi", active: false, hours: 3, energy: "5kwh" },
    { name: "Heater", active: true, hours: 3, energy: "5kwh" },
    { name: "Socket", active: true, hours: 3, energy: "5kwh" },
  ]);

    return (
        <div className="bg-gray-800 p-4 rounded-lg">
          <h2 className="text-xl mb-4">My Devices</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {devices.map((device, index) => (
              <div key={index} className="bg-gray-800 p-4 rounded-lg flex justify-between items-center">
                <div>
                  <div className="text-lg">{device.name}</div>
                  <div className="text-gray-400">Active for {device.hours} hours</div>
                  <div className="text-gray-400">{device.energy}</div>
                </div>
                <i className={`fas fa-toggle-${device.active ? "on text-blue-500" : "off text-gray-400"} text-2xl`}></i>
              </div>
            ))}
          </div>
        </div>
    )
}

export default AppliancesControls