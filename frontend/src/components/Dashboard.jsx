import React from 'react';
import { useState, useEffect } from 'react';
import { signOut } from "firebase/auth";
import { auth } from '../firebase';
import { useNavigate } from 'react-router-dom';
import AddDevice from './AddDevice.jsx';
import RoomDevicesView from './RoomDevicesView.jsx';
import { Tabs } from 'flowbite-react';

const Dashboard = () => {
  const [openAddDeviceModal, setOpenAddDeviceModal] = useState(false)
  const [currentRoom, setCurrentRoom] = useState("Living Room")
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await signOut(auth);
      // The onAuthStateChanged listener in App.jsx will handle the navigation
    } catch (error) {
      console.error("Error signing out:", error);
    }
  };

  useEffect(() => {

  }, [currentRoom])

  return (
    <div className="p-4 bg-gray-900 text-white min-h-screen">
      <div className="flex justify-between items-center mb-4">
        <div className="flex space-x-4">
          <Tabs variant="pills">
            {['Living Room', 'Kitchen Room', 'Bed Room', 'Movie Room', 'Game Room'].map(room => (
              <Tabs.Item title={room}></Tabs.Item>
            ))}
          </Tabs>
          
          <button className="text-gray-400 px-4 py-2">+ Add</button>
        </div>
        <div className="flex items-center space-x-4">
          <button onClick={() => setOpenAddDeviceModal(true)} className="bg-blue-500 text-white px-4 py-2 rounded">+ Add Device</button>
          <button onClick={handleLogout} className="bg-red-500 text-white px-4 py-2 rounded">Logout</button>
        </div>
        <AddDevice modalHook={[openAddDeviceModal, setOpenAddDeviceModal]} />
      </div>
      <RoomDevicesView room={currentRoom} />
      
    </div>
    );
};

export default Dashboard;