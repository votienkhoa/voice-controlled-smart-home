const express = require('express');
const mqtt = require('mqtt');
const admin = require("firebase-admin");
const serviceAccount = require("./kdth-smarthome-firebase-adminsdk-fbsvc-058365873e.json");
const { getAuth } = require("firebase-admin/auth");

const app = express();
const port = 3000;

const mqttServer = "mqtt://127.0.0.1:1883"; 
const mqttTopicCommand = "home/command"; 
const mqttTopicStatus = "home/status";
const client = mqtt.connect(mqttServer, { clientId: "NodeJS_API" });

let latestStatus = {
  dht11_temp: null,
  dht11_hum: null,
  mq2: null
};

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  databaseURL: "https://kdth-smarthome-default-rtdb.asia-southeast1.firebasedatabase.app"
});

// Middleware to verify Firebase Auth token and attach user info
async function authenticateToken(req, res, next) {
  // const authHeader = req.headers['authorization'];
  // if (!authHeader || !authHeader.startsWith('Bearer ')) {
  //   return res.status(401).json({ error: 'No token provided' });
  // }
  // const token = authHeader.split(' ')[1];
  // try {
  //   const decodedToken = await getAuth().verifyIdToken(token);
  //   req.user = decodedToken;
  //   next();
  // } catch (err) {
  //   return res.status(403).json({ error: 'Invalid or expired token' });
  // }
}

// Helper to check if user can control a room
async function canControlRoom(uid, room) {
  const ref = admin.database().ref(`userAccess/${uid}`);
  const snapshot = await ref.once('value');
  const allowedRooms = snapshot.val();
  if (!allowedRooms) return false;
  return allowedRooms.includes(room);
}

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
    // Example message formats:
    // "guestroom_door:open" or "guestroom_door:closed"
    // "livingroom_light:1" or "livingroom_light:0"
    // "livingroom_temp:25.5"
    // "livingroom_hum:60"
    // "masterbedroom_gas:100"

    // Door status (Guest Room)
    if (msg.startsWith("guestroom_door:")) {
      const open = msg.split(":")[1] === "open";
      admin.database().ref('devices/Guest Room/door/open').set(open);
    }
    // Light status (Guest Room)
    else if (msg.startsWith("guestroom_light:")) {
      const status = parseInt(msg.split(":")[1]);
      admin.database().ref('devices/Guest Room/light/status').set(status);
    }
    // Door status (Master Bedroom)
    else if (msg.startsWith("masterbedroom_door:")) {
      const open = msg.split(":")[1] === "open";
      admin.database().ref('devices/Master Bedroom/door/open').set(open);
    }
    // Light status (Master Bedroom)
    else if (msg.startsWith("masterbedroom_light:")) {
      const status = parseInt(msg.split(":")[1]);
      admin.database().ref('devices/Master Bedroom/light/status').set(status);
    }
    // Gas sensor (Master Bedroom)
    else if (msg.startsWith("masterbedroom_gas:")) {
      const value = parseFloat(msg.split(":")[1]);
      admin.database().ref('devices/Master Bedroom/Gas Sensor/value').set(value);
    }
    // Light status (Living Room)
    else if (msg.startsWith("livingroom_light:")) {
      const status = parseInt(msg.split(":")[1]);
      admin.database().ref('devices/Living Room/light/status').set(status);
    }
    // Temp (Living Room)
    else if (msg.startsWith("livingroom_temp:")) {
      const temp = parseFloat(msg.split(":")[1]);
      admin.database().ref('devices/Living Room/Temperature & Humidity Sensor/temp').set(temp);
    }
    // Humidity (Living Room)
    else if (msg.startsWith("livingroom_hum:")) {
      const humid = parseFloat(msg.split(":")[1]);
      admin.database().ref('devices/Living Room/Temperature & Humidity Sensor/humid').set(humid);
    }
    // Add more parsing as needed for other rooms/devices
  }
});

app.use(express.json()); // Parse JSON body

// LED control
app.post('/led/:id/:state', authenticateToken, async (req, res) => {
  const id = req.params.id;
  const state = req.params.state.toUpperCase();
  const room = req.body.room; // Expect room in body
  if (!room) return res.status(400).json({ error: 'Room is required' });
  if (!(await canControlRoom(req.user.uid, room))) {
    return res.status(403).json({ error: 'Not authorized to control this room' });
  }
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
app.post('/servo/:id/angle/:value', authenticateToken, async (req, res) => {
  const id = req.params.id;
  const angle = parseInt(req.params.value);
  const room = req.body.room;
  if (!room) return res.status(400).json({ error: 'Room is required' });
  if (!(await canControlRoom(req.user.uid, room))) {
    return res.status(403).json({ error: 'Not authorized to control this room' });
  }
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
app.post('/door/:state', authenticateToken, async (req, res) => {
  const state = req.params.state.toUpperCase();
  const room = req.body.room;
  if (!room) return res.status(400).json({ error: 'Room is required' });
  if (!(await canControlRoom(req.user.uid, room))) {
    return res.status(403).json({ error: 'Not authorized to control this room' });
  }
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
app.post('/update-device', authenticateToken, async (req, res) => {
  const { room, type, data } = req.body;
  if (!room || !type || typeof data !== 'object') {
    return res.status(400).json({ error: 'room, type, and data are required in the request body' });
  }
  if (!(await canControlRoom(req.user.uid, room))) {
    return res.status(403).json({ error: 'Not authorized to control this room' });
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
