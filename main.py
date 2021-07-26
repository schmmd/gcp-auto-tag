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

def tag_disks(disks_list: list, project: str, zone: str, instance_name, contact: str):
    # tag a volume from the instance volume list
    for disk in disks_list:
        logging.info(f'tagging disk {disk}')
        try:
            disk_data = compute.disks().get(project=project, zone=zone, disk=disk).execute()
        # if the instance is part of instace template - the api volume name is the instance template name, but the actual volume name is the instance name
        except googleapiclient.errors.HttpError:
            disk_data = compute.disks().get(project=project, zone=zone, disk=instance_name).execute()
            disk = instance_name
        disk_fingerprint = disk_data['labelFingerprint']
        disk_labels = {'labels': {'contact': contact, 'instance': instance_name},
                       'labelFingerprint': disk_fingerprint}
        try:
            compute.disks().setLabels(project=project, zone=zone, resource=disk, body=disk_labels).execute()
        except Exception as e:
            print(str(e))
    return True


def hello_pubsub(event, context):
    # parse the pubsub event
    pubsub_message = json.loads(base64.b64decode(event['data']).decode('utf-8'))

    # extract pubsub variables
    user_email = pubsub_message['jsonPayload']['actor']['user']
    user_contact = user_email.partition("@")[0]
    instance_zone = pubsub_message['jsonPayload']['operation']['zone']
    instance_name = pubsub_message['jsonPayload']['resource']['name']
    project_id = pubsub_message['resource']['labels']['project_id']

    logging.info(f'new instance created, tagging instance {instance_name}')
    # tag the instance
    instance_tag = tag_instance(instance_name, project_id, instance_zone, user_contact)

    # if instance tag was successful and the instance volume list exists
    if instance_tag and instance_tag['instance_disks_list']:
        disks_list = instance_tag['instance_disks_list']
        # tag volumes
        disks_tag = tag_disks(disks_list, project_id, instance_zone, instance_name, user_contact)
        if disks_tag:
            return True
