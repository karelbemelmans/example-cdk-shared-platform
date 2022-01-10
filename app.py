#!/usr/bin/env python3
import aws_cdk as cdk

from stacks.infrastructure_stack import InfrastructureStack
from stacks.component_stack import ComponentStack

app = cdk.App()
cdk.Tags.of(app).add("Service", "Shared Platform")

# Create our base infrastructure VPC, ECS and ALB
props = {'namespace': 'SharedPlatform '}
infra = InfrastructureStack(app, f"Infrastructure", props, description="Shared Platform - Infrastructure stack")

# This list should come from a better configuration resource, but for this test platform we simply define an array here.
components = [
    {
        "name": "amazon-ecs-sample",
        "image": "amazon/amazon-ecs-sample",
        "path": "/",
    }
]

# For every component on our shared platform we create a separate stack
for c in components:
    props = infra.outputs.copy()
    props['component'] = c

    cs = ComponentStack(app, f"PlatformComponent-{c['name']}", props, description=f"Component: {c['name']}")
    cs.add_dependency(infra)

app.synth()
