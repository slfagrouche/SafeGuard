// Country coordinates configuration
const countryCoords = {
  Sudan: [15.5007, 32.5599],
  Palestine: [31.9522, 35.2332],
  Ukraine: [48.3794, 31.1656],
  Other: [0, 0]
};

let map;
let currentCountry = "Sudan";
let uploadedImageBase64 = null;
let incidents = [];
let tempMarker = null;

// Initialize map on window load
window.onload = async function () {
  // Initialize map
  map = L.map("map", {
    attributionControl: false,
  }).setView(countryCoords[currentCountry], 6);

  L.control
    .attribution({
      prefix:
        'Supporting: Palestine & Sudan | © <a href="https://www.openstreetmap.org" target="_blank">OpenStreetMap</a>',
    })
    .addTo(map);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
  }).addTo(map);

  // Load existing incidents
  try {
    const response = await fetch("/api/incidents/");
    const data = await response.json();
    data.forEach((incident) => {
      createIncidentMarker(incident);
    });
  } catch (error) {
    console.error("Error loading incidents:", error);
  }

  // Map click handler
  map.on("click", (e) => {
    const lat = e.latlng.lat.toFixed(6);
    const lng = e.latlng.lng.toFixed(6);
    createTempMarker(e.latlng);
    document.getElementById("incident-lat").value = lat;
    document.getElementById("incident-lng").value = lng;
  });
};


// Country switching functionality
function switchCountry() {
  const selected = document.getElementById("countrySelect").value;
  currentCountry = selected;

  if (map) {
    if (currentCountry === "Other") {
      map.setView([0, 0], 2);
    } else {
      map.setView(countryCoords[currentCountry], 6);
    }
    if (tempMarker) {
      tempMarker.remove();
      tempMarker = null;
    }
  }
}

// Modal management
function openReportModal() {
  document.getElementById("reportModal").style.display = "flex";
}
function closeReportModal() {
  document.getElementById("reportModal").style.display = "none";
  document.getElementById("reportForm").reset();
  document.getElementById("imagePreview").style.display = "none";
  uploadedImageBase64 = null;
}

// CSRF token handling
function getCsrfToken() {
  return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

// Report submission
async function submitReport(e) {
  e.preventDefault();

  const dtValue = document.getElementById("incident-datetime").value.trim();
  const latVal = document.getElementById("incident-lat").value.trim();
  const lngVal = document.getElementById("incident-lng").value.trim();
  const desc = document.getElementById("incident-description").value.trim();
  const sourceLink = document.getElementById("incident-source").value.trim();

  if (!dtValue || !desc) {
    alert("Please fill in required fields (Date/Time and Description).");
    return;
  }

  const latNum = parseFloat(latVal);
  const lngNum = parseFloat(lngVal);

  try {
    const response = await fetch("/report/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({
        dateTime: dtValue,
        lat: latNum,
        lng: lngNum,
        description: desc,
        source: sourceLink,
        image: uploadedImageBase64,
      }),
    });

    const data = await response.json();
    if (data.status === "success") {
      const newIncident = {
        dateTime: dtValue,
        lat: latNum,
        lng: lngNum,
        description: desc,
        source: sourceLink || null,
        image: uploadedImageBase64,
        verified: false,
      };

      incidents.push(newIncident);
      createIncidentMarker(newIncident);
      alert("Incident submitted successfully!");
      closeReportModal();
    } else {
      alert("Error submitting incident: " + data.message);
    }
  } catch (error) {
    alert("Error submitting incident: " + error);
  }
}

// temporary marker when moving around map
function createTempMarker(latlng) {
  if (tempMarker) tempMarker.remove();

  const markerHtml = `<div class="pin"></div>`;
  const icon = L.divIcon({
    className: "custom-marker",
    html: markerHtml,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  });

  tempMarker = L.marker(latlng, {
    icon: icon,
  }).addTo(map);
}

function createIncidentMarker(incident) {
  L.circle([incident.lat, incident.lng], {
    color: "red",
    fillColor: "#f03",
    fillOpacity: 0.5,
    radius: 60000, // Adjust as needed
  })
    .addTo(map)
    .on("click", () => {
      openIncidentDetails(incident);
    });
}

