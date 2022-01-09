import aws_cdk as core
import aws_cdk.assertions as assertions

from infrastructure.infrastruture_stack import InfrastrutureStack

# example tests. To run these tests, uncomment this file along with the example
# resource in infrastruture/infrastruture_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = InfrastrutureStack(app, "infrastruture")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
