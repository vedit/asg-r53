from __future__ import print_function
import boto3
import json

ec2_client = boto3.client('ec2')
route53_client = boto3.client('route53')
asg_client = boto3.client('autoscaling')
hosted_zone_id = 'your hosted zone id'
zone_record_name = 'your zone record name'


def lambda_handler(event, context):
    asg = asg_client.describe_auto_scaling_groups(
        AutoScalingGroupNames=[event['detail']['AutoScalingGroupName']])
    asg_instances = asg['AutoScalingGroups'][0]['Instances']
    healthy_asg_instances = [asg_instance['InstanceId'] for asg_instance in asg_instances if
                             asg_instance['LifecycleState'] == "InService" and asg_instance[
                                 'HealthStatus'] == "Healthy"]
    healthy_asg_instances_metadata = ec2_client.describe_instances(
        DryRun=False, InstanceIds=healthy_asg_instances)
    zone_ips = [{'Value': healthy_asg_instance_metadata["Instances"][0]["PublicIpAddress"]} for
                healthy_asg_instance_metadata in
                healthy_asg_instances_metadata["Reservations"]]
    result = route53_client.change_resource_record_sets(
        HostedZoneId=hosted_zone_id,
        ChangeBatch={'Changes': [
            {'Action': 'UPSERT',
             'ResourceRecordSet': {'Name': zone_record_name, 'Type': 'A', 'TTL': 300,
                                   'ResourceRecords': zone_ips}}]})
    return zone_ips
