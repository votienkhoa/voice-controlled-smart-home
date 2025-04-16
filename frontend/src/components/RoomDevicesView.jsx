import AirConditionerControls from "./AirConditionerControls.jsx";
import AppliancesControls from "./AppliancesControls.jsx";
import LightsControls from "./LightsControls.jsx";
import { useEffect } from "react";

const RoomDevicesView = ({room}) => {

    useEffect(() => {
        // get devices of room here
    }, [room])

    return (
        <>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <AirConditionerControls />
            <AppliancesControls />
        </div>
        <LightsControls />
        </>
    )
}

export default RoomDevicesView