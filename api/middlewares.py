from datetime import datetime
import logging
from django.conf import settings
import os
from django.core.cache import cache
from .tasks import fetch_ip_data


logger = logging.getLogger('api.middlewares')

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
        logger.info(f"Cache hit - IP {ip_address} , path: {path}")

        # Generate a unique cache key per IP address
        cache_key =  f"ip_addr_{ip_address}"
        data = cache.get(cache_key)
        if data:
            # If cached, avoid hitting external API and DB again (performance optimization)
            country = data.get('country')
            city = data.get('city')
            logger.info(f"Cache hit - IP {ip_address} , path: {path},\
                         timestamp: {timestamp}, country: {country}, city: {city}")
        else:
            # If not cached, fetch geolocation data asynchronously using Celery task
            # The task has retries built in to handle temporary request failures
            fetch_ip_data.delay(ip_address, path, timestamp) 

                
        # Pass control to the next middleware/view
        response = self.get_response(request)
        return response

