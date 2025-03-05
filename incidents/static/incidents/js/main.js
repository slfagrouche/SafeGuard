// Map Configuration
const config = {
  layers: {
    hybrid: 'https://{s}.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}',
    satellite: 'https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    streets: 'https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    terrain: 'https://{s}.google.com/vt/lyrs=p&x={x}&y={y}&z={z}'
  }
};

let map;
let uploadedImageBase64 = null;
let incidents = [];
let markers = [];
let tempMarker = null;
let currentLayer;
let lastClickedLocation = null;

// Initialize tab system
document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM Content Loaded');
  
  // Add click handlers to nav links
  const navLinks = document.querySelectorAll('.nav-link');
  console.log('Nav links found:', navLinks.length);
  
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const tabId = link.getAttribute('data-tab');
      console.log('Tab clicked:', tabId);
      switchTab(tabId);
    });
  });

  // Add radius change handler
  const radiusSelect = document.querySelector('select[class*="rounded-lg"]');
  if (radiusSelect) {
    radiusSelect.addEventListener('change', () => {
      // Reload all markers with new radius
      markers.forEach(marker => marker.remove());
      markers = [];
      loadIncidents();
    });
  }

  // Initialize map first
  if (document.getElementById('leaflet-map')) {
    console.log('Found leaflet-map element');
    
    // Show map container
    const mapSection = document.getElementById('map');
    if (mapSection) {
      console.log('Found map section');
      mapSection.style.display = 'block';
      mapSection.style.visibility = 'visible';
      mapSection.style.opacity = '1';
    }
    
    // Initialize map
    initializeMap();
    
    // Set initial active tab
    const initialActiveTab = document.querySelector('.nav-link.active');
    if (initialActiveTab) {
      const tabId = initialActiveTab.getAttribute('data-tab');
      console.log('Initial active tab:', tabId);
      switchTab(tabId);
    }
    
    // Force map resize after initialization
    setTimeout(() => {
      if (map) {
        console.log('Resizing map');
        map.invalidateSize();
        // Center on default view
        map.setView([0, 0], 2);
      }
    }, 500);
  } else {
    console.error('Could not find leaflet-map element');
  }
});

