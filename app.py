#!/usr/bin/env python3
import aws_cdk as cdk

from stacks.infrastructure_stack import InfrastructureStack

app = cdk.App()
cdk.Tags.of(app).add("Service", "Shared Platform")

# Create our base infrastructure VPC, ECS and ALB
infra = InfrastructureStack(app, f"Infrastructure", description="Shared Platform - Infrastructure stack")

app.synth()
