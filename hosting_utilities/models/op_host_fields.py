from typing import ClassVar, Dict, List, Optional

from onepassword.types import ItemField, ItemFieldType, ItemSection


class ConnectionDetailsSection(ItemSection):
    """
    Extended ItemSection for connection details, containing ItemFields
    for each OP_FIELD_NAMES entry.
    """

    OP_CONNECTION_DETAILS_SECTION: ClassVar = [
        {"label": "user", "type": ItemFieldType.TEXT},
        {"label": "server", "type": ItemFieldType.TEXT},
        {"label": "port", "type": ItemFieldType.TEXT},
    ]

    # These must match the field *labels* in your 1Password item
    OP_FIELDS: ClassVar = [
        {"label": "Password", "type": ItemFieldType.CONCEALED},
        {"label": "Remote Backup Directory", "type": ItemFieldType.TEXT},
        {"label": "Local Destination Directory", "type": ItemFieldType.TEXT},
        *OP_CONNECTION_DETAILS_SECTION,
    ]

    def __init__(
        self,
        id: str,
        title: str = "Connection Details",
        field_values: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(id=id, title=title)
        self.fields: List[ItemField] = []
        field_values = field_values or {}
        for field in self.OP_FIELDS:
            value = field_values.get(field["label"], "")
            self.fields.append(
                ItemField(
                    id=field["label"],
                    title=field["label"].replace("_", " ").title(),
                    sectionId=id,
                    fieldType=field["type"],
                    value=value,
                )
            )
