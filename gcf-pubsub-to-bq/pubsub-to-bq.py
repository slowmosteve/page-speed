import base64
import json
from google.cloud import bigquery

def pubsub_bq_insert(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    print("event: "+str(event))
    print("context: "+str(context))
    raw_data = event['data']
    stream = base64.urlsafe_b64decode(raw_data)
    decoded_stream = base64.urlsafe_b64decode(stream)
    pubsub_message = json.loads(decoded_stream)
    print("data to insert: "+str(pubsub_message))

    client = bigquery.Client()
    dataset_id = 'page_speed_reports'
    table_id = 'reports'
    table_ref = client.dataset(dataset_id).table(table_id)
    table = client.get_table(table_ref)

    rows_to_insert = [pubsub_message]

    errors = client.insert_rows(table, rows_to_insert)
    if (errors != []):
        print(errors)
    assert errors == []
