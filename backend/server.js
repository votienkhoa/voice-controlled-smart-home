const express = require('express');
const mqtt = require('mqtt');

const app = express();
const port = 3000;

const mqttServer = "mqtt://127.0.0.1:1883";
const mqttTopic = "home/led";
const client = mqtt.connect(mqttServer);


client.on('connect', function () {
  console.log('Connected to MQTT broker');
  client.subscribe(mqttTopic, { qos: 0 }, function (err) {
    if (err) {
      console.log("Failed to subscribe to topic:", err);
    } else {
      console.log(`Subscribed to topic: ${mqttTopic}`);
    }
  });
});

client.on('error', function (err) {
  console.log('MQTT connection error:', err);
});

client.on('close', function () {
  console.log('MQTT connection closed');
});

client.on('message', (topic, message) => {
  if (topic === mqttTopic) {
    console.log(`Received message: ${message.toString()}`);
  }
});

app.get('/led/:state', (req, res) => {
  const state = req.params.state;
  if (state === "on" || state === "off") {
    client.publish(mqttTopic, state.toUpperCase(), function (err) {
      if (err) {
        res.status(500).send("Error publishing MQTT message");
      } else {
        res.send(`LED turned ${state.toUpperCase()}`);
      }
    });
  } else {
    res.status(400).send("Invalid state. Use 'on' or 'off'");
  }
});

app.get('/', (req, res) => {
  res.send('Welcome to the Smart Home API!');
});

app.listen(port, () => {
    console.log("Server is running on port " + port);
});
