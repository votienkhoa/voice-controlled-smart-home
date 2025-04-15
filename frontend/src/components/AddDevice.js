import { useState } from "react"
import { Modal } from "flowbite-react"

const AddDevice = ({ modalHook }) => {
    const [openModal, setOpenModal] = modalHook

    const toggleAdvancedSettings = () => {
        const advancedSettings = document.getElementById('advanced-settings');
        advancedSettings.style.display = advancedSettings.style.display === 'none' ? 'block' : 'none';
    }

    const cancel = () => {
        // Logic to handle cancel action, e.g., redirect to devices page
        window.location.href = '/devices';
    }

    return (
        <div class="justify-center text-center">
            <Modal show={openModal} onClose={() => setOpenModal(false)}>
                <Modal.Header>Add New Device</Modal.Header>
                <form id="add-device-form" class="space-y-4">
                <Modal.Body>
            
                <h2 class="text-xl font-semibold text-gray-700">Device Details</h2>
                
                <label for="device-name" class="block text-gray-700 font-medium">Device Name</label>
                <input type="text" id="device-name" class="w-full p-2 border rounded-md" placeholder="Enter device name" required />
                
                <label for="device-type" class="block text-gray-700 font-medium">Device Type</label>
                <select id="device-type" class="w-full p-2 border rounded-md" required>
                    <option value="">Select type</option>
                    <option value="sensor">Sensor</option>
                    <option value="actuator">Actuator</option>
                    <option value="camera">Camera</option>
                </select>
                
                <label for="device-id" class="block text-gray-700 font-medium">Device ID</label>
                <input type="text" id="device-id" class="w-full p-2 border rounded-md" placeholder="Enter unique device ID" required />

                <label for="location" class="block text-gray-700 font-medium">Location</label>
                <input type="text" id="location" class="w-full p-2 border rounded-md" placeholder="Enter device location" />

                <label for="firmware-version" class="block text-gray-700 font-medium">Firmware Version</label>
                <input type="text" id="firmware-version" class="w-full p-2 border rounded-md" placeholder="Enter firmware version" />

                <label class="block text-gray-700 font-medium">Connection Type</label>
                <div class="flex space-x-4">
                    <div><input type="radio" id="wifi" name="connection-type" value="Wi-Fi" required /><label for="wifi" class="ml-2">Wi-Fi</label></div>
                    <div><input type="radio" id="ethernet" name="connection-type" value="Ethernet" /><label for="ethernet" class="ml-2">Ethernet</label></div>
                    <div><input type="radio" id="cellular" name="connection-type" value="Cellular" /><label for="cellular" class="ml-2">Cellular</label></div>
                </div>

                <div class="border p-4 rounded-md bg-gray-100">
                    <button type="button" class="text-blue-500" onclick="toggleAdvancedSettings()">Show Advanced Settings</button>
                    <div id="advanced-settings" class="hidden mt-4">
                        <h3 class="text-lg font-semibold">Advanced Settings</h3>
                        <label for="security-protocol" class="block text-gray-700 font-medium">Security Protocol</label>
                        <select id="security-protocol" class="w-full p-2 border rounded-md">
                            <option value="TLS">TLS</option>
                            <option value="SSL">SSL</option>
                            <option value="None">None</option>
                        </select>

                        <label for="data-rate" class="block text-gray-700 font-medium">Data Rate (kbps)</label>
                        <input type="number" id="data-rate" class="w-full p-2 border rounded-md" placeholder="Enter data rate in kbps" />

                        <label for="custom-attributes" class="block text-gray-700 font-medium">Custom Attributes</label>
                        <textarea id="custom-attributes" class="w-full p-2 border rounded-md" placeholder="Enter any custom attributes in JSON format"></textarea>
                    </div>
                </div>

                <h3 class="text-lg font-semibold">Configuration Options</h3>
                <div class="flex flex-col space-y-2">
                    <div><input type="checkbox" id="enable-notifications" class="mr-2" /><label for="enable-notifications">Enable Notifications</label></div>
                    <div><input type="checkbox" id="auto-update" class="mr-2" /><label for="auto-update">Auto-Update Firmware</label></div>
                </div>
                </Modal.Body>
                <Modal.Footer>
                <div class="flex space-x-4 mt-4">
                    <button type="submit" class="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700">Add Device</button>
                    <button type="button" class="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700" onClick={() => setOpenModal(false)}>Cancel</button>
                </div>
                </Modal.Footer>
            </form>
                
            </Modal>
        </div>
    )
}

export default AddDevice