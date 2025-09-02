import os
from typing import Dict, Optional

from onepassword.client import Client as OPServiceAccountClient
from onepassword.types import Item, ItemListFilter, ItemListFilterByStateInner
from onepasswordconnectsdk.client import (
    Client as OPConnectClient,
)

from hosting_utilities.models.op_host_fields import ConnectionDetailsSection

connect_client: OPConnectClient | None = None

service_client: OPServiceAccountClient | None = None


def is_op_connect_client(client: object) -> bool:
    return isinstance(client, OPConnectClient)


def is_op_service_account_client(client: object) -> bool:
    return isinstance(client, OPServiceAccountClient)


async def is_op_authorized() -> bool:
    """
    Check if the 1Password Connect client is authorized.
    """
    connect_client = get_op_connect_client()
    service_client = await get_op_service_account_client()
    return is_op_connect_client(connect_client) or is_op_service_account_client(service_client)


def get_op_connect_client() -> OPConnectClient | None:
    global connect_client
    if is_op_connect_client(connect_client):
        return connect_client

    op_connect_token = os.environ.get("OP_CONNECT_TOKEN")
    op_connect_host = os.environ.get("OP_CONNECT_HOST")
    if not op_connect_token or not op_connect_host:
        # raise RuntimeError(
        #     """
        #     OP_CONNECT_TOKEN and OP_CONNECT_HOST environment variables must be set for
        #     1Password Connect.
        #     """
        # )
        return None

    try:
        connect_client = OPConnectClient(url=op_connect_host, token=op_connect_token)
    except Exception:
        connect_client = None

    return connect_client


async def get_op_service_account_client() -> OPServiceAccountClient | None:
    global service_client
    if is_op_service_account_client(service_client):
        return service_client

    token = os.getenv("OP_SERVICE_ACCOUNT_TOKEN")
    if not token:
        return None

    # Connects to 1Password. Fill in your own integration name and version.
    service_client = await OPServiceAccountClient.authenticate(
        auth=token, integration_name="Hosting Utilities PY", integration_version="v1.0.0"
    )

    return service_client


def fetch_fields_from_op_connect_client(
    field_names: list[str], env_field_map: Dict[str, str]
) -> Dict[str, str]:
    """
    Fetch required fields from 1Password using onepasswordconnectsdk and environment variables
    for item and vault names.
    Returns a dict mapping ENV_FIELD_MAP values to their corresponding values.
    """
    if OPConnectClient is None:
        raise ImportError(
            """
            The 'onepasswordconnectsdk' library is required to fetch credentials from
            1Password Connect.
            """
        )
    op_item_name = os.environ.get("OP_ITEM_NAME")
    op_vault_name = os.environ.get("OP_VAULT_NAME")
    if not op_item_name or not op_vault_name:
        raise RuntimeError("OP_ITEM_NAME and OP_VAULT_NAME environment variables must be set.")

    client = get_op_connect_client()
    if client is None:
        raise RuntimeError("Failed to create 1Password Connect client.")

    item = client.get_item_by_title(op_vault_name, op_item_name)
    # item.fields is a list of field objects with 'label' and 'value', but may be None
    fields = {f.label: f.value for f in (item.fields or []) if f.label in field_names}
    env_vars = {env_field_map[k]: v for k, v in fields.items() if k in env_field_map}
    return env_vars


def get_connection_details_section(
    op_service_item: Item, field_names: Optional[list[str]] = None
) -> ConnectionDetailsSection:
    """
    Extract the connection details section from the 1Password service item.
    """
    field_values = {
        f.title: f.value
        for f in (op_service_item.fields or [])
        if not field_names or f.title in field_names
    }
    return ConnectionDetailsSection(id=op_service_item.id, field_values=field_values)


async def get_op_service_vault_id(vault_name: str) -> str | None:
    """
    Get the vault ID from the vault name using the service account client.
    """
    client = await get_op_service_account_client()
    if client is None:
        raise RuntimeError("Failed to create 1Password Service Account client.")

    vaults = await client.vaults.list()
    if not vaults:
        return None

    vault = next((v for v in vaults if v.title == vault_name), None)
    if vault is None:
        return None

    return vault.id


async def get_op_service_item_id(item_name: str, vault_id: str) -> str | None:
    """
    Get the item ID from the item name and vault ID using the service account client.
    """
    client = await get_op_service_account_client()
    if client is None:
        raise RuntimeError("Failed to create 1Password Service Account client.")

    items = await client.items.list(
        vault_id, ItemListFilter(content=ItemListFilterByStateInner(active=True, archived=False))
    )
    if not items:
        return None

    item = next((i for i in items if i.title == item_name), None)
    if item is None:
        return None

    return item.id


async def fetch_fields_from_op_service_client(
    field_names: list[str], env_field_map: Dict[str, str]
) -> Dict[str, str]:
    """
    Fetch required fields from 1Password using onepasswordconnectsdk and environment variables
    for item and vault names.
    Returns a dict mapping ENV_FIELD_MAP values to their corresponding values.
    """
    if OPServiceAccountClient is None:
        raise ImportError(
            """
            The 'onepasswordconnectsdk' library is required to fetch credentials from
            1Password Connect.
            """
        )

    op_item_name = os.environ.get("OP_ITEM_NAME")
    op_vault_name = os.environ.get("OP_VAULT_NAME")
    if not op_item_name or not op_vault_name:
        raise RuntimeError("OP_ITEM_NAME and OP_VAULT_NAME environment variables must be set.")

    client = await get_op_service_account_client()
    if client is None:
        raise RuntimeError("Failed to create 1Password Service Account client.")

    # resolve the vault name the vault id
    vault_id = await get_op_service_vault_id(op_vault_name)
    if vault_id is None:
        raise RuntimeError("Failed to retrieve vault ID from 1Password Service Account client.")

    # resolve the item name the item id
    item_id = await get_op_service_item_id(op_item_name, vault_id)
    if item_id is None:
        raise RuntimeError("Failed to retrieve item ID from 1Password Service Account client.")

    item = await client.items.get(vault_id, item_id)
    if item is None:
        raise RuntimeError("Failed to retrieve item from 1Password Service Account client.")

    # item.fields is a list of field objects with 'label' and 'value', but may be None
    fields = {f.title: f.value for f in (item.fields or []) if f.title in field_names}
    env_vars = {env_field_map[k]: v for k, v in fields.items() if k in env_field_map}
    return env_vars


async def fetch_fields_from_1password(
    field_names: list[str], env_field_map: Dict[str, str]
) -> Dict[str, str]:
    env_vars: Dict[str, str] | None = None

    global connect_client, service_client
    if is_op_connect_client(connect_client):
        results = fetch_fields_from_op_connect_client(field_names, env_field_map)
        if results:
            env_vars = results

    if is_op_service_account_client(service_client):
        results = await fetch_fields_from_op_service_client(field_names, env_field_map)
        if results:
            env_vars = results

    if not env_vars:
        raise RuntimeError("Failed to retrieve environment variables from 1Password.")

    return env_vars
