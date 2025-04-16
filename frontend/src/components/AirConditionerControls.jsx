import { useState } from "react";

const AirConditionerControls = () => {
  const [temperature, setTemperature] = useState(24);
    
    return (
        <div className="bg-gray-800 p-4 rounded-lg">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl">Air Conditioner</h2>
            <i className="fas fa-power-off text-gray-400"></i>
          </div>
          <div className="text-4xl mb-4">{temperature}°C</div>
          <input
            type="range"
            min="16"
            max="32"
            value={temperature}
            onChange={(e) => setTemperature(e.target.value)}
            className="w-full mb-4"
          />
        </div>
    )
}

export default AirConditionerControls