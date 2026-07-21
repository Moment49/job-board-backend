import requests
import os
import logging
import functools
from datetime import datetime, timedelta
import time



logger = logging.getLogger('data_pipeline.utils.etl_process')


# Decorator to time the execution of the function
def timer(func):
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        # Check the time to run the api call and log the execution time
        start_time = time.perf_counter()
        results = func(*args, **kwargs)
        for data in results:
            yield data
        end_time = time.perf_counter()
        run_time = end_time - start_time

        # Log the execution time of the call_external_api function
        logger.info(f"Execution time for {func.__name__}: {run_time:.4f} seconds")
    return wrapper_timer
  

def rate_limit(max_requests, time_window):
    def decorator_rate_limit(func):
        request_count = 0
        request_timestamps = []
        request_log_timestamp = []  # List to store the timestamp of each request for logging purposes

        @functools.wraps(func)
        def wrapper_rate_limit(*args, **kwargs):
            # Use nonlocal to modify the request_count and request_timestamps variables defined in the enclosing scope
            nonlocal request_count, request_timestamps, request_log_timestamp

            # Get the current time and format it for logging
            current_time = datetime.now()

            # Format as YYYY-MM-DD HH:MM:SS,milliseconds 
            request_log_timestp = current_time.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

            if request_timestamps:
                # Check if the requests in the current time window exceed the max_requests limit
                if (current_time - request_timestamps[0]) < timedelta(seconds=time_window) and request_count >= max_requests:
                    logger.info(f"Max requests reached. Please wait before making more requests. log_timestamp: {request_log_timestp}, request_count: {request_count}")
                    time.sleep(20)

                    # Reset the request count and timestamps after the time window has passed
                    request_count = 0
                    request_timestamps = []
        
            # Call the function
            result = func(*args, **kwargs)

            # Append the request  timestamp and increment the count
            if request_count < max_requests:
                request_timestamps.append(current_time)
                request_log_timestamp.append(request_log_timestp)
                
                # Log the request count and timestamp for each request
                logger.info(f"Request made at {request_log_timestp}. Request count: {request_count}")
                request_count += 1

            return result
        return wrapper_rate_limit
    return decorator_rate_limit


def retry_on_failure(max_retries, delay):
    def decorator_retry_on_failure(func):

        @functools.wraps(func)
        def wrapper_retry_on_failure(*args, **kwargs):
            attempts = 0
            current_delay = delay
            while attempts < max_retries:
                try:
                    result = func(*args, **kwargs)
                    return result
                except (requests.exceptions.ConnectionError,
                        requests.exceptions.Timeout,
                        requests.exceptions.RequestException,
                        requests.exceptions.HTTPError) as e:

                    attempts += 1
                    logger.error(
                        f"[{func.__name__}] failed (attempt {attempts}/{max_retries}): {e}"
                    )
                    if attempts >= max_retries:
                        raise e
                  
                    time.sleep(current_delay)
                    current_delay *= 2  # Exponential backoff
        return wrapper_retry_on_failure
    return decorator_retry_on_failure



@retry_on_failure(max_retries=3, delay=2)
@rate_limit(max_requests=5, time_window=60)
def fetch_page(page_num):
    """Fetch a single page of data from the external API."""

    # Get the API URL from environment variables
    API_URL = os.getenv('EXTERNAL_API_URL')
    res = requests.get(f"{API_URL}?page={page_num}", timeout=10)
    
    # Ensures HTTP errors trigger retry
    res.raise_for_status()

    return res.json()


@timer
def extract_jobs_from_arbeitnow():
    """"
    Generator function that calls an external API and yeilds the Json response.
    """
    max_pages = 10
    page_num = 1

    while page_num <= max_pages:
        logger.info(f"Fetching page {page_num}")
        try:
            # Fetch the single page
            res_data = fetch_page(page_num)
           

            # Filter the data for the required fields and yield the data
            data = res_data.get('data', [])

            # Check if data is not empty and yield the data
            if not data:
                logger.warning(f"No data found for page {page_num}")
                break
            
            yield data

        except Exception as e:
            logger.error(f"Unexpected error on page {page_num}: {e}")
            
        page_num += 1



def transform_load_jobs(job_page_data):
    """
    Transform the job page data to match the JobPost model fields.
    The transform job function will take the job_page_data as response and will be called in the etl run command for each generator page data.
    """
    api_source = os.getenv('API_SOURCE')
    logger.info(f"Transforming job data from {api_source}...")
    return job_page_data

    


    
