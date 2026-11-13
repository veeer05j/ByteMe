import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import rawData from './map_data.json'; // Make sure this ends in .json

// FIX: Make pins visible
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Math formula to calculate distance in meters
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

// Convert GeoJSON to our app format
const clinicsData = rawData.features.map((feature, index) => {
  // THE FIX: Read the tags correctly based on how OpenStreetMap exports GeoJSON
  const props = feature.properties.tags || feature.properties || {};
  
  // Get the exact type from the data
  let rawType = props.amenity || props.shop || props.healthcare || "clinic";
  
  // Make sure "chemist" counts as "pharmacy" and "doctors" counts as "clinic"
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
export default function MapView() {
  const [userLocation, setUserLocation] = useState(null);
  const [statusMessage, setStatusMessage] = useState("");
  const [isArrived, setIsArrived] = useState(false);
  
  // NEW: State for the category filter
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
        } else {
          setStatusMessage(`You are ${Math.round(distance)} meters away from ${clinic.name}.`);
        }
      },
      () => setStatusMessage("Please allow location access."),
      { enableHighAccuracy: true }
    );
  };

  // NEW: Filter the data based on the selected category
  const filteredData = clinicsData.filter(clinic => {
    if (selectedCategory === "all") return true;
    // Basic check to match the OpenStreetMap tags
    return clinic.type.includes(selectedCategory); 
  });

  return (
    <div style={{ height: "100vh", width: "100vw", display: "flex", flexDirection: "column", position: "relative" }}>
      
      {/* HEADER & FILTERS */}
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, zIndex: 1000, backgroundColor: "white", padding: "16px", boxShadow: "0 4px 6px rgba(0,0,0,0.1)" }}>
        
        <h2 style={{ margin: 0, fontSize: "20px", fontWeight: "bold", textAlign: "center", color: "#1e3a8a" }}>
          Nearby Health Services
        </h2>

        {/* CATEGORY BUTTONS */}
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
                fontSize: "12px"
              }}
            >
              {cat === "all" ? "All" : cat + "s"}
            </button>
          ))}
        </div>

        {/* STATUS MESSAGE */}
        {statusMessage && (
          <div style={{ marginTop: "12px", padding: "8px", textAlign: "center", borderRadius: "8px", fontSize: "14px", fontWeight: "bold", backgroundColor: isArrived ? "#dcfce7" : "#dbeafe", color: isArrived ? "#166534" : "#1e40af" }}>
            {statusMessage}
          </div>
        )}
      </div>

      {/* MAP */}
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

          {/* RENDER FILTERED DATA */}
          {filteredData.map((clinic) => {
            if (!clinic.latitude || !clinic.longitude) return null; 

            return (
              <Marker key={clinic.id} position={[clinic.latitude, clinic.longitude]}>
                <Popup>
                  <div style={{ textAlign: "center", minWidth: "180px" }}>
                    <strong style={{ display: "block", fontSize: "14px", color: "#1e3a8a" }}>{clinic.name}</strong>
                    <span style={{ fontSize: "12px", color: "#4b5563", textTransform: "capitalize" }}>{clinic.type}</span>
                    
                    <button 
                      onClick={() => checkLocationToClinic(clinic)}
                      style={{ marginTop: "8px", width: "100%", backgroundColor: "#2563eb", color: "white", padding: "8px", borderRadius: "6px", border: "none", fontWeight: "bold", cursor: "pointer" }}
                    >
                      📍 Check My Location
                    </button>
                  </div>
                </Popup>
              </Marker>
            );
          })}

          {userLocation && (
            <Circle 
              center={[userLocation.lat, userLocation.lng]} 
              radius={30} 
              pathOptions={{ color: 'blue', fillColor: 'blue', fillOpacity: 0.6 }} 
            />
          )}
        </MapContainer>
      </div>
    </div>
  );
}