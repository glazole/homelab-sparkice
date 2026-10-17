import os
from oauthenticator.generic import GenericOAuthenticator
from dockerspawner import DockerSpawner

c = get_config()  # noqa: F821 -- supplied by JupyterHub

PUBLIC_URL = os.environ['JUPYTERHUB_PUBLIC_URL'].rstrip('/')
ISSUER = os.environ['KEYCLOAK_ISSUER'].rstrip('/')
OIDC = f'{ISSUER}/protocol/openid-connect'

c.JupyterHub.bind_url = 'http://0.0.0.0:8000'
c.JupyterHub.hub_bind_url = 'http://0.0.0.0:8081'
c.JupyterHub.hub_connect_url = 'http://jupyterhub:8081'
c.JupyterHub.trust_xheaders = True
c.JupyterHub.db_url = 'sqlite:////data/jupyterhub.sqlite'
c.JupyterHub.cookie_secret_file = '/data/jupyterhub_cookie_secret'
c.JupyterHub.authenticator_class = GenericOAuthenticator

c.GenericOAuthenticator.client_id = os.environ['KEYCLOAK_CLIENT_ID']
c.GenericOAuthenticator.client_secret = os.environ['KEYCLOAK_CLIENT_SECRET']
c.GenericOAuthenticator.authorize_url = f'{OIDC}/auth'
c.GenericOAuthenticator.token_url = f'{OIDC}/token'
c.GenericOAuthenticator.userdata_url = f'{OIDC}/userinfo'
c.GenericOAuthenticator.username_claim = 'preferred_username'
c.GenericOAuthenticator.scope = ['openid', 'profile', 'email']
c.GenericOAuthenticator.oauth_callback_url = f'{PUBLIC_URL}/hub/oauth_callback'
c.GenericOAuthenticator.auto_login = True

# Trusted CA for Keycloak OAuth token/userinfo requests
c.GenericOAuthenticator.http_request_kwargs = {
    "ca_certs": "/certs/ca-bundle.pem",
    "validate_cert": True,
}


allowed = {v.strip() for v in os.environ.get('JUPYTERHUB_ALLOWED_USERS', '').split(',') if v.strip()}
admins = {v.strip() for v in os.environ.get('JUPYTERHUB_ADMIN_USERS', '').split(',') if v.strip()}
if not allowed:
    raise RuntimeError('JUPYTERHUB_ALLOWED_USERS must contain at least one Keycloak preferred_username')
c.Authenticator.allow_all = False
c.Authenticator.allowed_users = allowed | admins
c.Authenticator.admin_users = admins

c.JupyterHub.spawner_class = DockerSpawner
c.DockerSpawner.image = os.environ.get('JUPYTER_SINGLEUSER_IMAGE', 'handyman-jupyter-spark:3.5.5-ice161')
c.DockerSpawner.network_name = os.environ.get('JUPYTER_DOCKER_NETWORK', 'outline-network')
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.name_template = 'sparkice-jupyter-{username}'
c.DockerSpawner.remove = True
c.DockerSpawner.volumes = {'sparkice-notebooks-{username}': '/home/spark/work'}
c.Spawner.notebook_dir = '/home/spark/work'
c.Spawner.default_url = '/lab'
c.Spawner.cmd = ['jupyterhub-singleuser']
c.Spawner.start_timeout = 300
c.Spawner.http_timeout = 120
c.Spawner.mem_limit = '3G'

# Only the explicitly allowed Keycloak users can launch notebook containers.
# S3 keys are scoped to this homelab warehouse, NOT production credentials.
base_env = {
    'AWS_REGION': os.environ.get('AWS_REGION', 'us-east-1'),
    'AWS_DEFAULT_REGION': os.environ.get('AWS_REGION', 'us-east-1'),
    'AWS_ACCESS_KEY_ID': os.environ['RUSTFS_ACCESS_KEY_ID'],
    'AWS_SECRET_ACCESS_KEY': os.environ['RUSTFS_SECRET_ACCESS_KEY'],
    'AWS_EC2_METADATA_DISABLED': 'true',
    'HOME': '/home/spark',
    'SPARK_HOME': '/opt/spark',
    'SPARK_CONF_DIR': '/opt/spark/conf',
    'SPARK_LOCAL_DIRS': '/tmp',
    'PYSPARK_PYTHON': '/opt/jupyter-venv/bin/python',
    'PYSPARK_DRIVER_PYTHON': '/opt/jupyter-venv/bin/python',
}
c.Spawner.environment = base_env

async def pre_spawn_hook(spawner):
    # Docker DNS resolves the actual user-container name on outline-network.
    driver_host = spawner.container_name
    env = dict(spawner.environment)
    env['PYSPARK_SUBMIT_ARGS'] = (
        '--master spark://spark-master:7077 '
        '--conf spark.driver.bindAddress=0.0.0.0 '
        f'--conf spark.driver.host={driver_host} '
        '--conf spark.cores.max=2 '
        '--conf spark.executor.instances=1 '
        '--conf spark.executor.cores=2 '
        '--conf spark.executor.memory=2g '
        'pyspark-shell'
    )
    spawner.environment = env

c.Spawner.pre_spawn_hook = pre_spawn_hook
