import aws_cdk as cdk

from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from constructs import Construct


class ComponentStack(cdk.Stack):

    def __init__(self, scope: Construct, id: str, props, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        task_definition = ecs.FargateTaskDefinition(self, "TaskDef")

        container = task_definition.add_container("web",
            image=ecs.ContainerImage.from_registry(props['component']['image']),
            memory_limit_mib=512
        )

        container.add_port_mappings(ecs.PortMapping(container_port=80))

        service = ecs.FargateService(self, props['component']['name'],
            cluster=props['cluster'],
            task_definition=task_definition,
            circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True),
        )

        target_group = props['listener_https'].add_targets(props['component']['name'],
            port=80,
            targets=[service],
            conditions=[
                elbv2.ListenerCondition.path_patterns([props['component']['path']])
            ],
            priority=10,
        )

        # Outputs to be used by other stacks
        self.output_props = props.copy()

    @property
    def outputs(self):
        return self.output_props
