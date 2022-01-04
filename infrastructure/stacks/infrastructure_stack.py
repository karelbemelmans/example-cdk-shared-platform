import aws_cdk as cdk

from aws_cdk import aws_certificatemanager as certificatemanager
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from constructs import Construct


class InfrastructureStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a VPC with all the defaults CDK uses
        vpc = ec2.Vpc(self, "PC", max_azs=3)

        # Create an ECS cluster with all the defaults from CDK
        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)

        # Create the load balancer
        alb = elbv2.ApplicationLoadBalancer(self, "ALB", vpc=vpc, internet_facing=True)

        # Create the listeners for the ALB
        # - HTTP
        listener_http = alb.add_listener("ALBHttpListener",
            open=True,
            port=80,
            default_action=elbv2.ListenerAction.fixed_response(status_code=404),
        )
        # - HTTPS @TODO

        # Security groups for the ALB
        alb_sg = ec2.SecurityGroup(self, "ALBSecurityGroup", vpc=vpc, allow_all_outbound=True)
        alb_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow http traffic")
        alb_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "Allow https traffic")

        # Target group
        target_group = elbv2.ApplicationTargetGroup(self, "TargetGroup",
            vpc=vpc,
            port=8080,
            protocol=elbv2.ApplicationProtocol.HTTP,
            target_type=elbv2.TargetType.IP,
            deregistration_delay=Duration.seconds(5),

            # We simply use the frontpage of our component as a health check
            # @TODO Make this a proper health check url
            health_check=elbv2.HealthCheck(
                path='/',
                protocol=elbv2.Protocol.HTTP,
                interval=Duration.seconds(30),
                healthy_threshold_count=2,
                timeout=Duration.seconds(5)
            )
        )

        # Security group to allow connection between ALB and Fargate containers
        ecs_sg = ec2.SecurityGroup(self, "ECSSecurityGroup", vpc=vpc, allow_all_outbound=True)
        ecs_sg.connections.allow_from(alb_sg, ec2.Port.all_tcp(), "Application Load Balancer")

        # The ECS Fargate Service definition
        service = ecs.FargateService(self, "FargateService",
            task_definition=task_def,
            cluster=cluster,
            security_groups=[ecs_sg],
            desired_count=desired_count.value_as_number,
            min_healthy_percent=100,
            max_healthy_percent=200,

            # See: https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_DeploymentCircuitBreaker.html
            circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True),
        )

        # Attach the Service to our Target group
        service.attach_to_application_target_group(target_group)




        # CloudFront logging bucket
        cloudfront_logging_bucket = s3.Bucket(self, f"{id}-cloudfront-log")

        # CloudFront origin
        origin = origins.LoadBalancerV2Origin(alb)

        # CloudFront distribution, one per market to make it easy to manage certificates
        distribution = cloudfront.Distribution(self, f"{id}-distribution",
            enabled=True,
            price_class=cloudfront.PriceClass.PRICE_CLASS_200,
            default_behavior=cloudfront.BehaviorOptions(
                origin=origin,
                origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD,
                cache_policy=cache_policy,
                compress=True,
                function_associations=distribution_functions
            ),
            domain_names=[f"{values['subdomain']}.{values['domain']}"],
            minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2018,
            certificate=certificatemanager.Certificate.from_certificate_arn(self, f"{id}-{market}-certificate",
                values['certificates']['cloudfront']),
            log_bucket=cloudfront_logging_bucket,
            log_file_prefix=f"{values['subdomain']}.{values['domain']}",
            enable_logging=True,
        )
