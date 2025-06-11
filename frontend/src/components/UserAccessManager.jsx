import { useEffect, useState } from "react";
import { ref, onValue, set } from "firebase/database";
import { database } from "../config/firebase";
import { getAuth } from "firebase/auth";

const UserAccessManager = () => {
  const [users, setUsers] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [userAccess, setUserAccess] = useState({});
  const [selectedUser, setSelectedUser] = useState("");
  const [selectedRooms, setSelectedRooms] = useState([]);
  const [status, setStatus] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);

  // Check if the user is an admin
  useEffect(() => {
    const auth = getAuth();
    const unsubscribe = auth.onAuthStateChanged(async (firebaseUser) => {
      if (firebaseUser) {
        // Check if user is admin (by custom claim or by uid)
        // Example: check if email is 'admin@...' or uid is in a hardcoded list
        // Replace this logic with your actual admin check
        if (firebaseUser.email === "johnyrodrick@gmail.com") {
          setIsAdmin(true);
        } else {
          setIsAdmin(false);
        }
      } else {
        setIsAdmin(false);
      }
    });
    return () => unsubscribe();
  }, []);

  // Fetch users, rooms, and userAccess from Firebase
  useEffect(() => {
    // Fetch users (assume users are stored under /users/{uid}/email)
    const usersRef = ref(database, "users");
    onValue(usersRef, (snapshot) => {
      const data = snapshot.val() || {};
      const userList = Object.entries(data).map(([uid, info]) => ({
        uid,
        email: info.email || uid,
      }));
      setUsers(userList);
    });
    // Fetch rooms
    const roomsRef = ref(database, "rooms");
    onValue(roomsRef, (snapshot) => {
      const data = snapshot.val() || {};
      setRooms(Object.keys(data));
    });
    // Fetch userAccess
    const accessRef = ref(database, "userAccess");
    onValue(accessRef, (snapshot) => {
      setUserAccess(snapshot.val() || {});
    });
  }, []);

  // When user is selected, update selectedRooms
  useEffect(() => {
    if (selectedUser && userAccess[selectedUser]) {
      setSelectedRooms(userAccess[selectedUser]);
    } else {
      setSelectedRooms([]);
    }
  }, [selectedUser, userAccess]);

  const handleRoomToggle = (room) => {
    setSelectedRooms((prev) =>
      prev.includes(room) ? prev.filter((r) => r !== room) : [...prev, room]
    );
  };

  const handleSave = async () => {
    if (!selectedUser) return;
    await set(ref(database, `userAccess/${selectedUser}`), selectedRooms);
    setStatus("Access updated!");
    setTimeout(() => setStatus(""), 2000);
  };

  if (!isAdmin) {
    return null;
  }

  return (
    <div className="p-4 bg-gray-900 text-white rounded-lg max-w-xl mx-auto mt-8">
      <h2 className="text-2xl font-bold mb-4">User Access Manager</h2>
      <div className="mb-4">
        <label className="block mb-2">Select User:</label>
        <div className="relative">
          <select
            className="appearance-none text-black p-2 rounded w-full border-2 border-blue-500 focus:border-blue-700 focus:ring-2 focus:ring-blue-200 transition-all duration-200 shadow-md bg-gradient-to-r from-blue-100 to-blue-200 hover:from-blue-200 hover:to-blue-100 outline-none"
            value={selectedUser}
            onChange={(e) => setSelectedUser(e.target.value)}
          >
            <option value="">-- Select a user --</option>
            {users.map((user) => (
              <option key={user.uid} value={user.uid}>
                {user.email}
              </option>
            ))}
          </select>
          <span className="pointer-events-none absolute right-3 top-1/2 transform -translate-y-1/2 text-blue-700 text-lg">▼</span>
        </div>
      </div>
      {selectedUser && (
        <div className="mb-4">
          <label className="block mb-2">Allowed Rooms:</label>
          <div className="flex flex-wrap gap-2">
            {rooms.map((room) => (
              <label key={room} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={selectedRooms.includes(room)}
                  onChange={() => handleRoomToggle(room)}
                />
                {room}
              </label>
            ))}
          </div>
        </div>
      )}
      <button
        className="bg-blue-600 px-4 py-2 rounded text-white mt-2"
        onClick={handleSave}
        disabled={!selectedUser}
      >
        Save Access
      </button>
      {status && <div className="mt-2 text-green-400">{status}</div>}
    </div>
  );
};

export default UserAccessManager;
