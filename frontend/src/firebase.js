import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
    apiKey: "AIzaSyCwb6fCM9XD1zF6eFm9PROWp1Cp81o8Qbc",
    authDomain: "kdth-smarthome.firebaseapp.com",
    databaseURL: "https://kdth-smarthome-default-rtdb.asia-southeast1.firebasedatabase.app",
    projectId: "kdth-smarthome",
    storageBucket: "kdth-smarthome.firebasestorage.app",
    messagingSenderId: "844822918951",
    appId: "1:844822918951:web:a4349c072d80f0a31f1b02"
};  

const app = initializeApp(firebaseConfig);

const auth = getAuth(app);

export { auth };