// Incident details modal
function openIncidentDetails(incident) {
  document.getElementById("incidentDetailsModal").style.display = "flex";
  document.getElementById("detailsDate").innerText = incident.dateTime;
  document.getElementById("detailsLocation").innerText = `${incident.lat}, ${incident.lng}`;
  document.getElementById("detailsDescription").innerText = incident.description;

  const detailsImg = document.getElementById("detailsImage");
  if (incident.image) {
    detailsImg.src = incident.image;
    detailsImg.style.display = "block";
  } else {
    detailsImg.style.display = "none";
  }

  const detailsSource = document.getElementById("detailsSource");
  if (incident.source) {
    detailsSource.href = incident.source;
    detailsSource.style.display = "inline";
  } else {
    detailsSource.style.display = "none";
  }

  const verificationStatus = document.getElementById("verificationStatus");
  if (incident.verified) {
    verificationStatus.innerText = "Verified by Developer";
    verificationStatus.className = "verification-badge verified";
  } else {
    verificationStatus.innerText = "Unverified";
    verificationStatus.className = "verification-badge unverified";
  }
}

function closeIncidentDetails() {
  document.getElementById("incidentDetailsModal").style.display = "none";
}

// Image handling
function previewImage(event) {
  const file = event.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function (e) {
      const preview = document.getElementById("imagePreview");
      preview.src = e.target.result;
      preview.style.display = "block";
      uploadedImageBase64 = e.target.result;
    };
    reader.readAsDataURL(file);
  }
}

// Address suggestions
const addressInput = document.getElementById("incident-address");
const suggestionsDiv = document.getElementById("address-suggestions");
let suggestTimeout = null;

addressInput.addEventListener("input", () => {
  const query = addressInput.value.trim();
  if (query.length < 3) {
    suggestionsDiv.style.display = "none";
    return;
  }

  if (suggestTimeout) clearTimeout(suggestTimeout);
  suggestTimeout = setTimeout(() => {
    fetchSuggestions(query);
  }, 400);
});

async function fetchSuggestions(query) {
  const url = `https://nominatim.openstreetmap.org/search?format=json&limit=5&q=${encodeURIComponent(
    query
  )}`;
  try {
    const response = await fetch(url);
    const data = await response.json();
    renderSuggestions(data);
  } catch (error) {
    console.error("Error fetching suggestions:", error);
  }
}

function renderSuggestions(data) {
  if (!data || !data.length) {
    suggestionsDiv.style.display = "none";
    return;
  }

  suggestionsDiv.innerHTML = data
    .map(
      (item) => `
      <div onclick="selectAddress('${item.display_name}', ${item.lat}, ${item.lon})">
        ${item.display_name}
      </div>
    `
    )
    .join("");

  suggestionsDiv.style.display = "block";
}

window.selectAddress = function (address, lat, lng) {
  addressInput.value = address;
  suggestionsDiv.style.display = "none";
  document.getElementById("incident-lat").value = lat;
  document.getElementById("incident-lng").value = lng;
};

// Coordinates toggle
function toggleCoordinates() {
  const coordinatesInput = document.getElementById("coordinatesInput");
  coordinatesInput.style.display =
    coordinatesInput.style.display === "block" ? "none" : "block";
}

// Subscribe form
async function subscribeUser(e) {
  e.preventDefault();

  const name = document.getElementById("sub-name").value.trim();
  const email = document.getElementById("sub-email").value.trim();
  const addressVal = document.getElementById("sub-address").value.trim();

  if (!name || !email || !addressVal) {
    alert("Please fill in all required fields.");
    return;
  }

  try {
    const response = await fetch("/subscribe/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({
        name: name,
        email: email,
        address: addressVal,
        latitude: document.getElementById("sub-lat").value,
        longitude: document.getElementById("sub-lng").value,
      }),
    });

    const data = await response.json();
    if (data.status === "success") {
      document.getElementById("subscribeForm").reset();
      document.getElementById("successMessage").style.display = "block";
      setTimeout(() => {
        document.getElementById("successMessage").style.display = "none";
      }, 3000);
    } else {
      alert("Error subscribing: " + data.message);
    }
  } catch (error) {
    alert("Error subscribing: " + error);
  }
}
