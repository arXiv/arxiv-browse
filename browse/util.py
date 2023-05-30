from google.cloud import secretmanager

def get_secret(project_id: str, secret_id: str, version_id: str) -> secretmanager.GetSecretRequest:
    """
    Get information about the given secret. This only returns metadata about
    the secret container, not any secret material.
    """

    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the secret.
    path = f'projects/{project_id}/secrets/{secret_id}/versions/{version_id}'

    # Get the secret.
    response = client.access_secret_version(request={"name": path})
    
    return response.payload.data.decode("UTF-8")
