// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getDatabase } from "firebase/database";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyCwb6fCM9XD1zF6eFm9PROWp1Cp81o8Qbc",
    authDomain: "kdth-smarthome.firebaseapp.com",
    projectId: "kdth-smarthome",
    storageBucket: "kdth-smarthome.firebasestorage.app",
    messagingSenderId: "844822918951",
    appId: "1:844822918951:web:a4349c072d80f0a31f1b02",
    databaseURL: "https://kdth-smarthome-default-rtdb.asia-southeast1.firebasedatabase.app"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const database = getDatabase(app);