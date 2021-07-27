import googleapiclient.discovery
import logging
import base64
import json
from google.auth import compute_engine

credentials = compute_engine.Credentials()
compute = googleapiclient.discovery.build('compute', 'v1')


def tag_instance(instance: str, project: str, zone: str, contact: str):
    # add a label to the instance and return a list of the disk volumes
    instance_information = compute.instances().get(project=project, zone=zone, instance=instance).execute()
    instance_disks_list = [disk['deviceName'] for disk in instance_information['disks']]
    instance_fingerprint = instance_information['labelFingerprint']
    instance_labels = {'labels': {'contact': contact}, 'labelFingerprint': instance_fingerprint}
    request = compute.instances().setLabels(project=project, zone=zone, instance=instance, body=instance_labels)
    try:
        request.execute()
        return {'status': True, 'instance_disks_list': instance_disks_list}
    except Exception as e:
        print(str(e))
        return {'status': False, instance_disks_list: []}


def hello_pubsub(event, context):
    # parse the pubsub event
    pubsub_message = json.loads(base64.b64decode(event['data']).decode('utf-8'))

    # extract pubsub variables
    user_email = pubsub_message['protoPayload']['response']['user']
    user_contact = user_email.partition("@")[0]
    instance_zone = pubsub_message['resource']['labels']['zone']
    instance_id = pubsub_message['resource']['labels']['instance_id']
    project_id = pubsub_message['resource']['labels']['project_id']

    logging.info(f'new instance created, tagging instance {instance_id}')
    # tag the instance
    instance_tag = tag_instance(instance_id, project_id, instance_zone, user_contact)
