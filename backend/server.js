const express = require('express');
const mqtt = require('mqtt');

const app = express();
const port = 3000;

const mqttServer = "mqtt://127.0.0.1:1883"; // Thay bằng IP MQTT server thực tế
const mqttTopicCommand = "home/command"; // Topic gửi lệnh
const mqttTopicStatus = "home/status"; // Topic nhận trạng thái
const client = mqtt.connect(mqttServer, { clientId: "NodeJS_API" });

let latestStatus = {
  dht11_temp: null,
  dht11_hum: null,
  mq2: null
};

var admin = require("firebase-admin");
var serviceAccount = require("./kdth-smarthome-firebase-adminsdk-fbsvc-058365873e.json");

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  databaseURL: "https://kdth-smarthome-default-rtdb.asia-southeast1.firebasedatabase.app"
});

client.on('connect', () => {
  console.log('Connected to MQTT broker');
  client.subscribe([mqttTopicCommand, mqttTopicStatus], { qos: 0 }, (err) => {
    if (err) {
      console.log("Failed to subscribe:", err);
    } else {
      console.log(`Subscribed to topics: ${mqttTopicCommand}, ${mqttTopicStatus}`);
    }
  });
});

client.on('error', (err) => {
  console.log('MQTT error:', err);
});

client.on('close', () => {
  console.log('MQTT connection closed');
});

client.on('message', (topic, message) => {
  if (topic === mqttTopicStatus) {
    const msg = message.toString();
    console.log(`Status: ${msg}`);
    if (msg.startsWith("dht11_temp:")) {
      latestStatus.dht11_temp = parseFloat(msg.substring(11));
    } else if (msg.startsWith("dht11_hum:")) {
      latestStatus.dht11_hum = parseFloat(msg.substring(10));
    } else if (msg.startsWith("mq2:")) {
      latestStatus.mq2 = parseFloat(msg.substring(4));
    }
  }
});

app.use(express.json()); // Parse JSON body

// LED control
app.post('/led/:id/:state', (req, res) => {
  const id = req.params.id;
  const state = req.params.state.toUpperCase();
  if (id >= 1 && id <= 3 && (state === 'ON' || state === 'OFF')) {
    const command = `device:led${id},state:${state}`;
    client.publish(mqttTopicCommand, command, { qos: 0 }, (err) => {
      if (err) {
        res.status(500).json({ error: 'Failed to publish MQTT message' });
      } else {
        res.json({ message: `LED ${id} turned ${state}` });
      }
    });
  } else {
    res.status(400).json({ error: 'Invalid LED ID (1-3) or state (on/off)' });
  }
});

// Servo control
app.post('/servo/:id/angle/:value', (req, res) => {
  const id = req.params.id;
  const angle = parseInt(req.params.value);
  if (id >= 1 && id <= 2 && angle >= 0 && angle <= 180) {
    const command = `device:servo${id},angle:${angle}`;
    client.publish(mqttTopicCommand, command, { qos: 0 }, (err) => {
      if (err) {
        res.status(500).json({ error: 'Failed to publish MQTT message' });
      } else {
        res.json({ message: `Servo ${id} set to ${angle} degrees` });
      }
    });
  } else {
    res.status(400).json({ error: 'Invalid servo ID (1-2) or angle (0-180)' });
  }
});

// DHT11 read
app.get('/dht11/:type', (req, res) => {
  const type = req.params.type.toLowerCase();
  if (type === 'temp' || type === 'hum') {
    const command = `device:dht11,action:read_${type}`;
    client.publish(mqttTopicCommand, command, { qos: 0 }, (err) => {
      if (err) {
        res.status(500).json({ error: 'Failed to publish MQTT message' });
      } else {
        res.json({ message: `Requested ${type} from DHT11` });
      }
    });
  } else {
    res.status(400).json({ error: 'Invalid type (temp/hum)' });
  }
});

// MQ-2 read
app.get('/mq2', (req, res) => {
  const command = "device:mq2,action:read";
  client.publish(mqttTopicCommand, command, { qos: 0 }, (err) => {
    if (err) {
      res.status(500).json({ error: 'Failed to publish MQTT message' });
    } else {
      res.json({ message: 'Requested MQ-2 reading' });
    }
  });
});

// Main door control
app.post('/door/:state', (req, res) => {
  const state = req.params.state.toUpperCase();
  if (state === 'ON' || state === 'OFF') {
    const command = `MAIN_DOOR_${state}`;
    client.publish(mqttTopicCommand, command, { qos: 0 }, (err) => {
      if (err) {
        res.status(500).json({ error: 'Failed to publish MQTT message' });
      } else {
        res.json({ message: `Door set to ${state}` });
      }
    });
  } else {
    res.status(400).json({ error: 'Invalid state (on/off)' });
  }
});

// Update device in Firebase Realtime Database
app.post('/update-device', async (req, res) => {
  const { room, type, data } = req.body;
  if (!room || !type || typeof data !== 'object') {
    return res.status(400).json({ error: 'room, type, and data are required in the request body' });
  }
  try {
    await admin.database().ref(`devices/${room}/${type}`).set(data);
    res.json({ message: `Device ${type} in room ${room} updated successfully` });
  } catch (err) {
    res.status(500).json({ error: 'Failed to update device in Firebase', details: err.message });
  }
});

app.get('/', (req, res) => {
  res.json({ message: 'Smart Home API' });
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
