import workflows_cdk
print("Request class:", type(workflows_cdk.Request))
print("Request methods:", [m for m in dir(workflows_cdk.Request) if not m.startswith('_')])
print("\nResponse class:", type(workflows_cdk.Response))
print("Response methods:", [m for m in dir(workflows_cdk.Response) if not m.startswith('_')])