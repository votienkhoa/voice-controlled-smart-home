import AppliancesControls from "./AppliancesControls.jsx";
import LightsControls from "./LightsControls.jsx";
import DoorsControls from "./DoorsControls.jsx";

const RoomDevicesView = ({ room, devices }) => {
    // Filter out lights and doors, pass the rest as an array to AppliancesControls
    const applianceDevices = Object.entries(devices)
        .filter(([key, value]) => key !== 'light' && key !== 'door' && value && ((Array.isArray(value) && value.length > 0) || (typeof value === 'object' && Object.keys(value).length > 0)))
        .map(([key, value]) => ({ type: key, ...value }));

    const hasAppliances = applianceDevices.length > 0;
    const hasLights = devices.light && ((Array.isArray(devices.light) && devices.light.length > 0) || (typeof devices.light === 'object' && Object.keys(devices.light).length > 0));
    const hasDoors = devices.door && ((Array.isArray(devices.door) && devices.door.length > 0) || (typeof devices.door === 'object' && Object.keys(devices.door).length > 0));

    return (
        <div className="flex flex-col md:flex-row gap-6 w-full">
            {hasAppliances && (
                <div className="md:w-1/2 w-full">
                    <AppliancesControls devices={applianceDevices} />
                </div>
            )}
            <div className="md:w-1/2 w-full flex flex-col gap-6">
                {hasLights && <LightsControls devices={devices.light} room={room} />}
                {hasDoors && <DoorsControls devices={devices.door} room={room} />}
            </div>
        </div>
    )
}

export default RoomDevicesView