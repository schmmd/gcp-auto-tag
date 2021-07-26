# gcp-auto-tag

This repository contains code to autotag instances in GCP with a `contact` label, which can be
useful for establishing who is responsiblef or a resource in GCP.

These instructions were adapted from https://blog.doit-intl.com/automatically-label-google-cloud-compute-engine-instances-and-disks-upon-creation-5d1245f361c1

1.  Go to [Cloud Functions](https://console.cloud.google.com/functions/list) and click on CREATE FUNCTION.

  a.  Give the function a name (such as `autotagger`), and change the trigger to `Cloud Pub/Sub`.
  b.  Click CREATE TOPIC and give a title such as `label-instance-on-creation`.
  c.  Click SAVE.
  d.  Click NEXT to advance from `Configuration` to `Code`.
  e.  Select `Python 3.8`.
  f.  Click on SOURCE CODE and change it to ZIP Upload.
