import json
from db import db
from numpy import random
from pydantic import BaseModel
from starlette.responses import JSONResponse
from modules.item_static import item_user
from modules.flex_message import flex_dynamic
from models.callback import Webhook, LineToken, UpdateLineToken
from models.data_table import ColumnDataTable, TokenUser, SelectColumn
from random import randint
from typing import Optional, List
from fastapi import APIRouter, Depends, Body, Request, status, HTTPException, Path
from oauth2 import get_current_active, User
from fastapi.encoders import jsonable_encoder
from linebot import LineBotApi, WebhookHandler
from linebot.models import StickerSendMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
from modules.mg_chatbot import chatbot_standard, intent_model
from modules.mapping import image_map
from linebot.exceptions import InvalidSignatureError, LineBotApiError

router = APIRouter()
collection = "webhook"


async def get_webhook(token):
    user = await db.find_one(collection=collection, query={"token": token})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Not found token {token}')
    user = Webhook(**user)
    return user


def create_file_json(path: str, data):
    with open(path, mode="w") as jsonfile:
        json.dump(data, jsonfile)


async def get_profile(userId: str, access_token: str):
    line_bot_api = LineBotApi(access_token)
    profile = line_bot_api.get_profile(userId)
    displayName = profile.display_name
    userId = profile.user_id
    img = profile.picture_url
    status = profile.status_message
    result = {
        "access_token": access_token,
        "displayName": displayName,
        "userId": userId,
        "img": img,
        "status": status,
    }
    return result


async def check_access_token(item: LineToken):
    user = await db.find_one(
        collection=collection, query={"access_token": item.access_token}
    )
    if not user:
        try:
            line_bot_api = LineBotApi(item.access_token)
            line_bot_api.get_bot_info()
            return item
        except LineBotApiError as ex:
            raise HTTPException(status_code=ex.status_code, detail=ex.message)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Access token have already",
    )


@router.get("/channel/info", response_model=List[Webhook])
async def get_all_token(current_user: User = Depends(get_current_active)):
    """

    :param uid:
    :param current_user:
    :return:
    """
    uid = current_user.data.uid
    channels = await db.find(collection=collection, query={"uid": uid})
    channels = list(channels)
    return channels


@router.get("/channel/info/{token}", response_model=Webhook)
async def get_query_token(token: str,
                          current_user: User = Depends(get_current_active)):
    channel = await db.find_one(collection=collection, query={"token": token})
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"not found channel {token}",
        )

    channel = Webhook(**channel)
    return channel


@router.post("/channel/create", response_model=Webhook)
async def create_channel(
        item: LineToken = Depends(check_access_token),
        current_user: User = Depends(get_current_active),
):
    """

    :param item:
    :param current_user:
    :return:
    """

    line_bot_api = LineBotApi(item.access_token)
    bot_info = line_bot_api.get_bot_info()
    item_model = jsonable_encoder(item)
    item_model = item_user(data=item_model, current_user=current_user, url=True)
    item_model["bot_info"] = bot_info
    item_model = jsonable_encoder(item_model)
    store_model = Webhook(**item_model)
    models = await db.find(collection='default_tables_model', query={})
    models = list(models)

    selected_table_model = SelectColumn(access_token=item.access_token)
    selected_obj = jsonable_encoder(selected_table_model)
    selected_obj = item_user(selected_obj, current_user)

    for model in models:
        structure_table_model = ColumnDataTable(
            value=model['value'],
            text=model['text'],
            access_token=item.access_token,
            status=model['status'],
            default_field=model['default_field'],
            used=model['used'],
            type_field=model.get('type_field')
        )
        obj_store_model = jsonable_encoder(structure_table_model)
        obj_model = item_user(data=obj_store_model, current_user=current_user)
        await db.insert_one(collection='data_table', data=obj_model)

    await db.insert_one(collection='columns', data=selected_obj)
    await db.insert_one(collection=collection, data=item_model)
    return store_model


@router.put("/channel/update/{token}", response_model=UpdateLineToken)
async def update_channel(
        payload: UpdateLineToken,
        token: Optional[str] = None,
        current_user: User = Depends(get_current_active),
):
    try:
        line_bot_api = LineBotApi(payload.access_token)
        line_bot_api.get_bot_info()
        data = jsonable_encoder(payload)
        query = {"token": token}
        values = {"$set": data}

        if (await db.update_one(collection=collection, query=query, values=values)) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Callback not found {token} or Update Already exits",
            )
        return payload
    except LineBotApiError as ex:
        raise HTTPException(status_code=ex.status_code, detail=ex.message)


