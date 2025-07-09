<template>
    <div class="device-management-container">
      <h2>Device Management</h2>
      <button @click="showAddDeviceModal = true">Add New Device</button>
      
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Device ID</th>
            <th>Name</th>
            <th>Product</th>
            <th>Status</th>
            <th>Firmware</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
            <tr v-for="device in devices" :key="device.id">
              <td>{{ device.id }}</td>
              <td>{{ device.device_id }}</td>
              <td>{{ device.device_name }}</td>
              <td>{{ device.product_id }}</td>
              <td>{{ device.status }}</td>
              <td>{{ device.firmware_version || 'N/A' }}</td>
              <td>
                <button @click="controlDevice(device.device_id)">Control</button>
                <button @click="showUpgradeModal(device)">Upgrade Firmware</button>
                <button @click="deleteDevice(device.id)">Delete</button>
              </td>
            </tr>
        </tbody>
      </table>

      <!-- Add Dvice Modal -->>
      <div v-if="showAddDeviceModal" class="modal">
        <h3>Add Device</h3>
        <form @submit.prevent="addDevice">
          <input type="text" v-model="newDevice.device_id" placeholder="DeviceUnique ID" required />
          <input type="text" v-model="newDevice.device_name" placeholder="DeviceName" required />
          <input type="text" v-model="newDevice.product_id" placeholder="ProductID" required />
          <button type="submit">Add</button>
          <button type="button" @click="showAddDeviceModal = false">Cancel</button>
        </form>
      </div>

      <!-- Firmware Upgrade Modal -->>
      <div v-if="showFirmwareUpgradeModal" class="modal">
        <h3>Upgrade Firmware for {{ selectedDevice.device_name }}</h3>
        <select v-model="selectedFirmwareId">
          <option v-for="fw in availableFirmwares" :key="fw.id" :value="fw.id">
            {{ fw.version }} (Product: {{ fw.product_id }})
          </option>
        </select>
        <button @click="initiateFirmwareUpgrade">Initiate Upgrade</button>
        <button @click="showFirmwareUpgradeModal = false">Cancel</button>
      </div>
    
    </div>
  </template>
  
  <script>
  import { ref, onMounted } from 'vue'
  import { getDevice, createDevice, deleteDevice, controlDevice, getFirmwares, initiateUpgradeTask} from '@/api/modules/devices';
 
  export default {
    name: 'DeviceManagement',
    setup() {
      const devices = ref([]);
      const showAddDeviceModal = ref(false);
      const newDevice = ref({device_id:'', device_name: '', product_id: ''});
      const showFirmwareUpgradeModal = ref(false);
      const selectedDevice = ref(null);
      const availableFirmwares = ref([]);
      const selectedFirmwareId = ref(null);
  
      const fetchDevices = async () => {
        try {
          devices.value = await getDevice();
        } catch (error) {
          console.error("Error fetching devices:", error);
        }
      };

      const addDevices = async () => {
        try {
          await createDevice(newDevice.value);
          await fetchDevices();
          showAddDeviceModal.value = false;
          newDevice.value = { device_id: '', device_name: '', product_id: '' };
        } catch (error) {
          console.error("Error adding devices:", error);
        }
      };

      const deleteDevices = async () => {
        if (confirm('Are you sure you want to delete this devices?')){
          try {
            await deleteDevice(id);
            await fetchDevices();
          } catch (error) {
            console.error("Error deleting devices:", error);
          }
        }
      };

      const controlDevices = async () => {
        const command = prompt('Enter command for device(e.g., {"light":"on"})');
        if (command){
          try {
            await controlDevice(deviceId, JSON.parse(command));
            alert('Command sent!');
          } catch (error) {
            console.error("Error sending command:", error);
            alert('Failed to send command.');
          }
        }
      };
      
      const showUpgradeModal = async (device) => {
        selectedDevice.value = device;
        availableFirmwares.value = await getFirmwares(device.product_id); // 获取该产品线所有固件
        if (availableFirmwares.value.length > 0) {
          selectedFirmwareId.value = availableFirmwares.value[0].id;
        }
        showFirmwareUpgradeModal.value = true;
      };

      const initiateFirmwareUpgrade = async () => {
        if (!selectedDevice.value || !selectedFirmwareId.value) return;
          try {
            await initiateUpgradeTask(selectedDevice.value.id,selectedFirmwareId.value);
            alert('Firmware upgrade initiated!');
            showFirmwareUpgradeModal.value = false;
        } catch (error) {
          console.error('Error initiating upgrade:', error);
          alert('Failed to initiate upgrade.');
        }
      };
      
      onMounted(fetchDevices);

      return {
        devices,
        showAddDeviceModal,
        newDevice,
        showFirmwareUpgradeModal,
        selectedDevice,
        availableFirmwares,
        selectedFirmwareId,
        fetchDevices,
        addDevice,
        deleteDevice,
        controlDevice,
        showUpgradeModal,
        initiateFirmwareUpgrade,
      };
    },
  };
  </script>
  
  <style>
  /*样式省略*/
  </style>