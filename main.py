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

def tag_disk(disk, project: str, zone: str, contact: str):
    # tag a volume from the instance volume list
    logging.info(f'tagging disk {disk}')
    disk_data = compute.disks().get(project=project, zone=zone, disk=disk).execute()
    disk_fingerprint = disk_data['labelFingerprint']
    disk_labels = {'labels': {'contact': contact},
                    'labelFingerprint': disk_fingerprint}
    try:
        compute.disks().setLabels(project=project, zone=zone, resource=disk, body=disk_labels).execute()
        return True
    except Exception as e:
        print(str(e))
        return False

def hello_pubsub(event, context):
    # parse the pubsub event
    pubsub_message = json.loads(base64.b64decode(event['data']).decode('utf-8'))

    # extract pubsub variables
    user_email = pubsub_message['protoPayload']['response']['user']
    user_contact = user_email.partition("@")[0]
    instance_zone = pubsub_message['resource']['labels']['zone']
    instance_id = pubsub_message['resource']['labels']['instance_id']
    project_id = pubsub_message['resource']['labels']['project_id']

    # tag the instance
    logging.info(f'new instance created, tagging instance {instance_id}')
    instance_tag = tag_instance(instance_id, project_id, instance_zone, user_contact)
    status = instance_tag['status']

    # tag each disk
    if instance_tag and instance_tag['instance_disks_list']:
        for disk in instance_tag['instance_disks_list']:
            if not tag_disk(disk, project_id, instance_zone, user_contact):
                status = False

    # return False if an error ocurred
    return status
