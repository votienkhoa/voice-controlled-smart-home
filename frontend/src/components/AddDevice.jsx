import { Modal } from "flowbite-react"

const AddDevice = ({ modalHook }) => {
    const [openModal, setOpenModal] = modalHook

    const toggleAdvancedSettings = () => {
        const advancedSettings = document.getElementById('advanced-settings');
        advancedSettings.style.display = advancedSettings.style.display === 'none' ? 'block' : 'none';
    }

    const cancel = () => {
        window.location.href = '/devices';
    }

    return (
        <div className="justify-center text-center">
            <Modal show={openModal} onClose={() => setOpenModal(false)}>
                <Modal.Header>Add New Device</Modal.Header>
                <form id="add-device-form" className="space-y-4">
                <Modal.Body>
            
                <h2 className="text-xl font-semibold text-gray-700">Device Details</h2>
                
                <label for="device-name" className="block text-gray-700 font-medium">Device Name</label>
                <input type="text" id="device-name" className="w-full p-2 border rounded-md" placeholder="Enter device name" required />
                
                <label for="device-type" className="block text-gray-700 font-medium">Device Type</label>
                <select id="device-type" className="w-full p-2 border rounded-md" required>
                    <option value="">Select type</option>
                    <option value="sensor">Sensor</option>
                    <option value="actuator">Actuator</option>
                    <option value="camera">Camera</option>
                </select>
                
                <label for="device-id" className="block text-gray-700 font-medium">Device ID</label>
                <input type="text" id="device-id" className="w-full p-2 border rounded-md" placeholder="Enter unique device ID" required />

                <label for="location" className="block text-gray-700 font-medium">Location</label>
                <input type="text" id="location" className="w-full p-2 border rounded-md" placeholder="Enter device location" />

                <label for="firmware-version" className="block text-gray-700 font-medium">Firmware Version</label>
                <input type="text" id="firmware-version" className="w-full p-2 border rounded-md" placeholder="Enter firmware version" />

                <label className="block text-gray-700 font-medium">Connection Type</label>
                <div className="flex space-x-4">
                    <div><input type="radio" id="wifi" name="connection-type" value="Wi-Fi" required /><label for="wifi" className="ml-2">Wi-Fi</label></div>
                    <div><input type="radio" id="ethernet" name="connection-type" value="Ethernet" /><label for="ethernet" className="ml-2">Ethernet</label></div>
                    <div><input type="radio" id="cellular" name="connection-type" value="Cellular" /><label for="cellular" className="ml-2">Cellular</label></div>
                </div>

                <div className="border p-4 rounded-md bg-gray-100">
                    <button type="button" className="text-blue-500" onclick="toggleAdvancedSettings()">Show Advanced Settings</button>
                    <div id="advanced-settings" className="hidden mt-4">
                        <h3 className="text-lg font-semibold">Advanced Settings</h3>
                        <label for="security-protocol" className="block text-gray-700 font-medium">Security Protocol</label>
                        <select id="security-protocol" className="w-full p-2 border rounded-md">
                            <option value="TLS">TLS</option>
                            <option value="SSL">SSL</option>
                            <option value="None">None</option>
                        </select>

                        <label for="data-rate" className="block text-gray-700 font-medium">Data Rate (kbps)</label>
                        <input type="number" id="data-rate" className="w-full p-2 border rounded-md" placeholder="Enter data rate in kbps" />

                        <label for="custom-attributes" className="block text-gray-700 font-medium">Custom Attributes</label>
                        <textarea id="custom-attributes" className="w-full p-2 border rounded-md" placeholder="Enter any custom attributes in JSON format"></textarea>
                    </div>
                </div>

                <h3 className="text-lg font-semibold">Configuration Options</h3>
                <div className="flex flex-col space-y-2">
                    <div><input type="checkbox" id="enable-notifications" className="mr-2" /><label for="enable-notifications">Enable Notifications</label></div>
                    <div><input type="checkbox" id="auto-update" className="mr-2" /><label for="auto-update">Auto-Update Firmware</label></div>
                </div>
                </Modal.Body>
                <Modal.Footer>
                <div className="flex space-x-4 mt-4">
                    <button type="submit" className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700">Add Device</button>
                    <button type="button" className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700" onClick={() => setOpenModal(false)}>Cancel</button>
                </div>
                </Modal.Footer>
            </form>
                
            </Modal>
        </div>
    )
}

export default AddDevice