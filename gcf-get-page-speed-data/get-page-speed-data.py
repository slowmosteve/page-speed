import os
from collections import defaultdict
import json
import requests
import time
import base64
from google.cloud import pubsub
from google.cloud import datastore

def get_page_speed_data(request):
    """Cloud function that requests page speed report from webpagetest.org for a given URL
    then calls the publish_data function to send to Pub/Sub
    """

    # configure webpagetest
    api_key = os.environ.get("web_page_test_api_key")

    # configure pubsub
    publisher = pubsub.PublisherClient()
    topic_name = "projects/{project_id}/topics/{topic}".format(
        project_id=os.getenv("gcp_project"),
        topic=os.getenv("gcp_topic"),
    )

    # define a function for publishing to Pub/Sub
    def publish_data(test_url, test_type, test_results):
        """Cloud function that publishes a message to a Pub/Sub topic

        Args:
            test_url: The URL that the report was requested for
            test_type: Specifies uncached first view or cached repeat view
            test_results: A json object with the test results 

        """
        print("sending to Pub/Sub")
        result = defaultdict(list)
        result["test_url"] = test_url
        result["test_date"] = time.strftime("%Y-%m-%d")
        result["test_type"] = test_type
        field_list = test_results.keys()
        for field in field_list:
            field = field.replace(".","_")
            field = field.replace("-","_")
            result[field] = test_results.get(field)
        json_data = json.dumps(result)
        print(json_data)
        data_payload = base64.urlsafe_b64encode(bytearray(json_data, "utf8"))
        print(data_payload)
        message_future = publisher.publish(topic_name, data=data_payload)
        message_future.add_done_callback(callback)

    # define a callback function
    def callback(message_future):
        # When timeout is unspecified, the exception method waits indefinitely.
        if message_future.exception(timeout=30):
            print('Publishing message on {} threw an Exception {}.'.format(topic_name, message_future.exception()))
        else:
            print(message_future.result())

    # create datastore client
    print("configure gcp datastore client")
    datastore_client = datastore.Client()
    entity_kind = "test_url"

    # define a function to fetch a list of test URLs from datastore
    def fetch_test_urls(client):
        query = client.query(kind=entity_kind)
        query.add_filter("type","=","telecom")
        results = list(query.fetch())
        return results

    # query datastore for the most recent timestamp
    query_results = fetch_test_urls(datastore_client)
    print("query results :"+str(query_results))
    test_url_list = []
    for result in query_results:
        test_url_list.append(result.get("test_url"))
    print(test_url_list)

    for test_url in test_url_list:
        # request report for test_url
        url = "http://www.webpagetest.org/runtest.php?url="+test_url+"&f=json&runs=2&r=12345&k="+api_key
        print("Requesting test for "+test_url)
        request_test = requests.get(url)
        download_url = request_test.json()["data"]["jsonUrl"]
        test_status = requests.get(download_url).json()["statusText"]
        
        limit = 1
        while limit < 60:
            while "Waiting" in test_status:
                print(time.strftime("%Y-%m-%d %H:%M:%S")+" "+test_status)
                test_status = requests.get(download_url).json()["statusText"]
                limit = limit + 1
                time.sleep(10)
                continue
            else:
                while test_status != "Test Complete":
                    print(time.strftime("%Y-%m-%d %H:%M:%S")+" "+test_status)
                    test_status = requests.get(download_url).json()["statusText"]
                    limit = limit + 1
                    time.sleep(5)
                    continue
                else:
                    print(time.strftime("%Y-%m-%d %H:%M:%S")+" "+test_status)
                    time.sleep(10)
                    test_data = requests.get(download_url).json()
                    print("download complete: "+test_data["statusText"])
                    # return the first view and repeat view results
                    firstView = test_data["data"]["average"].get("firstView")
                    repeatView = test_data["data"]["average"].get("repeatView")
                    # publish data to pubsub
                    publish_data(test_url, "first view", firstView)
                    publish_data(test_url, "repeat view", repeatView)
                    break
            print("Test failed: timeout")
            return str("Test completed for "+test_url)