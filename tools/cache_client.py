# tools/cache_client.py
# এই file টা API responses cache করে রাখে
# মানে — প্রথমবার API call হলে result save করে
# পরের বার same request আসলে saved file থেকে দেয়

import json      # JSON file read/write করার জন্য
import os        # folder তৈরি করার জন্য
import hashlib   # unique file name তৈরি করার জন্য
import requests  # API call করার জন্য


class CachedAPIClient:
    """
    এই class টা API client এর মতো কাজ করে
    কিন্তু এটা smart — একই request দুইবার করে না
    """
    
    def __init__(self, cache_dir="cache"):
        # cache folder কোথায় থাকবে সেটা set করো
        # project root থেকে 'cache' folder এ save হবে
        self.cache_dir = cache_dir
        
        # folder না থাকলে তৈরি করো
        os.makedirs(cache_dir, exist_ok=True)
        print(f"Cache folder ready: {cache_dir}")
    
    def _make_filename(self, url, params):
        """
        প্রতিটি unique request এর জন্য unique filename তৈরি করো
        যেমন: OpenFDA+ibuprofen → abc123.json
        """
        # url আর params কে একসাথে string বানাও
        request_string = json.dumps(
            {"url": url, "params": params or {}},
            sort_keys=True  # সবসময় same order এ রাখো
        )
        
        # সেই string এর MD5 hash নাও (unique ID এর মতো)
        unique_id = hashlib.md5(request_string.encode()).hexdigest()
        
        return os.path.join(self.cache_dir, f"{unique_id}.json")
    
    def get(self, url, params=None):
        """
        API call করো — কিন্তু আগে cache check করো
        """
        # এই request এর জন্য file name কী হবে?
        cache_file = self._make_filename(url, params)
        
        # Cache-এ আছে কিনা দেখো
        if os.path.exists(cache_file):
            # আছে! File থেকে পড়ো, internet-এ যাওয়া লাগবে না
            with open(cache_file, 'r') as f:
                print(f"  [CACHE HIT] Saved file থেকে data নিচ্ছি")
                return json.load(f)
        
        # Cache-এ নেই — real API call করো
        print(f"  [API CALL] Internet থেকে data আনছি: {url[:50]}...")
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        # Result টা cache-এ save করো future use এর জন্য
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  [SAVED] cache folder-এ save হলো")
        
        return data


# এই একটা object বানাও এবং সব জায়গায় import করো
# cache folder project root এ থাকবে
client = CachedAPIClient(cache_dir="cache")