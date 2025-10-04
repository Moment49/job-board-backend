from django.http import HttpResponseForbidden
from datetime import datetime
from .models import RequestLog
import logging
import requests
from django.conf import settings
import os
from django.core.cache import cache


# This gets the full file path to where we can log the requests
full_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../logs/requests.log'))

# Set up logging
logging.basicConfig(filename=full_path,
                    format='%(asctime)s %(message)s',
                    filemode='a')

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class RequestLogMiddleware:
    def __init__(self, get_response):
        """
        Initialize middleware.
        get_response is a callable (the next middleware or the view) 
        that will be called once this middleware finishes.
        """
        self.get_response = get_response
    

    def get_ip_address(self, request):
        """
        Extract client IP address from the request headers.
        
        - If behind a proxy/load balancer, IP is usually in HTTP_X_FORWARDED_FOR.
        - Otherwise, fallback to REMOTE_ADDR (direct client IP).
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            # Take the first IP if multiple IPs are forwarded (comma-separated list)
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get("REMOTE_ADDR")
        
        return ip_address
    
    def __call__(self, request):
        """
        Main middleware execution flow:
        - Runs before the view
        - Executes custom logic
        - Calls the next middleware/view
        - Runs after the response is generated
        """
        
        # Get client IP
        ip_address = self.get_ip_address(request)
        
        # Get request path and timestamp
        timestamp = datetime.now() 
        path = request.get_full_path()

        # --- Geolocation lookup (using ipapi API) ---
        API_KEY = settings.IP_GEOLOCATION_SETTINGS.get('BACKEND_API_KEY')
    
       
        res = requests.get(f"http://api.ipapi.com/{ip_address}?access_key={API_KEY}")

        # Ensure API call succeeded (implement retries for the api call - later)
        if res.status_code == 200:
            data = res.json()
            ip_address = data['ip']
            country_name = data['country_name']
            city = data['city']

            # Build unique cache key per IP
            cache_key =  f"ip_addr_{ip_address}"
            
            if cache.get(cache_key):
                # If cached, skip re-logging heavy data and just update DB
                logger.info(f"Cache hit - IP {ip_address} data retrieved from cache.")
                request_log = RequestLog.objects.filter(ip_address=ip_address)
                if request_log.exists():
                    request_log.update(country=country_name, city=city, path=path)

            else:
                # If not cached, fetch or create DB log entry
                request_log = RequestLog.objects.filter(ip_address=ip_address)
                if request_log.exists():
                    # Update record if already logged before
                    request_log.update(country=country_name, city=city)
                    logger.info(f"Updated log - IP: {ip_address}, Path: {path}, Timestamp: {timestamp}")
                else:
                    # Create a new request log entry
                    request_log = RequestLog.objects.create(ip_address=ip_address, 
                                                            path=path, timestamp=timestamp, 
                                                            country=country_name, city=city)
                    request_log.save()
                    logger.info(f"New log created - IP: {ip_address}, Path: {path}, Timestamp: {timestamp}")

                    # Store results in cache for 1 hour (3600 seconds)
                    cache.set(cache_key, request_log, timeout=3600)
                
         # Pass control to the next middleware/view
        response = self.get_response(request)

        # Code to be execcuted after the response is returned from the view or call the next middleware
        return response

