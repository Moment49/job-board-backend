import requests
import os

# utils/etl_process.py
def call_external_api():
    """"
    A function that calls an external API and returns the Json response.
    """
    # Fetch the API URL from environment variables
    api_url = os.getenv('EXTERNAL_API_URL') # Implement Request signature for api call(security)

    # Make a api call to url
    response = requests.get(api_url)

    # Return the json data
    data = response.json()
    
    print(data['data'])
    
