"""Los tests usan una DynamoDB simulada (moto): nunca tocan AWS."""
import os

os.environ.update(
    {
        "DYNAMODB_TABLE": "links-test",
        "PUBLIC_BASE_URL": "http://api.test:8000",
        "CORS_ORIGINS": "http://front.test",
        "AWS_REGION": "us-east-1",
        "AWS_ACCESS_KEY_ID": "test",
        "AWS_SECRET_ACCESS_KEY": "test",
    }
)

import boto3  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from moto import mock_aws  # noqa: E402

from app.main import app  # noqa: E402
from app.repository import LinkRepository, get_repository  # noqa: E402


@pytest.fixture
def tabla():
    with mock_aws():
        dynamo = boto3.resource("dynamodb", region_name="us-east-1")
        t = dynamo.create_table(
            TableName="links-test",
            KeySchema=[{"AttributeName": "short_code", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "short_code", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        yield t


@pytest.fixture
def client(tabla):
    repo = LinkRepository("links-test", "us-east-1")
    app.dependency_overrides[get_repository] = lambda: repo
    with TestClient(app, follow_redirects=False) as c:
        yield c
    app.dependency_overrides.clear()
