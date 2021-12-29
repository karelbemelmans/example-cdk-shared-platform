from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
)
from constructs import Construct


class InfrastructureStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a VPC with all the defaults CDK uses
        vpc = ec2.Vpc(self, "PC", max_azs=3)

        # Create an ECS cluster with all the defaults from CDK
        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)
