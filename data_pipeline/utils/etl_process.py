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
  

def rate_limit(max_requests, time_window_secs):
    def decorator_rate_limit(func):
        request_count = 0
        request_timestamps = []

        @functools.wraps(func)
        def wrapper_rate_limit(*args, **kwargs):
            nonlocal request_count, request_timestamps
            current_time = datetime.now()
            # Format as YYYY-MM-DD HH:MM:SS,milliseconds
            request_log_timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
            if request_timestamps:
                if (current_time - request_timestamps[0]) < timedelta(seconds=time_window_secs) and request_count >= max_requests:
                    logger.info(f"Max requests reached. Please wait before making more requests. log_timestamp: {request_log_timestamp}, request_count: {request_count}")
                    time.sleep(20)

                    # Reset the request count and timestamps after the time window has passed
                    request_count = 0
                    request_timestamps = []
                    print(request_count)

            # Call the function and get the result
            result = func(*args, **kwargs)

            # Update the request count and timestamps
            if request_count < max_requests:
                request_timestamps.append(current_time)
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
@rate_limit(max_requests=5, time_window_secs=30)
def fetch_page(page_num):
    """Fetch a single page of data from the external API."""

    # Get the API URL from environment variables
    API_URL = os.getenv('EXTERNAL_API_URL')
    res = requests.get(f"{API_URL}?page={page_num}", timeout=10)

    # Ensures HTTP errors trigger retry
    res.raise_for_status()
    return res.json()



@timer
def call_external_api():
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



    
