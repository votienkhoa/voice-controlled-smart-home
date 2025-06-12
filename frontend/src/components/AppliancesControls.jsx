import { useState } from "react";

const API_PORT = 3000; // Keep in sync with backend server.js
// const API_BASE = `http://localhost:${API_PORT}`;
const API_BASE = "api.kdth-smarthome.space";


const AppliancesControls = ({ devices = [], canControl, room }) => {
  return (
    <div className="mt-8">
      <h2 className="text-xl mb-4">My Devices</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {devices.map((device, index) => {
          const { name, ...readings } = device;
          return (
            <div key={index} className="bg-gray-800 p-4 rounded-lg flex justify-between items-center">
              <div>
                <div className="text-lg">{(name || `Device ${index + 1}`)}</div>
                {Object.entries(readings).map(([key, value]) => (
                  <div key={key} className="text-gray-400">
                    <span className="font-medium capitalize">{key}:</span> {String(value)}
                  </div>
                ))}
              </div>
              {/* Example: Add control buttons here if canControl is true */}
              {!canControl && <div className="text-xs text-gray-500">View only</div>}
            </div>
          );
        })}
      </div>
    </div>
  )
}

// Use API_BASE for any axios/fetch calls you add here in the future

export default AppliancesControls