@router.delete("/channel/delete/{token}")
async def delete_channel(
        token: Optional[str] = None,
        current_user: User = Depends(get_current_active),
):
    """

    :param token:
    :param current_user:
    :return:
    """
    item = await get_webhook(token)
    if (await db.delete_one(collection=collection, query={"token": token})) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Callback not found {token} or Delete Already exits",
        )
    collections = db.get_collection_names()
    for collect in collections:
        await db.delete_many(collection=collect, query={"access_token": item.access_token})
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{token}")
async def client_webhook(
        request: Request,
        token: Optional[str] = Path(...),
        payload: Optional[dict] = Body(None),
):
    """

    :param request:
    :param token:
    :param payload:
    :return:
    """

    model = await get_webhook(token)
    handler = WebhookHandler(model.secret_token)
    create_file_json("static/log/line.json", payload)
    try:
        signature = request.headers['X-Line-Signature']
        body = await request.body()
        events = payload["events"][0]
        event_type = events["type"]
        if event_type == "follow":
            userId = events["source"]["userId"]
            follower = await get_profile(userId, model.access_token)
            db.insert_one(collection="follower_linebot", data=follower)
        elif event_type == "unfollow":
            userId = events["source"]["userId"]
            db.delete_one("follower_linebot", query={"userId": userId})
        elif event_type == "postback":
            await event_postback(events, model)
        elif event_type == "message":
            message_type = events["message"]["type"]
            if message_type == "text":
                try:
                    handler.handle(str(body, encoding='utf8'), signature)
                    await handle_message(events, model)
                except InvalidSignatureError as v:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={"status_code": 400, "message": v.message},
                    )
            else:
                no_event = len(payload["events"])
                for i in range(no_event):
                    events = payload["events"][i]
                    event_handler(events, model)
    except IndexError:
        raise HTTPException(
            status_code=status.HTTP_200_OK, detail={"message": "Index error"}
        )
    return payload


async def event_postback(events, model):
    line_bot_api = LineBotApi(model.access_token)
    reply_token = events["replyToken"]
    postback = events['postback']['data']
    item = await db.find_one(collection='rule_based',
                             query={'access_token': model.access_token, 'keyword': postback})
    type_reply = item.get('type_reply')

    if type_reply == 'Flex Message':
        card = item.get('card')
        flex_msg = await get_card_content(card)
        line_bot_api.reply_message(reply_token, flex_msg)
    elif type_reply == 'Text':
        answer = item.get('answer')
        reply = random.choice(answer)
        line_bot_api.reply_message(reply_token, TextSendMessage(text=reply))


def event_handler(events, model):
    line_bot_api = LineBotApi(model.access_token)
    replyToken = events["replyToken"]
    package_id = "446"
    stickerId = randint(1988, 2027)
    line_bot_api.reply_message(
        replyToken, StickerSendMessage(package_id, str(stickerId))
    )


def quick_reply_custom(line_bot_api, userId: str, send_text: str, labels: list, texts: list):
    line_bot_api.reply_message(
        userId,
        TextSendMessage(
            text=send_text,
            quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label=label, text=text)) for label, text in zip(labels, texts)
            ])
        )
    )


async def get_card_content(card):
    content_card = await db.find_one(collection='card', query={'_id': card})
    content = json.loads(content_card.get('content'))
    flex_msg = flex_dynamic(alt_text=content_card.get('name'), contents=content)
    return flex_msg


async def get_image_content(image):
    return await db.find_one(collection='images_map', query={'_id': image})


class Word(BaseModel):
    X: list
    y: list
    answers: Optional[list] = None


def preprocessing_words(db):
    sum_word = []
    ans_list = [x['answer'] for x in db]
    embedding = [x for x in range(len(ans_list))]
    for words in db:
        text = str()
        for word in words['question']:
            text += word
        sum_word.append(text)
    return Word(X=sum_word, y=embedding, answers=ans_list)


