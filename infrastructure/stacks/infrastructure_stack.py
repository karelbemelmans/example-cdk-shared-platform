import aws_cdk as cdk

from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from constructs import Construct


class InfrastructureStack(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.output_props = {}

        # Create a VPC with all the defaults CDK uses
        vpc = ec2.Vpc(self, "PC", max_azs=3)
        self.output_props['vpc'] = vpc

        # Create an ECS cluster with all the defaults from CDK
        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)
        self.output_props['cluster'] = cluster

        # Create the load balancer
        alb = elbv2.ApplicationLoadBalancer(self, "ALB", vpc=vpc, internet_facing=True)
        self.output_props['alb'] = alb

        # Create the listeners for the ALB
        listener_http = alb.add_listener("HttpListener",
            open=True,
            port=80,
            default_action=elbv2.ListenerAction.fixed_response(status_code=404),
        )
        self.output_props['listener_http'] = listener_http

        # TODO: https listener

        # Security groups for the ALB
        alb_sg = ec2.SecurityGroup(self, "ALBSecurityGroup", vpc=vpc, allow_all_outbound=True)
        alb_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow http traffic")
        alb_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "Allow https traffic")

        # Everything else about the ECS setup will be done in components:
        # - target groups
        # - service and task definition
        # - ALB rules

    # pass objects to another stack
    @property
    def outputs(self):
        return self.output_props
