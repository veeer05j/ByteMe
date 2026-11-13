import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import rawData from './map_data.json'; // Make sure your file is named exactly this

// 1. FIX: Make the map pins visible in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// 2. Math formula to calculate distance in meters
function getDistanceInMeters(lat1, lon1, lat2, lon2) {
  const R = 6371e3; 
  const dLat = (lat2 - lat1) * (Math.PI / 180);
  const dLon = (lon2 - lon1) * (Math.PI / 180);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c; 
}

// 3. Convert OpenStreetMap GeoJSON to our App's format
const clinicsData = rawData.features.map((feature, index) => {
  const props = feature.properties.tags || feature.properties || {};
  let rawType = props.amenity || props.shop || props.healthcare || "clinic";
  
  if (rawType === "chemist") rawType = "pharmacy";
  if (rawType === "doctors") rawType = "clinic";

  return {
    id: index,
    name: props.name || "Unnamed Health Facility",
    type: rawType.toLowerCase(), 
    latitude: feature.geometry.coordinates[1],
    longitude: feature.geometry.coordinates[0],
    address: props['addr:street'] || props['addr:city'] || "Mauritius",
    openingHours: props.opening_hours || "Hours not listed"
  };
});

// 4. Accept setActiveTab from App.jsx
export default function MapView({ setActiveTab }) {
  const [userLocation, setUserLocation] = useState(null);
  const [statusMessage, setStatusMessage] = useState("");
  const [isArrived, setIsArrived] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState("all");

  const checkLocationToClinic = (clinic) => {
    setStatusMessage("Locating...");
    setIsArrived(false);

    if (!navigator.geolocation) {
      setStatusMessage("GPS not supported.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        setUserLocation({ lat: latitude, lng: longitude });

        const distance = getDistanceInMeters(
          latitude, longitude, clinic.latitude, clinic.longitude
        );

        if (distance <= 100) { 
          setStatusMessage(`🎉 You have arrived at ${clinic.name}!`);
          setIsArrived(true);
          
          // AUTOMATION: Switch to the Chat tab after 2.5 seconds to greet them
          setTimeout(() => {
            // Save the arrival so the Chat can read it
            localStorage.setItem('lastArrivedClinic', clinic.name);
            setActiveTab("chat"); 
          }, 2500); 

        } else {
          setStatusMessage(`You are ${Math.round(distance)} meters away from ${clinic.name}.`);
        }
      },
      () => setStatusMessage("Please allow location access."),
      { enableHighAccuracy: true }
    );
  };

  // 5. Filter based on the selected button
  const filteredData = clinicsData.filter(clinic => {
    if (selectedCategory === "all") return true;
    return clinic.type.includes(selectedCategory); 
  });

  return (
    <div style={{ height: "100vh", width: "100vw", display: "flex", flexDirection: "column", position: "relative" }}>
      
      {/* --- HEADER & FILTERS --- */}
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, zIndex: 1000, backgroundColor: "white", padding: "16px", boxShadow: "0 4px 6px rgba(0,0,0,0.1)", borderBottomLeftRadius: "16px", borderBottomRightRadius: "16px" }}>
        
        <h2 style={{ margin: 0, fontSize: "20px", fontWeight: "bold", textAlign: "center", color: "#1e3a8a" }}>
          Nearby Health Services
        </h2>

        {/* Category Buttons */}
        <div style={{ display: "flex", justifyContent: "center", gap: "8px", marginTop: "12px", flexWrap: "wrap" }}>
          {["all", "pharmacy", "clinic", "hospital"].map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              style={{
                padding: "6px 12px",
                borderRadius: "20px",
                border: "1px solid #2563eb",
                backgroundColor: selectedCategory === cat ? "#2563eb" : "white",
                color: selectedCategory === cat ? "white" : "#2563eb",
                fontWeight: "bold",
                textTransform: "capitalize",
                cursor: "pointer",
                fontSize: "12px",
                transition: "all 0.2s ease"
              }}
            >
              {cat === "all" ? "All" : cat + "s"}
            </button>
          ))}
        </div>

        {/* Status Message (Shows when checking GPS) */}
        {statusMessage && (
          <div style={{ marginTop: "12px", padding: "8px", textAlign: "center", borderRadius: "8px", fontSize: "14px", fontWeight: "bold", backgroundColor: isArrived ? "#dcfce7" : "#dbeafe", color: isArrived ? "#166534" : "#1e40af" }}>
            {statusMessage}
          </div>
        )}
      </div>

      {/* --- MAP CONTAINER --- */}
      <div style={{ flex: 1, width: "100%", marginTop: "130px" }}>
        <MapContainer 
          center={[-20.2188, 57.4961]} 
          zoom={11} 
          style={{ height: "100%", width: "100%", zIndex: 0 }}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          />

          {/* Render filtered pins */}
          {filteredData.map((clinic) => {
            if (!clinic.latitude || !clinic.longitude) return null; 

            return (
              <Marker key={clinic.id} position={[clinic.latitude, clinic.longitude]}>
                <Popup>
                  <div style={{ textAlign: "center", minWidth: "180px", paddingBottom: "5px" }}>
                    <strong style={{ display: "block", fontSize: "15px", color: "#1e3a8a", marginBottom: "2px" }}>{clinic.name}</strong>
                    <span style={{ fontSize: "12px", color: "#6b7280", textTransform: "capitalize" }}>{clinic.type}</span>

                    {/* GPS Check Button */}
                    <button 
                      onClick={() => checkLocationToClinic(clinic)}
                      style={{ marginTop: "10px", width: "100%", backgroundColor: "#2563eb", color: "white", padding: "8px", borderRadius: "6px", border: "none", fontWeight: "bold", cursor: "pointer", fontSize: "13px" }}
                    >
                      📍 Check My Location
                    </button>
                  </div>
                </Popup>
              </Marker>
            );
          })}

          {/* Show User Location as a Blue Dot */}
          {userLocation && (
            <Circle 
              center={[userLocation.lat, userLocation.lng]} 
              radius={30} 
              pathOptions={{ color: '#2563eb', fillColor: '#2563eb', fillOpacity: 0.6 }} 
            />
          )}
        </MapContainer>
      </div>
    </div>
  );
}