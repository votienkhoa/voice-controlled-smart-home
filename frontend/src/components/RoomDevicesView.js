import AirConditionerControls from "./AirConditionerControls";
import AppliancesControls from "./AppliancesControls";
import LightsControls from "./LightsControls";
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