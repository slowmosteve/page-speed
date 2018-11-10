# Page speed reporting app

This application uses the webpagetest.org API to get page speed data for a given list of urls and store in Google BigQuery

The key components in this application are as follows:

## Scheduler App
- This is a Google App Engine instance that is running a cron job to trigger a cloud function

## Page Speed Data Cloud Function
- This is a Google Cloud Function that requests data from the webpagetest.org API and sends it to Google Pub/Sub
  - Google Datastore is used to store and retrieve the list of URLs to test

## Pub/Sub to BigQuery Cloud Function
- This is a Google Cloud Function that is triggered by the Pub/Sub topic and pushes data to BigQuery


![App architecture](https://github.com/slowmosteve/page-speed/blob/master/images/page-speed-app.png)


## References
- Pub/Sub Python client library https://googleapis.github.io/google-cloud-python/latest/pubsub/index.html
- Example of sending data from Pub/Sub to BigQuery https://medium.com/devopslinks/writing-a-pub-sub-stream-to-bigquery-401b44c86bf
