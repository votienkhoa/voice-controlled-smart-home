import { useState } from "react";
import axios from 'axios';

const api_url = import.meta.env.VITE_API_URL
const LightsControls = () => {
  
  const [lights, setLights] = useState([
    { name: "Light 1", brightness: 60, status: 0 },
    { name: "Light 2", brightness: 80, status: 0 },
    { name: "Light 3", brightness: 45, status: 0 },
    { name: "Light 4", brightness: 30, status: 0 },
    { name: "Light 5", brightness: 50, status: 0 },
  ]);

  const turnOnLight = async (index) => {
    let url = ""
    const newLights = [...lights];
    try {
        if (lights[index].status === 0){
          url = api_url + "/led/on"
          newLights[index].status = 1
        }
        else{
          url = api_url + "/led/off"
          newLights[index].status = 0
        }
        setLights(newLights);
        const response = await axios.get(`${url}`);
        return response.data;
    } catch (error) {
        console.error("Error fetching devices:", error);
        return []; // Return an empty array on error
    }
  };
    return (
        <div className="mt-8">
        <h2 className="text-xl mb-4">Light</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {lights.map((light, index) => (
            <div key={index} className="bg-gray-800 p-4 rounded-lg flex justify-between items-center">
              <div>
                <div className="text-lg">{light.name}</div>
                <div className="text-gray-400">{light.brightness}%</div>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={light.brightness}
                onChange={(e) => {
                  const newLights = [...lights];
                  newLights[index].brightness = e.target.value;
                  setLights(newLights);
                }}
                className="w-1/2"
              />
              <button className="text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 me-2 mb-2 dark:bg-blue-600 dark:hover:bg-blue-700 focus:outline-none dark:focus:ring-blue-800" onClick={() => turnOnLight(index)}>
                Turn {light.status===0?"on":"off"}
              </button>
            </div>
          ))}
        </div>
      </div>
    )
}

export default LightsControls