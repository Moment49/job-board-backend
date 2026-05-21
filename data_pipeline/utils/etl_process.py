import requests
import os
import logging
import time
import functools


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


def retry(max_retries, delay):
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



@retry(max_retries=3, delay=2)
def fetch_single_page(page_num):
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
            res_data = fetch_single_page(page_num)

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

        # Add a delay between page requests to avoid hitting rate limits
        if page_num > 1:
            time.sleep(2)  
       
    
