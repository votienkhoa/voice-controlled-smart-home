import React, { useEffect, useState } from 'react';
import { fetchDevices } from '../api';

const DeviceList = () => {
    const [devices, setDevices] = useState([]);

    useEffect(() => {
        const getDevices = async () => {
            const data = await fetchDevices();
            setDevices(data);
        };
        getDevices();
    }, []);

    return (
        <div>
            <h2>Device List</h2>
            <ul>
                {devices.length > 0 ? (
                    devices.map(device => (
                        <li key={device.id}>{device.name} - {device.status}</li>
                    ))
                ) : (
                    <li>No devices found.</li>
                )}
            </ul>
        </div>
    );
};

export default DeviceList;