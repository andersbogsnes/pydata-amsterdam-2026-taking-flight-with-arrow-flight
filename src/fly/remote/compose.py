import python_on_whales


def _start_services():
    client = python_on_whales.DockerClient(compose_files=["./compose.yaml"])
    client.compose.up(build=True, detach=True)
