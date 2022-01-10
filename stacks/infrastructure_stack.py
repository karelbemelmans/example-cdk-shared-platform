import aws_cdk as cdk

from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_route53 as route53
from aws_cdk import aws_route53_targets as targets
from constructs import Construct


class InfrastructureStack(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DNS domain_name for our service. We need
        hosted_zone = cdk.CfnParameter(self, "hostedZone", type="String", default="example.org")
        hosted_zone_id = cdk.CfnParameter(self, "hostedZoneId", type="String", default="")
        hosted_name = cdk.CfnParameter(self, "hostedName", type="String", default="api")

        # Create a VPC with all the defaults CDK uses
        vpc = ec2.Vpc(self, "PC", max_azs=2)

        # Create an ECS cluster with all the defaults from CDK
        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)

        # Load our already existing Route53 zone
        route53_zone = route53.HostedZone.from_hosted_zone_attributes(self, "HostedZone",
            hosted_zone_id=hosted_zone_id.value_as_string,
            zone_name=hosted_zone.value_as_string,
        )

        # Create the load balancer
        alb = elbv2.ApplicationLoadBalancer(self, "ALB", vpc=vpc, internet_facing=True)

        # DNS entry for our load balancer
        route53.ARecord(self, "AliasRecord",
            zone=route53_zone,
            record_name=hosted_name.value_as_string,
            target=route53.RecordTarget.from_alias(targets.LoadBalancerTarget(alb)),
        )

        # SSL Certificate
        certificate = acm.Certificate(self, "Certificate",
            domain_name=f"{hosted_name.value_as_string}.{hosted_zone.value_as_string}",
            validation=acm.CertificateValidation.from_dns(route53_zone)
        )

        # Create the listeners for the ALB
        alb.add_listener("HttpListener",
            open=True,
            port=80,
            default_action=elbv2.ListenerAction.redirect(protocol="HTTPS", port="443")
        )

        listener_https = alb.add_listener("HttpsListener",
            open=True,
            port=443,
            default_action=elbv2.ListenerAction.fixed_response(status_code=404),
            certificates=[certificate],
        )

        # Security groups for the ALB
        alb_sg = ec2.SecurityGroup(self, "ALBSecurityGroup", vpc=vpc, allow_all_outbound=True)
        alb_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow http traffic")
        alb_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "Allow https traffic")

        # We add a simple "ECS Sample" container on a test path
        task_definition = ecs.FargateTaskDefinition(self, "TaskDef")

        task_definition.add_container("DefaultContainer",
            image=ecs.ContainerImage.from_registry("amazon/amazon-ecs-sample"),
            memory_limit_mi_b=512
        )

        sample_service = ecs.FargateService(self, "SampleService",
            cluster=cluster,
            task_definition=task_definition,
            circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True),
        )

        target_group = listener_https.add_targets("ECSSample",
            port=80,
            targets=[sample_service],
            conditions=[
                elbv2.ListenerCondition.path_patterns('/ecs-sample')
            ],
        )

        # Everything else about the ECS setup will be done in components:
        # - target groups
        # - service and task definition
        # - ALB rules
        # ...and more if needed

        # Outputs
        cdk.CfnOutput(self, "ALBArn", value=alb.load_balancer_arn)
        cdk.CfnOutput(self, "ListenerHTTPArn", value=listener_https.listener_arn)
