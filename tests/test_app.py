import os
from fastapi import status
from fastapi.testclient import TestClient
from main import app, get_settings
from internal.config import Settings

client = TestClient(app)


def get_settings_override():
    return Settings(admin_email="wera.watcharapon@gmail.com")

app.dependency_overrides[get_settings] = get_settings_override

headers = {}
USER = {"username": os.environ['user_testing'], "password": os.environ['pwd_testing']}

PAYLOAD_INTENT = {
    "name": "test unit",
    "access_token": "test unit access token",
    "ready": True,
    "type_reply": "Text",
    "card": "content test unit",
    "question": ["a", "b", "c", "d"],
    "answer": ["1", "2", "3", "4", "5"],
}


def get_token():
    token = client.post("/authentication/token", data=USER)
    token = token.json()["access_token"]
    headers["Authorization"] = "Bearer " + token


def test_intent_create():
    get_token()
    response = client.post("/intents/create", json=PAYLOAD_INTENT, headers=headers)
    global ids_intent
    ids_intent = response.json()["_id"]
    assert response.status_code == status.HTTP_201_CREATED


def test_intent_duplicate():
    response = client.post("/intents/create", json=PAYLOAD_INTENT, headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Invalid duplicate name."}


def test_intent_invalid():
    response = client.post(
        "/intents/create", json=PAYLOAD_INTENT.pop("name"), headers=headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"][0]["msg"] == "value is not a valid dict"


def test_intent_find():
    response = client.get(
        "/intents?access_token={}".format(PAYLOAD_INTENT.get("access_token")),
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) >= 1


def test_intent_find_empty():
    response = client.get("/intents?access_token=fake access token", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


def test_intent_update():
    PAYLOAD_INTENT["name"] = "test update unit"
    response = client.put(
        f"/intents/query/update/{ids_intent}", json=PAYLOAD_INTENT, headers=headers
    )
    assert response.status_code == status.HTTP_200_OK


def test_intent_update_flex_status_not_found_card():
    PAYLOAD_INTENT['type_reply'] = 'Flex Message'
    response = client.put(
        f'/intents/query/update/{ids_intent}', json=PAYLOAD_INTENT, headers=headers
    )
    PAYLOAD_INTENT['type_reply'] = 'Text'
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {f"detail": f"id card not found {PAYLOAD_INTENT['card']}"}


def test_intent_delete():
    response = client.delete(f"/intents/query/delete/{ids_intent}", headers=headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_intent_update_not_found():
    id = "fake_id_intent"
    PAYLOAD_INTENT["name"] = "update name intent test unit"
    response = client.put(
        f"/intents/query/update/{id}",
        json=PAYLOAD_INTENT,
        headers=headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": f"Intent not found {id}"}


def test_intent_delete_not_found():
    id = "fake_id_intent"
    response = client.delete(f"/intents/query/delete/{id}", headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": f"Intent not found {id}"}


"""
Testing Intent success
"""

PAYLOAD_RuleBased = {
    "name": "rule based",
    "access_token": "access token long live",
    "type_reply": 'Text',
    "ready": True,
    "card": "put query card in collection card",
    "keyword": 'test',
    "answer": [
        "answer bot"
    ]
}


def test_rule_based_create():
    response = client.post(
        "/rule_based/create", json=PAYLOAD_RuleBased, headers=headers
    )
    global ids_rule_based
    ids_rule_based = response.json()["_id"]
    assert response.status_code == status.HTTP_201_CREATED


def test_rule_based_duplicate():
    response = client.post(
        "/rule_based/create", json=PAYLOAD_RuleBased, headers=headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Invalid duplicate keyword."}


def test_rule_based_invalid():
    response = client.post(
        "/rule_based/create", json=PAYLOAD_RuleBased.pop("name"), headers=headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"][0]["msg"] == "value is not a valid dict"


def test_rule_based_find():
    response = client.get(
        "/rule_based?access_token={}".format(PAYLOAD_RuleBased.get("access_token")),
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) >= 1


def test_rule_based_find_empty():
    response = client.get("/rule_based?access_token=fake access token", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


def test_rule_based_update():
    PAYLOAD_RuleBased["name"] = "test update unit"
    response = client.put(
        f"/rule_based/query/update/{ids_rule_based}",
        json=PAYLOAD_INTENT,
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK


def test_rule_Based_update_flex_status_not_found_card():
    PAYLOAD_RuleBased['type_reply'] = 'Flex Message'
    response = client.put(
        f'/rule_based/query/update/{ids_rule_based}', json=PAYLOAD_RuleBased, headers=headers
    )
    PAYLOAD_RuleBased['type_reply'] = 'Text'
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {f"detail": f"id card not found {PAYLOAD_RuleBased['card']}"}


def test_rule_based_delete():
    response = client.delete(
        f"/rule_based/query/delete/{ids_rule_based}", headers=headers
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_rule_based_update_not_found():
    id = "fake_id_rule_based"
    PAYLOAD_RuleBased["name"] = "update name rule_based test unit"
    response = client.put(
        f"/rule_based/query/update/{id}",
        json=PAYLOAD_RuleBased,
        headers=headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": f"Rule Based not found {id}"}


def test_rule_based_delete_not_found():
    id = "fake_id_rule_based"
    response = client.delete(f"/rule_based/query/delete/{id}", headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": f"Rule Based not found {id}"}


"""
Testing RuleBased success
"""

PAYLOAD_CALLBACK = {
    "name": "test unit name",
    "access_token": os.environ['channel_access_token_callback'],
    "secret_token": "test unit secret token_callback",
}


def test_callback_create():
    get_token()
    response = client.post(
        "/callback/channel/create", json=PAYLOAD_CALLBACK, headers=headers
    )
    global callback_token
    global uid_callback
    callback_token = response.json()["token"]
    uid_callback = response.json()["uid"]
    assert response.status_code == status.HTTP_200_OK


def test_callback_update():
    PAYLOAD_CALLBACK["name"] = "update name callback test unit"
    response = client.put(
        f"/callback/channel/update/{callback_token}",
        json=PAYLOAD_CALLBACK,
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK


def test_callback_update_not_found():
    fake_token = "fake_id_callback"
    PAYLOAD_CALLBACK["name"] = "update name callback test unit"
    response = client.put(
        f"/callback/channel/update/{fake_token}",
        json=PAYLOAD_CALLBACK,
        headers=headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": f"Callback not found {fake_token} or Update Already exits"
    }


def test_callback_create_invalid_data():
    PAYLOAD_CALLBACK['access_token'] = 'test invalid'
    response = client.post(
        "/callback/channel/create", json=PAYLOAD_CALLBACK, headers=headers
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        'detail': 'Authentication failed. Confirm that the access token in the authorization header is valid.'}


def test_callback_find():
    response = client.get(f"/callback/channel/info?uid={uid_callback}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


def test_callback_find_one():
    response = client.get(f"/callback/channel/info/{callback_token}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), dict)


def test_callback_find_one_not_found():
    fake_token = "fake_user_access_token"
    response = client.get(f"/callback/channel/info/{fake_token}", headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": f"not found channel {fake_token}"}


def test_callback_delete():
    response = client.delete(
        f"/callback/channel/delete/{callback_token}", headers=headers
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_callback_delete_not_found():
    fake_token = "fake_id_callback"
    response = client.delete(f"/callback/channel/delete/{fake_token}", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Not found token {fake_token}"
    }


def test_callback_create_invalid():
    response = client.post(
        "/callback/channel/create", json=PAYLOAD_CALLBACK.pop("name"), headers=headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"][0]["msg"] == "value is not a valid dict"


"""
Testing Callback success
"""

PAYLOAD_CARD = {
    "name": "test unit name",
    "access_token": "access token long live",
    "content": "test unit content",
    "message": "message",
}


def test_card_create():
    response = client.post("/card/create", json=PAYLOAD_CARD, headers=headers)
    global ids_card
    ids_card = response.json()["_id"]
    assert response.status_code == status.HTTP_201_CREATED


def test_card_create_duplicate():
    response = client.post('/card/create', json=PAYLOAD_CARD, headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "card name is duplicate"}


def test_card_create_invalid():
    response = client.post(
        "/card/create", json=PAYLOAD_CARD.pop("name"), headers=headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"][0]["msg"] == "value is not a valid dict"


def test_card_get():
    access_token = PAYLOAD_CARD["access_token"]
    response = client.get(f"/card/find?access_token={access_token}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


def test_card_update():
    PAYLOAD_CARD["name"] = "test unit update name"
    response = client.put(
        f"/card/query/update/{ids_card}", json=PAYLOAD_CARD, headers=headers
    )
    assert response.status_code == status.HTTP_200_OK


def test_card_delete():
    response = client.delete(f"/card/query/delete/{ids_card}", headers=headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_card_update_not_found():
    id = "fake_card"
    PAYLOAD_CARD["name"] = "update name card test unit"
    response = client.put(
        f"/card/query/update/{id}",
        json=PAYLOAD_CARD,
        headers=headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": f"Card not found {id}"}


def test_card_delete_not_found():
    id = "fake_id_rule_based"
    response = client.delete(f"/card/query/delete/{id}", headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": f"Card not found {id}"}


"""
Testing Card success
"""

PAYLOAD_QUICK_REPLY = {
    "name": "test unit name",
    "access_token": "test access token long live",
    "intent": "test unit hello world",
    "texts": ["what name", "what product"],
    "labels": ["name", "product"],
    "reply": ["hello ja", "swadee ja"],
}


def test_button_create():
    response = client.post("/button/create", json=PAYLOAD_QUICK_REPLY, headers=headers)
    global ids_quick_reply
    ids_quick_reply = response.json()["_id"]
    assert response.status_code == status.HTTP_201_CREATED


def test_button_duplicate():
    response = client.post("/button/create", json=PAYLOAD_QUICK_REPLY, headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Invalid duplicate name."}


def test_button_create_invalid():
    response = client.post(
        "/button/create", json=PAYLOAD_QUICK_REPLY.pop("name"), headers=headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"][0]["msg"] == "value is not a valid dict"


def test_button_find():
    response = client.get(
        "/button?access_token={}".format(PAYLOAD_QUICK_REPLY.get("access_token")),
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) >= 1


def test_button_find_empty():
    response = client.get("/button?access_token=fake access token", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


def test_button_update():
    PAYLOAD_QUICK_REPLY["name"] = "test update unit"
    response = client.put(
        f"/button/query/update/{ids_quick_reply}",
        json=PAYLOAD_QUICK_REPLY,
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK


def test_button_delete():
    response = client.delete(f"/button/query/delete/{ids_quick_reply}", headers=headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_button_update_not_found():
    id = "fake_id_quick_reply"
    PAYLOAD_QUICK_REPLY["name"] = "update name quick_reply test unit"
    response = client.put(
        f"/button/query/update/{id}",
        json=PAYLOAD_QUICK_REPLY,
        headers=headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": f"Quick Reply not found {id}"}


def test_button_delete_not_found():
    id = "fake_id_quick_reply"
    response = client.delete(f"/button/query/delete/{id}", headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": f"Quick Reply not found {id}"}


"""
quick reply test success
100%
"""

PAYLOAD_IMAGE_MAP = {
    "name": "add mapping",
    "access_token": os.environ.get('BOT_LINE'),
    "content": """
    {
    "size": {
        "width": 480,
        "height": 480
    },
    "selected": true,
    "name": "Rich Menu 1",
    "chatBarText": "Bulletin",
    "areas": [
        {
            "bounds": {
                "x": 898,
                "y": 330,
                "width": 550,
                "height": 414
            },
            "action": {
                "type": "message",
                "data": "action"
            }
        },
        {
            "bounds": {
                "x": 898,
                "y": 330,
                "width": 550,
                "height": 414
            },
            "action": {
                "type": "message",
                "data": "action1"
            }
        }
    ]
}""",
    "description": "description mapping"
}


def test_mapping_create():
    response = client.post("/mapping/create", json=PAYLOAD_IMAGE_MAP, headers=headers)
    global ids_mapping
    ids_mapping = response.json()["_id"]
    assert response.status_code == status.HTTP_201_CREATED


def test_mapping_duplicate_item():
    response = client.post("/mapping/create", json=PAYLOAD_IMAGE_MAP, headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'detail': 'Invalid duplicate name.'}


def test_mapping_update():
    PAYLOAD_IMAGE_MAP['name'] = 'update name item'
    response = client.put(f'/mapping/query/update/{ids_mapping}',
                          json=PAYLOAD_IMAGE_MAP, headers=headers)
    assert response.status_code == status.HTTP_200_OK


def test_mapping_delete():
    response = client.delete(f'/mapping/query/delete/{ids_mapping}',
                             json=PAYLOAD_IMAGE_MAP, headers=headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


"""
progress ...100%
"""
BOT_PUSH = {
    "access_token": os.environ.get('BOT_LINE'),
    "broadcast": True,
    "content": {
        "ID": os.getenv("GITHUB_RUN_ID", "1234"),
        "Repository": os.getenv("GITHUB_REPOSITORY", "mango-bot"),
        "EventName": os.getenv("GITHUB_EVENT_NAME", "Unit Test"),
        "GITHUB_API_URL": os.getenv("GITHUB_API_URL", "https://api.com"),
        "GITHUB_PATH": os.getenv("GITHUB_PATH", "github_path"),
        "GITHUB_REF": os.getenv("GITHUB_REF", "github_ref"),
        "GITHUB_SERVER_URL": os.getenv("GITHUB_SERVER_URL", "https://github.com/watcharap0n"),
        "OWNER": "https://github.com/watcharap0n",
        "COMPANY": "Mango Consultant",
        "status": "Unit Test Success"
    },
    "config_default_card": {
        "header": "Unit Test Report",
        "image": True,
        "path_image": "https://sv1.picz.in.th/images/2022/03/04/rDEup9.png",
        "footer": True,
        "name_btn": "Report CI/CD",
        "url_btn": 'https://github.com/watcharap0n/mango-bot/actions'
    }
}


def test_push_unit_test_success_to_line():
    response = client.post(f'/bot/push/flex/default',
                           json=BOT_PUSH, headers=headers)
    assert response.status_code == status.HTTP_200_OK
