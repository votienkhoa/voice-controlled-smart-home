import React, { useEffect, useState } from 'react';
import { database } from '../config/firebase';
import { ref, onValue } from 'firebase/database';

const DeviceList = () => {
    const [devices, setDevices] = useState([]);

    useEffect(() => {
        const devicesRef = ref(database, 'devices');
        const unsubscribe = onValue(devicesRef, (snapshot) => {
            const data = snapshot.val();
            if (!data) {
                setDevices([]);
                return;
            }
            // Flatten all devices from all rooms
            const allDevices = [];
            Object.entries(data).forEach(([room, roomDevices]) => {
                Object.entries(roomDevices).forEach(([type, value]) => {
                    // If the value is an array, add each item
                    if (Array.isArray(value)) {
                        value.forEach((device, idx) => {
                            allDevices.push({
                                room,
                                type,
                                ...device,
                                key: `${room}-${type}-${idx}`
                            });
                        });
                    } else if (typeof value === 'object') {
                        allDevices.push({
                            room,
                            type,
                            ...value,
                            key: `${room}-${type}`
                        });
                    }
                });
            });
            setDevices(allDevices);
        });
        return () => unsubscribe();
    }, []);

    return (
        <div className="p-4 bg-gray-900 text-white min-h-screen">
            <h2 className="text-2xl font-bold mb-6">Device List</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {devices.length > 0 ? (
                    devices.map(device => (
                        <div key={device.key} className="bg-gray-800 p-4 rounded-lg shadow flex flex-col gap-2">
                            <div className="text-lg font-semibold text-white mb-1">
                                {device.name ? device.name : `${device.type.charAt(0).toUpperCase() + device.type.slice(1)}`}
                            </div>
                            <div className="text-gray-400 text-sm mb-1">
                                <span className="font-medium">Room:</span> {device.room}
                            </div>
                            <div className="text-gray-400 text-sm mb-1">
                                <span className="font-medium">Type:</span> {device.type}
                            </div>
                            {Object.entries(device).map(([key, value]) => (
                                !['key', 'room', 'type', 'name'].includes(key) && (
                                    <div key={key} className="text-gray-300 text-sm">
                                        <span className="font-medium capitalize">{key}:</span> {String(value)}
                                    </div>
                                )
                            ))}
                        </div>
                    ))
                ) : (
                    <div className="bg-gray-800 p-4 rounded-lg text-gray-400">No devices found.</div>
                )}
            </div>
        </div>
    );
};

export default DeviceList;