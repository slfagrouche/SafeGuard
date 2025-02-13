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
    const uniqueIncidents = data.filter((incident, index, self) =>
      index === self.findIndex(i => 
        i.latitude === incident.latitude && i.longitude === incident.longitude
      )
    );
    
    incidents = uniqueIncidents;
    uniqueIncidents.forEach(incident => {
      createIncidentMarker({
        lat: incident.latitude,
        lng: incident.longitude,
        dateTime: incident.datetime,
        description: incident.description,
        source: incident.source,
        image_url: incident.image_url,
        verified: incident.verified,
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
    const countryVal = document.getElementById("incident-country").value.trim();

    console.log("Form Values:", {
      dateTime: dtValue,
      description: desc,
      country: countryVal
    });

    if (!dtValue || !desc || !countryVal) {
      console.log("Missing required fields:", {
        dateTime: !dtValue,
        description: !desc,
        country: !countryVal
      });
      alert("Please fill in required fields (Date/Time, Description, and Country).");
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
        country: countryVal
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
  const lat = incident.latitude || incident.lat;
  const lng = incident.longitude || incident.lng;

  // Check if marker already exists at these coordinates
  const existingMarker = markers.find(m => 
    (m.incident.latitude || m.incident.lat) === lat && 
    (m.incident.longitude || m.incident.lng) === lng
  );
  
  if (existingMarker) return;

  const marker = L.circle([lat, lng], {
    color: "#ff0000",
    fillColor: "#ff0000",
    fillOpacity: incident.verified ? 0.4 : 0.2,
    radius: 15000,
    weight: incident.verified ? 2 : 1,
    stroke: true,
    strokeOpacity: 0.8
  })
  .addTo(map)
  .on("click", () => openIncidentDetails(incident));
  
  marker.incident = incident;
  markers.push(marker);
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
  if (incident.image_url) {
    detailsImg.src = incident.image_url;
    detailsImg.style.display = "block";
    
    // Add loading indicator
    detailsImg.style.opacity = "0.5";
    detailsImg.onload = function() {
      detailsImg.style.opacity = "1";
    };
    detailsImg.onerror = function() {
      detailsImg.src = '/static/incidents/images/placeholder.svg';
      detailsImg.style.opacity = "1";
    };
  } else {
    detailsImg.src = '/static/incidents/images/placeholder.svg';
    detailsImg.style.display = "block";
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
function openChat(type) {
  alert(`Opening ${type} chat... This feature is coming soon!`);
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
      }),
    });

    const data = await response.json();
    if (data.status === "success") {
      document.getElementById("subscribeForm").reset();
      alert("Successfully subscribed to alerts!");
    } else {
      alert("Error subscribing: " + data.message);
    }
  } catch (error) {
    alert("Error subscribing: " + error);
  }
}