// Initialize Map
function initializeMap() {
  console.log('Initializing map');
  
  // Create map instance
  map = L.map('leaflet-map', {
    center: [0, 0],
    zoom: 6,
    zoomControl: true,
    attributionControl: false
  });

  // Add default layer (hybrid)
  addGoogleLayer('hybrid');

  // Load existing incidents
  loadIncidents();

  // Force a resize after initialization
  setTimeout(() => {
    map.invalidateSize();
    
    // Add click handler for markers after map is properly sized
    map.on('click', function(e) {
      console.log('Map clicked at:', e.latlng);
      
      // Format coordinates with 6 decimal places
      const lat = parseFloat(e.latlng.lat).toFixed(6);
      const lng = parseFloat(e.latlng.lng).toFixed(6);
      
      // Store clicked location
      lastClickedLocation = { lat, lng, latlng: e.latlng };
      
      // Remove previous temporary marker if it exists
      if (tempMarker) {
        tempMarker.remove();
      }

      // Create a new pin marker at clicked location
      createTempMarker(e.latlng);

      // Try to get country from coordinates
      fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`)
        .then(response => response.json())
        .then(data => {
          if (data.address && data.address.country_code) {
            const countryCode = data.address.country_code.toUpperCase();
            const countrySelect = document.getElementById("incident-country");
            if (Array.from(countrySelect.options).some(opt => opt.value === countryCode)) {
              countrySelect.value = countryCode;
            }
          }
        })
        .catch(error => console.error("Error getting country:", error));
      
      // Pan map to center on clicked location with smooth animation
      map.panTo(e.latlng, { animate: true, duration: 0.5 });
    });
  }, 100);
}

// Add Google Layer
function addGoogleLayer(type) {
  if (currentLayer) {
    map.removeLayer(currentLayer);
  }

  currentLayer = L.tileLayer(config.layers[type], {
    maxZoom: 20,
    subdomains: ['mt0', 'mt1', 'mt2', 'mt3']
  }).addTo(map);
}

// Tab Switching Functionality
function switchTab(tabId) {
  console.log('Switching to tab:', tabId);
  
  // Hide all tab contents first
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.remove('active');
    content.style.display = 'none';
  });

  // Remove active class from all nav links
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.remove('active');
  });

  // Activate selected tab and content
  const selectedTab = document.querySelector(`[data-tab="${tabId}"]`);
  const selectedContent = document.getElementById(tabId);
  const heroSection = document.getElementById('hero-section');

  console.log('Selected tab:', selectedTab);
  console.log('Selected content:', selectedContent);

  if (selectedTab && selectedContent) {
    selectedTab.classList.add('active');
    selectedContent.style.display = 'block';
    
    // Add active class after a brief delay to trigger transition
    setTimeout(() => {
      selectedContent.classList.add('active');
    }, 10);

    // Show/hide hero section based on tab
    if (tabId === 'map') {
      if (heroSection) {
        heroSection.style.display = 'flex';
        setTimeout(() => {
          heroSection.classList.add('active');
        }, 10);
      }
    } else {
      if (heroSection) {
        heroSection.classList.remove('active');
        heroSection.style.display = 'none';
      }
    }

    // If switching to map tab, trigger a resize to fix map rendering
    if (tabId === 'map' && map) {
      map.invalidateSize();
    }
  }
}

// Load incidents
async function loadIncidents() {
  try {
    // Clear existing markers and incidents
    markers.forEach(marker => marker.remove());
    markers = [];
    incidents = [];
    
    const response = await fetch("/api/incidents/");
    const data = await response.json();
    console.log("Loaded incidents:", data);
    
    // Filter out duplicates based on coordinates
    // Sort incidents by datetime in descending order
    const sortedIncidents = data.sort((a, b) => 
      new Date(b.datetime) - new Date(a.datetime)
    );
    
    incidents = sortedIncidents;
    sortedIncidents.forEach(incident => {
      createIncidentMarker({
        lat: incident.latitude,
        lng: incident.longitude,
        dateTime: incident.datetime,
        description: incident.description,
        source: incident.source,
        image_url: incident.image_url,
        verified: Boolean(incident.verified), // Ensure boolean type
        address: incident.address
      });
    });
  } catch (error) {
    console.error("Error loading incidents:", error);
  }
}

// Switch Map Layer
function switchMapLayer() {
  const type = document.getElementById('mapLayer').value;
  addGoogleLayer(type);
}

// Filter incidents
function filterIncidents() {
  const filterValue = document.getElementById('incidentFilter').value;
  const now = new Date();
  const last24Hours = new Date(now - 24 * 60 * 60 * 1000);
  const lastWeek = new Date(now - 7 * 24 * 60 * 60 * 1000);
  const lastMonth = new Date(now - 30 * 24 * 60 * 60 * 1000);
  const last3Months = new Date(now - 90 * 24 * 60 * 60 * 1000);

  markers.forEach(marker => {
    const incident = marker.incident;
    let show = true;
    const incidentDate = new Date(incident.dateTime);

    switch(filterValue) {
      case 'verified':
        show = incident.verified;
        break;
      case 'unverified':
        show = !incident.verified;
        break;
      case 'recent':
        show = incidentDate >= last24Hours;
        break;
      case 'week':
        show = incidentDate >= lastWeek;
        break;
      case 'month':
        show = incidentDate >= lastMonth;
        break;
      case '3months':
        show = incidentDate >= last3Months;
        break;
      default: // 'all'
        show = true;
    }

    if (show) {
      marker.addTo(map);
    } else {
      marker.remove();
    }
  });
}

// Address search handling with automatic form update
async function searchAddress() {
  const address = document.getElementById("incident-address").value.trim();
  if (!address) {
    alert("Please enter an address to search");
    return;
  }

  try {
    const url = `https://nominatim.openstreetmap.org/search?format=json&addressdetails=1&q=${encodeURIComponent(address)}`;
    const response = await fetch(url);
    const data = await response.json();

    if (data && data.length > 0) {
      const location = data[0];
      const lat = parseFloat(location.lat);
      const lng = parseFloat(location.lon);

      // Update form fields
      document.getElementById("incident-lat").value = lat;
      document.getElementById("incident-lng").value = lng;
      
      // Try to set country from address details
      if (location.address && location.address.country_code) {
        const countryCode = location.address.country_code.toUpperCase();
        document.getElementById("incident-country").value = countryCode;
      }

      // Update map view and marker
      map.setView([lat, lng], 6);
      if (tempMarker) {
        tempMarker.remove();
      }
      createTempMarker([lat, lng]);
      
      // Store as last clicked location
      lastClickedLocation = { lat, lng, latlng: L.latLng(lat, lng) };
    } else {
      alert("No location found for this address. Please try a different address or use coordinates.");
    }
  } catch (error) {
    console.error("Error searching address:", error);
    alert("Error searching for address. Please try again or use coordinates directly.");
  }
}

// Manual coordinates handling
function setManualCoordinates() {
  const lat = parseFloat(document.getElementById("manual-lat").value);
  const lng = parseFloat(document.getElementById("manual-lng").value);
  
  if (!isNaN(lat) && !isNaN(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
    map.setView([lat, lng], 6);
    if (tempMarker) {
      tempMarker.remove();
    }
    createTempMarker([lat, lng]);
    document.getElementById("incident-lat").value = lat;
    document.getElementById("incident-lng").value = lng;
  } else {
    alert("Please enter valid coordinates. Latitude must be between -90 and 90, Longitude between -180 and 180.");
  }
}

// Modal management
function openReportModal() {
  const modal = document.getElementById("reportModal");
  
  // Set current datetime as default
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  document.getElementById("incident-datetime").value = now.toISOString().slice(0, 16);
  
  // Set coordinates from last clicked location if available
  if (lastClickedLocation) {
    const latInput = document.getElementById("incident-lat");
    const lngInput = document.getElementById("incident-lng");
    
    if (latInput && lngInput) {
      latInput.value = lastClickedLocation.lat;
      lngInput.value = lastClickedLocation.lng;
    }
  }
  
  // Show the modal
  modal.style.display = "flex";
  modal.style.justifyContent = "center";
  modal.style.alignItems = "center";
  
  // Ensure map is visible and properly sized
  if (map) {
    setTimeout(() => {
      map.invalidateSize();
    }, 100);
  }
}

function closeReportModal() {
  const modal = document.getElementById("reportModal");
  modal.style.display = "none";
  document.getElementById("reportForm").reset();
  document.getElementById("imagePreview").style.display = "none";
  uploadedImageBase64 = null;
}

// CSRF token handling
function getCsrfToken() {
  return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

// Report submission with loading state, S3 upload handling, and address geocoding
async function submitReport(e) {
  e.preventDefault();

  const submitButton = e.target.querySelector('button[type="submit"]');
  const originalButtonText = submitButton.innerHTML;
  
  try {
    // Show loading state
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i>Uploading...';

    const dtValue = document.getElementById("incident-datetime").value.trim();
    const latVal = document.getElementById("incident-lat").value.trim();
    const lngVal = document.getElementById("incident-lng").value.trim();
    const desc = document.getElementById("incident-description").value.trim();
    const sourceLink = document.getElementById("incident-source").value.trim();
    const addressVal = document.getElementById("incident-address").value.trim();
    console.log("Form Values:", {
      dateTime: dtValue,
      description: desc
    });

    if (!dtValue || !desc) {
      console.log("Missing required fields:", {
        dateTime: !dtValue,
        description: !desc
      });
      alert("Please fill in required fields (Date/Time and Description).");
      return;
    }

    let latNum = latVal ? parseFloat(latVal) : null;
    let lngNum = lngVal ? parseFloat(lngVal) : null;

    // If address is provided but no coordinates, try to geocode
    if (addressVal && (!latNum || !lngNum)) {
      try {
        const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(addressVal)}`;
        const response = await fetch(url);
        const data = await response.json();

        if (data && data.length > 0) {
          latNum = parseFloat(data[0].lat);
          lngNum = parseFloat(data[0].lon);
        }
      } catch (error) {
        console.error("Error geocoding address:", error);
      }
    }

    // Require either coordinates or address
    if (!latNum && !lngNum && !addressVal) {
      alert("Please provide either coordinates or an address for the incident location.");
      return;
    }

    const response = await fetch("/report/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({
        dateTime: dtValue,
        latitude: latNum,
        longitude: lngNum,
        description: desc,
        source: sourceLink,
        image: uploadedImageBase64,
        address: addressVal,
      }),
    });

    const data = await response.json();
    if (data.status === "success") {
      // Reload all incidents to show the new one
      loadIncidents();
      alert("Incident submitted successfully!");
      closeReportModal();
    } else {
      alert("Error submitting incident: " + data.message);
    }
  } catch (error) {
    alert("Error submitting incident: " + error);
  } finally {
    // Reset button state
    submitButton.disabled = false;
    submitButton.innerHTML = originalButtonText;
  }
}

// Temporary marker when moving around map
function createTempMarker(latlng) {
  if (tempMarker) tempMarker.remove();

  const markerHtml = `<div class="pin" style="width: 30px; height: 30px; background-color: #8a2be2; border: 2px solid #ffffff; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); box-shadow: 0 0 8px rgba(138, 43, 226, 0.6);"></div>`;
  const icon = L.divIcon({
    className: "custom-marker",
    html: markerHtml,
    iconSize: [30, 30],
    iconAnchor: [15, 30],
  });

  tempMarker = L.marker(latlng, {
    icon: icon,
  }).addTo(map);
}

function createIncidentMarker(incident) {
  const lat = incident.latitude || incident.lat;
  const lng = incident.longitude || incident.lng;
  const address = incident.address;

  // Try to geocode address if no coordinates are available
  if (!lat && !lng && address) {
    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`)
      .then(response => response.json())
      .then(data => {
        if (data && data.length > 0) {
          const location = data[0];
          incident.lat = parseFloat(location.lat);
          incident.lng = parseFloat(location.lon);
          addMarkerToMap(incident);
        }
      })
      .catch(error => console.error("Error geocoding address:", error));
  } else if (lat && lng) {
    addMarkerToMap(incident);
  }

  // Add to sidebar list regardless of coordinates
  addIncidentToSidebar(incident);
}

function addMarkerToMap(incident) {
  let lat = incident.latitude || incident.lat;
  let lng = incident.longitude || incident.lng;
  
  // Check for existing markers at these coordinates
  const existingCount = markers.filter(m => 
    (m.incident.latitude || m.incident.lat) === lat && 
    (m.incident.longitude || m.incident.lng) === lng
  ).length;
  
  // If there are existing markers at this location, offset this one slightly
  if (existingCount > 0) {
    // Add a small offset (about 50 meters) in a circular pattern
    // Create a spiral pattern for multiple markers
    const angle = (2 * Math.PI * existingCount) / 8; // Divide circle into 8 parts
    const spiralDistance = 0.002 * (1 + existingCount * 0.5); // Increase distance with each marker
    lat = lat + (spiralDistance * Math.cos(angle));
    lng = lng + (spiralDistance * Math.sin(angle));
  }

  // Create pin marker HTML with verification badge
  const markerHtml = `
    <div class="pin-container" style="position: relative;">
      <div class="pin" style="
        width: 30px;
        height: 30px;
        background-color: #ff0000;
        border: 2px solid #ffffff;
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        box-shadow: 0 0 12px rgba(255, 0, 0, 0.6);
        position: relative;
      "></div>
      ${incident.verified ? `
        <div style="
          position: absolute;
          top: -5px;
          right: -5px;
          width: 16px;
          height: 16px;
          background: #00c853;
          border: 2px solid white;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 2;
        ">
          <i class="fa-solid fa-check" style="color: white; font-size: 8px; margin-top: -1px;"></i>
        </div>
      ` : `
        <div style="
          position: absolute;
          top: -5px;
          right: -5px;
          width: 16px;
          height: 16px;
          background: #ffc107;
          border: 2px solid white;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 2;
        ">
          <i class="fa-solid fa-clock" style="color: white; font-size: 8px; margin-top: -1px;"></i>
        </div>
      `}
      <div class="pin-shadow" style="
        width: 20px;
        height: 6px;
        background: rgba(0, 0, 0, 0.3);
        border-radius: 50%;
        margin-top: -3px;
        filter: blur(2px);
      "></div>
    </div>`;

  const icon = L.divIcon({
    className: "custom-pin-marker",
    html: markerHtml,
    iconSize: [30, 42],
    iconAnchor: [15, 42],
  });

  const marker = L.marker([lat, lng], {
    icon: icon,
  })
  .addTo(map)
  .on("click", () => openIncidentDetails(incident));
  
  marker.incident = incident;
  markers.push(marker);

  // Add radius circle
  const radiusSelect = document.querySelector('select[class*="rounded-lg"]');
  const radiusKm = parseInt(radiusSelect?.value || 5);
  const radiusMeters = radiusKm * 1000;

  const circle = L.circle([lat, lng], {
    color: "#ff0000",
    fillColor: "#ff0000",
    fillOpacity: 0.1,
    radius: radiusMeters,
    weight: 1,
    stroke: true,
    strokeOpacity: 0.3
  }).addTo(map);

  // Store circle reference for later removal
  marker.circle = circle;
}

// Update map initialization to set higher zoom level
function initializeMap() {
  console.log('Initializing map');
  
  // Create map instance with higher zoom level
  map = L.map('leaflet-map', {
    center: [20, 0], // Center more towards populated areas
    zoom: 3, // Even lower zoom level to show more area
    zoomControl: true,
    attributionControl: false
  });

  // Add default layer (hybrid)
  addGoogleLayer('hybrid');

  // Load existing incidents
  loadIncidents();

  // Force a resize after initialization
  setTimeout(() => {
    map.invalidateSize();
    
    // Add click handler for markers after map is properly sized
    map.on('click', function(e) {
      console.log('Map clicked at:', e.latlng);
      
      // Format coordinates with 6 decimal places
      const lat = parseFloat(e.latlng.lat).toFixed(6);
      const lng = parseFloat(e.latlng.lng).toFixed(6);
      
      // Store clicked location
      lastClickedLocation = { lat, lng, latlng: e.latlng };
      
      // Remove previous temporary marker if it exists
      if (tempMarker) {
        tempMarker.remove();
      }

      // Create a new pin marker at clicked location
      createTempMarker(e.latlng);

      // Try to get country from coordinates
      fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`)
        .then(response => response.json())
        .then(data => {
          if (data.address && data.address.country_code) {
            const countryCode = data.address.country_code.toUpperCase();
            const countrySelect = document.getElementById("incident-country");
            if (Array.from(countrySelect.options).some(opt => opt.value === countryCode)) {
              countrySelect.value = countryCode;
            }
          }
        })
        .catch(error => console.error("Error getting country:", error));
      
      // Pan map to center on clicked location with smooth animation
      map.panTo(e.latlng, { animate: true, duration: 0.5 });
    });
  }, 100);
}

function addIncidentToSidebar(incident) {
  // Removed sidebar functionality
}

// Incident details modal with image loading handling
function openIncidentDetails(incident) {
  document.getElementById("incidentDetailsModal").style.display = "flex";
  document.getElementById("detailsDate").innerText = incident.dateTime;
  
  // Handle location display
  const lat = incident.latitude || incident.lat;
  const lng = incident.longitude || incident.lng;
  const address = incident.address || '';
  const hasCoords = lat && lng;
  const hasAddress = address && address.trim().length > 0;
  
  let locationText;
  let locationLink;
  
  if (hasCoords && hasAddress) {
    locationText = `${address} (${lat}, ${lng})`;
    locationLink = `https://www.google.com/maps?q=${lat},${lng}&z=10`;
  } else if (hasCoords) {
    locationText = `${lat}, ${lng}`;
    locationLink = `https://www.google.com/maps?q=${lat},${lng}&z=10`;
  } else if (hasAddress) {
    locationText = address;
    locationLink = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address)}`;
  } else {
    locationText = 'Location not specified';
    locationLink = null;
  }

  const detailsLocation = document.getElementById("detailsLocation");
  if (locationLink) {
    detailsLocation.innerHTML = `<a href="${locationLink}" target="_blank" class="text-blue-400 hover:text-blue-300">${locationText}</a>`;
  } else {
    detailsLocation.innerText = locationText;
  }
  
  document.getElementById("detailsDescription").innerText = incident.description;

  const detailsImg = document.getElementById("detailsImage");
  
  // Reset image state
  detailsImg.style.display = "none";
  detailsImg.style.opacity = "0";
  detailsImg.src = "";
  
  // Show loading spinner
  const loadingSpinner = document.createElement("div");
  loadingSpinner.className = "loading-spinner";
  loadingSpinner.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
  detailsImg.parentNode.insertBefore(loadingSpinner, detailsImg);

  if (incident.image_url) {
    // Create a new Image object to preload
    const img = new Image();
    
    // Set crossOrigin to handle CORS for S3 URLs
    if (incident.image_url.includes('amazonaws.com')) {
      img.crossOrigin = 'anonymous';
    }
    
    img.onload = function() {
      // Remove loading spinner
      if (loadingSpinner) loadingSpinner.remove();
      
      // Update the actual image element
      detailsImg.src = incident.image_url;
      detailsImg.style.display = "block";
      
      // Fade in the image
      requestAnimationFrame(() => {
        detailsImg.style.transition = "opacity 0.3s ease-in-out";
        detailsImg.style.opacity = "1";
      });
    };
    
    img.onerror = function(error) {
      console.error('Error loading image:', error);
      // Remove loading spinner
      if (loadingSpinner) loadingSpinner.remove();
      
      // Show error state
      document.getElementById('imageError').style.display = 'flex';
      detailsImg.style.display = "none";
    };
    
    // Start loading the image
    img.src = incident.image_url;
  } else {
    // Remove loading spinner
    loadingSpinner.remove();
    // Show placeholder immediately
    detailsImg.src = '/static/incidents/images/placeholder.svg';
    detailsImg.style.display = "block";
    detailsImg.style.opacity = "1";
  }

  const detailsSource = document.getElementById("detailsSource");
  if (incident.source) {
    detailsSource.href = incident.source;
    detailsSource.style.display = "inline";
  } else {
    detailsSource.style.display = "none";
  }

  // Display country
  const detailsCountry = document.getElementById("detailsCountry");
  if (incident.country) {
    const countrySelect = document.getElementById("incident-country");
    const countryOption = Array.from(countrySelect.options).find(option => option.value === incident.country);
    detailsCountry.innerText = countryOption ? countryOption.text : incident.country;
  } else {
    detailsCountry.innerText = "Not specified";
  }

  const verificationStatus = document.getElementById("verificationStatus");
  if (incident.verified) {
    verificationStatus.className = "flex items-center gap-2 p-3 rounded-lg bg-green-500/10 border border-green-500/20";
    verificationStatus.innerHTML = `
      <div class="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center">
        <i class="fa-solid fa-shield-check text-green-400"></i>
      </div>
      <div>
        <p class="text-green-400 font-medium">Verified</p>
        <p class="text-green-400/60 text-sm">This incident has been verified by our team</p>
      </div>
    `;
  } else {
    verificationStatus.className = "flex items-center gap-2 p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20";
    verificationStatus.innerHTML = `
      <div class="w-8 h-8 rounded-full bg-yellow-500/20 flex items-center justify-center">
        <i class="fa-solid fa-clock text-yellow-400"></i>
      </div>
      <div>
        <p class="text-yellow-400 font-medium">Pending Verification</p>
        <p class="text-yellow-400/60 text-sm">This incident is currently being reviewed</p>
      </div>
    `;
  }
}

function closeIncidentDetails() {
  document.getElementById("incidentDetailsModal").style.display = "none";
}

// Image handling with validation and preview
function previewImage(event) {
  const file = event.target.files[0];
  if (file) {
    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      event.target.value = '';
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert('Please select an image smaller than 5MB');
      event.target.value = '';
      return;
    }

    const reader = new FileReader();
    reader.onload = function (e) {
      const preview = document.getElementById("imagePreview");
      preview.src = e.target.result;
      preview.style.display = "block";
      uploadedImageBase64 = e.target.result;
    };
    reader.onerror = function (e) {
      alert('Error reading file: ' + e.target.error);
      event.target.value = '';
    };
    reader.readAsDataURL(file);
  }
}

// Search location from sidebar
function searchLocationFromSidebar() {
  const address = document.getElementById("sidebar-address").value.trim();
  const lat = parseFloat(document.getElementById("sidebar-lat").value);
  const lng = parseFloat(document.getElementById("sidebar-lng").value);

  if (address) {
    // If address is provided, search by address
    searchAddressAndUpdateMap(address);
  } else if (!isNaN(lat) && !isNaN(lng)) {
    // If coordinates are provided, center map on coordinates
    if (lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
      centerMapOnLocation(lat, lng);
    } else {
      alert("Please enter valid coordinates. Latitude must be between -90 and 90, Longitude between -180 and 180.");
    }
  } else {
    alert("Please enter either an address or valid coordinates.");
  }
}

// Search address and update map
async function searchAddressAndUpdateMap(address) {
  try {
    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`;
    const response = await fetch(url);
    const data = await response.json();

    if (data && data.length > 0) {
      const location = data[0];
      const lat = parseFloat(location.lat);
      const lng = parseFloat(location.lon);
      
      // Update sidebar coordinate inputs
      document.getElementById("sidebar-lat").value = lat.toFixed(6);
      document.getElementById("sidebar-lng").value = lng.toFixed(6);
      
      // Center map on location
      centerMapOnLocation(lat, lng);
    } else {
      alert("No location found for this address. Please try a different address or use coordinates.");
    }
  } catch (error) {
    console.error("Error searching address:", error);
    alert("Error searching for address. Please try again or use coordinates directly.");
  }
}

// Center map on location and add temporary marker
function centerMapOnLocation(lat, lng) {
  // Update map view
  map.setView([lat, lng], 12);
  
  // Create temporary marker
  if (tempMarker) {
    tempMarker.remove();
  }
  createTempMarker([lat, lng]);
  
  // Store as last clicked location for report modal
  lastClickedLocation = { lat, lng, latlng: L.latLng(lat, lng) };
}

// Get country name from country code
function getCountryName(countryCode) {
  const countrySelect = document.getElementById("countryFilter");
  const option = Array.from(countrySelect.options).find(opt => opt.value === countryCode);
  return option ? option.text : countryCode;
}

// Filter incidents by country
function filterByCountry() {
  const selectedCountry = document.getElementById("countryFilter").value;
  
  markers.forEach(marker => {
    const incident = marker.incident;
    const show = !selectedCountry || incident.country === selectedCountry;
    
    if (show) {
      marker.addTo(map);
    } else {
      marker.remove();
    }
  });

  // Update sidebar list
  const listContainer = document.getElementById('incidents-list');
  if (listContainer) {
    listContainer.innerHTML = '';
    incidents
      .filter(incident => !selectedCountry || incident.country === selectedCountry)
      .forEach(incident => addIncidentToSidebar(incident));
  }
}

// AI Chat functionality
let isWaitingForResponse = false;
let chatHistory = [];

function openChat(type) {
  const chatModal = document.getElementById('chatModal');
  const chatMessages = document.getElementById('chatMessages');
  const chatTitle = document.getElementById('chatTitle');
  
  // Fetch chat history
  fetchChatHistory();
  
  // Show modal with fade-in animation
  chatModal.style.opacity = '0';
  chatModal.style.display = 'flex';
  requestAnimationFrame(() => {
    chatModal.style.transition = 'opacity 0.3s ease-in-out';
    chatModal.style.opacity = '1';
  });
  
  // Focus input after animation
  setTimeout(() => {
    document.getElementById('messageInput').focus();
  }, 300);
}

function closeChat() {
  const chatModal = document.getElementById('chatModal');
  chatModal.style.opacity = '0';
  setTimeout(() => {
    chatModal.style.display = 'none';
  }, 300);
}

async function fetchChatHistory() {
  try {
    const response = await fetch('/chat/history/');
    const data = await response.json();
    
    if (data.history) {
      chatHistory = data.history;
      const chatMessages = document.getElementById('chatMessages');
      chatMessages.innerHTML = '';
      
      // Add messages with staggered animation
      data.history.forEach((msg, index) => {
        setTimeout(() => {
          addMessage(msg.role, msg.content, false);
        }, index * 100);
      });
    }
  } catch (error) {
    console.error('Error fetching chat history:', error);
  }
}

function formatMarkdown(content) {
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>')
    .replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
    .replace(/`(.*?)`/g, '<code class="bg-blue-500/10 px-1 py-0.5 rounded">$1</code>')
    .replace(/\n/g, '<br>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="text-blue-400 hover:text-blue-300 underline">$1</a>');
}

function addMessage(type, content, animate = true) {
  const chatMessages = document.getElementById('chatMessages');
  const messageDiv = document.createElement('div');
  const isUser = type === 'user';
  
  messageDiv.className = `chat-message ${isUser ? 'user-message' : 'ai-message'} ${animate ? 'animate-fade-in' : ''}`;
  
  const formattedContent = formatMarkdown(content);
  
  messageDiv.innerHTML = `
    <div class="flex items-start gap-4">
      <div class="flex-shrink-0 w-8 h-8 rounded-full ${
        isUser ? 'bg-blue-500/20' : 'bg-blue-500/10'
      } flex items-center justify-center">
        <i class="fa-solid ${
          isUser ? 'fa-user text-blue-400' : 'fa-brain text-blue-400'
        } text-sm"></i>
      </div>
      <div class="flex-1">
        <div class="text-white text-sm leading-relaxed whitespace-pre-wrap">
          ${formattedContent}
        </div>
        <div class="message-time">${formatTimestamp()}</div>
      </div>
    </div>
  `;
  
  chatMessages.appendChild(messageDiv);
  
  // Smooth scroll to bottom
  const scrollOptions = {
    top: chatMessages.scrollHeight,
    behavior: 'smooth'
  };
  chatMessages.scrollTo(scrollOptions);
}

async function sendMessage(event) {
  event.preventDefault();
  
  if (isWaitingForResponse) return;
  
  const messageInput = document.getElementById('messageInput');
  const message = messageInput.value.trim();
  const submitButton = event.target.querySelector('button[type="submit"]');
  const typingIndicator = document.getElementById('typingIndicator');
  
  if (!message) return;
  
  // Clear input and disable
  messageInput.value = '';
  messageInput.disabled = true;
  
  // Add user message to chat
  addMessage('user', message);
  
  // Show loading state
  isWaitingForResponse = true;
  submitButton.disabled = true;
  submitButton.classList.add('opacity-50');
  typingIndicator.style.display = 'block';
  
  try {
    // Send message to backend
    const response = await fetch('/chat/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
      },
      body: JSON.stringify({ message }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    if (data.error) {
      throw new Error(data.error);
    }
    
    // Add AI response to chat
    addMessage('system', data.response || 'I understand your message. Let me help you with that.');
    
  } catch (error) {
    console.error('Chat error:', error);
    addMessage('system', `I apologize, but I encountered an error: ${error.message}. Please try rephrasing your question or try again later.`);
  } finally {
    // Reset all states
    isWaitingForResponse = false;
    submitButton.disabled = false;
    submitButton.classList.remove('opacity-50');
    messageInput.disabled = false;
    typingIndicator.style.display = 'none';
    messageInput.focus();
  }
}

// Add input handling for better UX
document.addEventListener('DOMContentLoaded', () => {
  const messageInput = document.getElementById('messageInput');
  const submitButton = document.querySelector('.send-button');
  
  messageInput?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isWaitingForResponse && messageInput.value.trim()) {
        submitButton.click();
      }
    }
  });
  
  messageInput?.addEventListener('input', () => {
    submitButton.disabled = !messageInput.value.trim();
    submitButton.classList.toggle('opacity-50', !messageInput.value.trim());
  });
});

// Subscribe form
async function subscribeUser(e) {
  e.preventDefault();

  const submitButton = e.target.querySelector('button[type="submit"]');
  const originalButtonText = submitButton.innerHTML;

  try {
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i>Subscribing...';

    const name = document.getElementById("sub-name").value.trim();
    const email = document.getElementById("sub-email").value.trim();
    const addressVal = document.getElementById("sub-address").value.trim();

    if (!name || !email || !addressVal) {
      alert("Please fill in all required fields.");
      return;
    }

    // Geocode the address
    let latitude, longitude;
    try {
      const geocodeUrl = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(addressVal)}`;
      const geocodeResponse = await fetch(geocodeUrl);
      const geocodeData = await geocodeResponse.json();

      if (geocodeData && geocodeData.length > 0) {
        latitude = parseFloat(geocodeData[0].lat);
        longitude = parseFloat(geocodeData[0].lon);
      } else {
        throw new Error("Could not geocode address");
      }
    } catch (error) {
      alert("Could not verify the address location. Please check the address and try again.");
      return;
    }

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
        latitude: latitude,
        longitude: longitude
      }),
    });

    const data = await response.json();
    if (data.status === "success") {
      const radiusSelect = document.querySelector('select[class*="rounded-lg"]');
      const radius = radiusSelect?.value || 5;
      document.getElementById("subscribeForm").reset();
      alert(`Successfully subscribed to alerts! You will receive notifications for incidents within ${radius}km of your location.`);
    } else {
      alert("Error subscribing: " + data.message);
    }
  } catch (error) {
    alert("Error subscribing: " + error);
  } finally {
    submitButton.disabled = false;
    submitButton.innerHTML = originalButtonText;
  }
}
