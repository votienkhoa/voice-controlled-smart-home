import React from 'react';
import { useState, useEffect } from 'react';
import { signOut } from "firebase/auth";
import { auth, database } from '../config/firebase';
import { useNavigate } from 'react-router-dom';
import AddDevice from './AddDevice.jsx';
import RoomDevicesView from './RoomDevicesView.jsx';
import { ref, onValue } from 'firebase/database';

const Dashboard = () => {
  const [openAddDeviceModal, setOpenAddDeviceModal] = useState(false)
  const [rooms, setRooms] = useState([]);
  const [devices, setDevices] = useState({});
  const [currentRoom, setCurrentRoom] = useState("");
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
    // Fetch rooms and devices from Firebase
    const roomsRef = ref(database, 'rooms');
    const devicesRef = ref(database, 'devices');

    const unsubscribeRooms = onValue(roomsRef, (snapshot) => {
      const data = snapshot.val();
      if (data) {
        setRooms(Object.keys(data));
      } else {
        setRooms([]);
      }
    });

    const unsubscribeDevices = onValue(devicesRef, (snapshot) => {
      const data = snapshot.val();
      setDevices(data || {});
    });

    return () => {
      unsubscribeRooms();
      unsubscribeDevices();
    };
  }, []);

  useEffect(() => {
    if (rooms.length > 0 && (!currentRoom || !rooms.includes(currentRoom))) {
      setCurrentRoom(rooms[0]);
    }
    // No dependency on currentRoom to avoid infinite loop
  }, [rooms]);

  return (
    <div className="p-4 bg-gray-900 text-white min-h-screen">
      <div className="flex justify-between items-center mb-4">
        <div className="flex space-x-4">
          <div className="flex">
            {rooms.length > 0 ? rooms.map(room => (
              <button
                key={room}
                className={`px-4 py-2 rounded-lg focus:outline-none mr-2 ${currentRoom === room ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300'}`}
                onClick={() => setCurrentRoom(room)}
              >
                {room}
              </button>
            )) : (
              <button className="px-4 py-2 rounded-lg bg-gray-700 text-gray-300">{currentRoom}</button>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-4 ml-auto">
          <button onClick={() => setOpenAddDeviceModal(true)} className="bg-blue-500 text-white px-4 py-2 rounded">+ Add Device</button>
          <button onClick={handleLogout} className="bg-red-500 text-white px-4 py-2 rounded">Logout</button>
        </div>
        <AddDevice modalHook={[openAddDeviceModal, setOpenAddDeviceModal]} />
      </div>
      <RoomDevicesView room={currentRoom} devices={devices[currentRoom] || {}} />
      
    </div>
    );
};

export default Dashboard;