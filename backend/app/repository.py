"""Acceso a la tabla de DynamoDB con boto3.

No hay llaves en el código: en la EC2, boto3 toma credenciales temporales del IAM Role.
"""
from functools import lru_cache
from typing import Annotated

import boto3
from fastapi import Depends

from app.config import settings


class LinkRepository:
    def __init__(self, table_name: str, region: str):
        self.region = region
        self.table = boto3.resource("dynamodb", region_name=region).Table(table_name)

    def save(self, item: dict) -> None:
        # La condición evita sobrescribir un enlace si se repitiera un UUID.
        self.table.put_item(Item=item, ConditionExpression="attribute_not_exists(short_code)")

    def find(self, short_code: str) -> dict | None:
        return self.table.get_item(Key={"short_code": short_code}).get("Item")

    def role_name(self) -> str | None:
        """Nombre del IAM Role con el que trabaja la API, sin el número de cuenta."""
        try:
            arn = boto3.client("sts", region_name=self.region).get_caller_identity()["Arn"]
        except Exception:
            return None
        partes = arn.split("/")
        return partes[1] if ":assumed-role/" in arn and len(partes) > 1 else None


@lru_cache
def get_repository() -> LinkRepository:
    return LinkRepository(settings.table_name, settings.aws_region)


RepoDep = Annotated[LinkRepository, Depends(get_repository)]
