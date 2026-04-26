# tools/cache_client.py
# This file caches API responses
# Meaning — it saves the result on the first API call
# For subsequent identical requests, it retrieves data from the saved file

import json      # For reading/writing JSON files
import os        # For directory management
import hashlib   # For generating unique file names
import requests  # For making API calls


class CachedAPIClient:
    """
    This class acts as an API client but functions intelligently 
    by avoiding redundant requests for the same data.
    """
    
    def __init__(self, cache_dir="cache"):
        # Set the location for the cache directory
        # Data will be saved in the 'cache' folder within the project root
        self.cache_dir = cache_dir
        
        # Create the folder if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        print(f"Cache folder ready: {cache_dir}")
    
    def _make_filename(self, url, params):
        """
        Generate a unique filename for every unique request
        Example: OpenFDA+ibuprofen → abc123.json
        """
        # Combine url and params into a single string
        request_string = json.dumps(
            {"url": url, "params": params or {}},
            sort_keys=True  # Ensure consistent ordering
        )
        
        # Generate an MD5 hash of that string (acting as a unique ID)
        unique_id = hashlib.md5(request_string.encode()).hexdigest()
        
        return os.path.join(self.cache_dir, f"{unique_id}.json")
    
    def get(self, url, params=None):
        """
        Execute API call — but check the cache first
        """
        # Determine the filename for this specific request
        cache_file = self._make_filename(url, params)
        
        # Check if it exists in the cache
        if os.path.exists(cache_file):
            # Found! Read from file, no internet access required
            with open(cache_file, 'r') as f:
                print(f"  [CACHE HIT] Retrieving data from saved file")
                return json.load(f)
        
        # Not in cache — perform a live API call
        print(f"  [API CALL] Fetching data from internet: {url[:50]}...")
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        # Save the result to the cache for future use
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  [SAVED] Data saved to cache folder")
        
        return data


# Instantiate the object to be imported across the project
# The cache folder will be located in the project root
client = CachedAPIClient(cache_dir="cache")