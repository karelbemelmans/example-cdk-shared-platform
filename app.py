#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks.infrastructure_stack import InfrastructureStack

# We read in the deployment environment to give our stack a custom name so we can potentially deploy multiple
# environments in the same account.
deploy_env = os.getenv('DEPLOY_ENV', "Undefined")

app = cdk.App()
cdk.Tags.of(app).add("Environment", deploy_env)

InfrastructureStack(app, f"InfrastructureStack-{deploy_env}",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION')
    ),
    description=f"Shared Platform stack - {deploy_env}",
)

app.synth()
