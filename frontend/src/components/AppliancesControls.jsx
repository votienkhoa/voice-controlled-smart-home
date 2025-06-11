import { useState } from "react";

const AppliancesControls = ({ devices = [] }) => {
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
            </div>
          );
        })}
      </div>
    </div>
  )
}

export default AppliancesControls