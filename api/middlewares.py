# from django.http import HttpResponseForbidden
# from datetime import datetime
# from .models import RequestLog
# import logging
# import requests
# from django.conf import settings
# import os
# from django.core.cache import cache


# # This gets the full file path to where we can log the requests
# full_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../requests.log'))

# # Set up logging
# logging.basicConfig(filename=full_path,
#                     format='%(asctime)s %(message)s',
#                     filemode='a')

# logger = logging.getLogger(__name__)
# handler = logging.StreamHandler()
# handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
# logger.addHandler(handler)
# logger.setLevel(logging.INFO)

# class RequestLogMiddleware:
#     def __init__(self, get_response):
#         """Initialize the get_response that will be called after the request is sent"""
#         self.get_response = get_response
    
#     def __call__(self, request):
#         # Get the IP address from the request
#         x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#         if x_forwarded_for:
#             ip_address = x_forwarded_for.split(',')[0]
#         else:
#             ip_address = request.META.get('REMOTE_ADDR')
   
#         # Get the request path and timestamp
#         timestamp = datetime.now() 
#         path = request.path

#         # Get geolocation data for country and city
#         # Make an API call to the Geolocation service
#         # IPGEO API KEY 
#         # API_KEY = settings.IP_GEOLOCATION_SETTINGS.get('BACKEND_API_KEY')
    
#         # # MAKE the requests
#         # res = requests.get(f"http://api.ipapi.com/{ip_address}?access_key={API_KEY}")
#         # # Check if the response is status code 200
#         # if res.status_code == 200:
#         #     data = res.json()
#         #     ip_address = data['ip']
#         #     country_name = data['country_name']
#         #     city = data['city']

#         #     # Get the IP address from the request

#         #     # Check the cache first, create a unique key that includes the ip to diferenitate each IP address
#         #     cache_key =  f"ip_addr_{ip_address}"
            
#         #     if cache.get(cache_key):
#         #         print("Ip gotten from cache; cache hit")
#         #         logger.info(f"Logged data:Ip address {ip_address} gotten from cache, succssful cache hit")
#         #     else:
#     request_log = RequestLog.objects.filter(ip_address=ip_address)
#     # if request_log.exists():
#         # request_log.update(country=country_name, city=city)
#         # Log the request path, ip_address and timestap to the file
#         logger.info(f"Logged data updated successful - Ip address: {ip_address} request path: {path} timestamp: {timestamp}")

#                     # Cache the results for 24 hours
#                     # cache.set(cache_key, request_log, timeout=86400)

#                 # else:
#             request_log = RequestLog.objects.create(ip_address=ip_address, path=path, timestamp=timestamp)
#             request_log.save()
#             # Log the request path, ip_address and timestap to the file
#             logger.info(f"Logged data successful - Ip address: {ip_address} request path: {path} timestamp: {timestamp}")

#                     # Cache the results for 24 hours
#                     # cache.set(cache_key, request_log, timeout=86400)
        

#         response = self.get_response(request)
#         # Code to be execcuted after the response is returned from the view or call the next middleware

#         return response