async def handle_message(events, model):
    line_bot_api = LineBotApi(model.access_token)
    message = events["message"]["text"]
    reply_token = events["replyToken"]
    userId = events["source"]["userId"]

    keyword = await db.find_one(collection='rule_based',
                                query={'access_token': model.access_token, 'keyword': message})

    if not keyword:
        intents = list(await db.find(collection='intents', query={'access_token': model.access_token}))
        words = preprocessing_words(db=intents)
        result_intent = await intent_model(
            X=words.X,
            y=words.y,
            answers=words.answers,
            message=message,
            db=intents
        )
        if result_intent.require:
            line_bot_api.reply_message(reply_token, TextSendMessage(text=result_intent.require))

        confidence = result_intent.confidence[0] * 100
        type_reply = result_intent.type_reply
        predicted = result_intent.predicted[0]
        answers = result_intent.answers
        card = result_intent.card
        ready = result_intent.ready
        id_intent = result_intent.id
        image = result_intent.image

        buttons = await db.find_one(collection='quick_reply', query={'intent': id_intent})
        if buttons:
            labels = buttons['labels']
            texts = buttons['texts']
            reply_message = buttons['reply']
            reply = random.choice(reply_message)
            quick_reply_custom(line_bot_api, reply_token, reply, labels, texts)
            profile = await get_profile(userId, model.access_token)
            profile["question"] = message
            profile['answer'] = reply
            await db.insert_one(collection="messages_user", data=profile)

        elif not buttons:
            if ready:
                if confidence > 69:
                    if type_reply == 'Flex Message':
                        flex_msg = await get_card_content(card)
                        line_bot_api.reply_message(reply_token, flex_msg)
                        profile = await get_profile(userId, model.access_token)
                        profile["question"] = message
                        profile['answer'] = card
                        await db.insert_one(collection="messages_user", data=profile)

                    elif type_reply == 'Text':
                        reply = random.choice(answers[predicted])
                        line_bot_api.reply_message(reply_token, TextSendMessage(text=reply))
                        profile = await get_profile(userId, model.access_token)
                        profile["question"] = message
                        profile['answer'] = reply
                        await db.insert_one(collection="messages_user", data=profile)

                    elif type_reply == 'Image Map':
                        content = await get_image_content(image)
                        reply_image = image_map(
                            base_url_image=content.get('base_url_image'),
                            size=content.get('size'),
                            areas=content.get('areas')
                        )
                        if reply_image:
                            line_bot_api.reply_message(reply_token, reply_image)
                            profile = await get_profile(userId, model.access_token)
                            profile["question"] = message
                            profile['answer'] = 'Image map'
                            await db.insert_one(collection="messages_user", data=profile)

                        else:
                            line_bot_api.reply_message(reply_token, TextSendMessage(text='.'))
                            profile = await get_profile(userId, model.access_token)
                            profile["question"] = message
                            profile['answer'] = f'Invalid Data Image'
                            await db.insert_one(collection="messages_user", data=profile)

                else:
                    line_bot_api.reply_message(reply_token, TextSendMessage(text='.'))
                    profile = await get_profile(userId, model.access_token)
                    profile["question"] = message
                    profile['answer'] = '.'
                    await db.insert_one(collection="messages_user", data=profile)

    elif keyword:
        answer_keyword = keyword.get('answer')
        card_keyword = keyword.get('card')
        image_keyword = keyword.get('image')
        if keyword.get('ready'):
            type_reply = keyword.get('type_reply')
            if type_reply == 'Flex Message':
                flex_msg = await get_card_content(card_keyword)
                line_bot_api.reply_message(reply_token, flex_msg)
                profile = await get_profile(userId, model.access_token)
                profile["question"] = message
                profile['answer'] = card_keyword
                await db.insert_one(collection="messages_user", data=profile)

            elif type_reply == 'Image Map':
                content = await get_image_content(image_keyword)
                reply_image = image_map(
                    base_url_image=content.get('base_url_image'),
                    size=content.get('size'),
                    areas=content.get('areas')
                )
                if reply_image:
                    line_bot_api.reply_message(reply_token, reply_image)
                    profile = await get_profile(userId, model.access_token)
                    profile["question"] = message
                    profile['answer'] = 'Image map'
                    await db.insert_one(collection="messages_user", data=profile)

                else:
                    line_bot_api.reply_message(reply_token, TextSendMessage(text='.'))
                    profile = await get_profile(userId, model.access_token)
                    profile["question"] = message
                    profile['answer'] = f'Invalid Data Image'
                    await db.insert_one(collection="messages_user", data=profile)

            elif type_reply == 'Text':
                reply = random.choice(answer_keyword)
                line_bot_api.reply_message(reply_token, TextSendMessage(text=reply))
                profile = await get_profile(userId, model.access_token)
                profile["question"] = message
                profile['answer'] = reply
                await db.insert_one(collection="messages_user", data=profile)
