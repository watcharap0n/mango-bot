import json
from db import db
from typing import Optional, Any
from linebot import LineBotApi
from models.notification import Post, TokenUser
from oauth2 import User, get_current_active
from fastapi import APIRouter, HTTPException, Depends, status, Body
from fastapi.responses import JSONResponse
from models.callback import LineToken, Webhook, UpdateLineToken
from modules.item_static import item_user
from modules.flex_message import flex_dynamic, content_card_dynamic
from linebot.exceptions import LineBotApiError
from linebot.models import TextSendMessage
from fastapi.encoders import jsonable_encoder

router = APIRouter()

collection = 'notifications'


async def check_access_token(payload: Post,
                             current_user: User = Depends(get_current_active)):
    try:
        line_bot_api = LineBotApi(payload.access_token)
        line_bot_api.get_bot_info()
        return payload
    except LineBotApiError as ex:
        raise HTTPException(status_code=ex.status_code, detail=ex.message)


async def post_content(payload: Post = Depends(check_access_token),
                       current_user: User = Depends(get_current_active)):
    local_collection = 'card'
    line_bot_api = LineBotApi(payload.access_token)

    if payload.flex_status:
        if payload.id_card:
            card = await db.find_one(collection=local_collection,
                                     query={'uid': current_user.data.uid, '_id': payload.id_card})
            if not card:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail={f'Not found {payload.id_card}'})
            content = json.loads(card.get('content'))
            flex_msg = flex_dynamic(alt_text=card.get('name'), contents=content)
            line_bot_api.push_message(payload.user_id, flex_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='No content flex message')

    line_bot_api.push_message(payload.user_id, TextSendMessage(text=payload.message))
    item_model = jsonable_encoder(payload)
    item_model = item_user(data=item_model, current_user=current_user)
    await db.insert_one(collection=collection, data=item_model)
    item_store = TokenUser(**item_model)
    return item_store


@router.post('/post/any', response_model=TokenUser)
async def post_any(notify: Post = Depends(post_content),
                   current_user: User = Depends(get_current_active)):
    keys = notify.content.keys()
    values = notify.content.values()
    content_default = notify.config_default_card
    func, content = content_card_dynamic(
        header=content_default.header,
        image=content_default.image,
        path_image=content_default.path_image,
        footer=content_default.footer,
        body_key=keys,
        body_value=values,
        name_btn=content_default.name_btn,
        url_btn=content_default.url_btn,
    )
    line_bot_api = LineBotApi(notify.access_token)
    line_bot_api.push_message(notify.user_id, func)
    item_model = jsonable_encoder(notify)
    item_model = item_user(data=item_model, current_user=current_user)
    await db.insert_one(collection=collection, data=item_model)
    item_store = TokenUser(**item_model)
    return item_store


@router.post('/post/condition/form')
async def post_any_form(
        id: str,
        payload: Optional[Any] = Body(None)):
    channel = await db.find_one('notification_webhook', query={'forms._id': id}, select_field={'_id': 0})
    if channel:
        keys = []
        data_table = await db.find('data_table', query={'access_token': channel.get('base_access_token')})
        for data in data_table:
            if data['value'] in payload.keys():
                keys.append(data['text'])
        values = payload.values()
        func, content = content_card_dynamic(
            body_key=keys,
            body_value=values,
        )
        line_bot_api = LineBotApi(channel.get('access_token'))
        line_bot_api.broadcast(func)
    return channel


@router.get('/find/webhook', response_model=Webhook)
async def get_webhook_notification(id: str, current_user: User = Depends(get_current_active)):
    notification = await db.find_one(collection='notification_webhook',
                                     query={'base_access_token': id})
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"not found channel {id}",
        )
    item_store = Webhook(**notification)
    return item_store


@router.post('/create/webhook', response_model=Webhook)
async def create_notification(payload: LineToken, current_user: User = Depends(get_current_active)):
    try:
        line_bot_api = LineBotApi(payload.access_token)
        bot_info = line_bot_api.get_bot_info()
        item_model = jsonable_encoder(payload)
        item_model = item_user(data=item_model, current_user=current_user, url=True)
        item_model["bot_info"] = bot_info
        item_model = jsonable_encoder(item_model)
        await db.insert_one('notification_webhook', data=item_model)
        item_store = Webhook(**item_model)
        return item_store
    except LineBotApiError as ex:
        raise HTTPException(status_code=ex.status_code, detail=ex.message)


@router.put('/update/webhook/{token}', response_model=UpdateLineToken)
async def update_notification(
        token: str,
        payload: LineToken,
        id_form: Optional[str] = None,
        current_user: User = Depends(get_current_active)
):
    try:
        line_bot_api = LineBotApi(payload.access_token)
        line_bot_api.get_bot_info()
        item_model = jsonable_encoder(payload)
        query = {'token': token}
        values = {'$set': item_model}

        if id_form:
            item = await db.find_one('notification_webhook', query={'token': token,
                                                                    'forms._id': id_form})
            if item:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='form is duplicate')

        if (await db.update_one('notification_webhook', query=query, values=values)) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Callback not found {token} or Update Already exits",
            )
        return payload
    except LineBotApiError as ex:
        raise HTTPException(status_code=ex.status_code, detail=ex.message)


@router.delete('/delete/webhook/{token}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(token: str, current_user: User = Depends(get_current_active)):
    if (await db.delete_one(collection='notification_webhook', query={"token": token})) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Callback not found {token} or Delete Already exits",
        )
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)
