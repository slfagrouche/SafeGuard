from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from django.conf import settings
import time

class GeocodingManager:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="flow_alerts")
        self.max_retries = 3
        self.retry_delay = 1  # seconds

    def geocode_address(self, address):
        """
        Convert an address string to latitude and longitude coordinates.
        
        Args:
            address (str): The address to geocode
            
        Returns:
            tuple: (latitude, longitude) if successful, (None, None) if failed
        """
        for attempt in range(self.max_retries):
            try:
                # Attempt to geocode the address
                location = self.geolocator.geocode(address)
                
                if location:
                    return location.latitude, location.longitude
                    
                print(f"Address not found: {address}")
                return None, None
                
            except GeocoderTimedOut:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                print(f"Geocoding timed out for address: {address}")
                
            except GeocoderServiceError as e:
                print(f"Geocoding service error for address {address}: {str(e)}")
                return None, None
                
            except Exception as e:
                print(f"Unexpected error geocoding address {address}: {str(e)}")
                return None, None
                
        return None, None

# Create a singleton instance
geocoding_manager = GeocodingManager()
