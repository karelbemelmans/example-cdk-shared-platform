#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks.infrastructure_stack import InfrastructureStack

# We read in the deployment environment to give our stack a custom name so we can potentially deploy multiple
# environments in the same account.
envs = ['Development', 'Production']

app = cdk.App()
cdk.Tags.of(app).add("Service", "Shared Platform")

for env in envs:
    stack = InfrastructureStack(app, f"InfrastructureStack-{env}",
        env=cdk.Environment(
            account=os.getenv('CDK_DEFAULT_ACCOUNT'),
            region=os.getenv('CDK_DEFAULT_REGION')
        ),
        description=f"Shared Platform stack - {env}",
    )
    cdk.Tags.of(stack).add("Environment", env)

app.synth()
