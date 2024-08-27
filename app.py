import os

import aiohttp
import chainlit as cl
import json

import requests

dify_base_url = os.environ["DIFY_BASE_URL"]
dify_api_key = os.environ["DIFY_API_KEY"]


@cl.on_chat_start
def start_chat():
    cl.user_session.set("message_history", [])


@cl.on_message
async def main(message: cl.Message):
    message_history = cl.user_session.get("message_history")
    message_history = message_history[-8:]
    message_history.append({"role": "user", "content": message.content, "content_type": "text"})
    msg = cl.Message(content="")
    url = f"{dify_base_url}/chat-messages"
    headers = {
        "Authorization": f"Bearer {dify_api_key}",
        "Content-Type": "application/json"
    }
    print(headers)
    data = {
        "inputs": {},
        "query": message.content,
        "user": "tarzan",
        "conversation_id": "",
        "response_mode": "streaming",
        "files": []
    }
    async for delta in fetch_sse(url, headers=headers, data=json.dumps(data)):
        task_id = delta.get("task_id", '')
        cl.user_session.set("task_id",task_id)
        await msg.stream_token(delta.get("answer", ''))
    await msg.send()


# message_history.append({"role": "assistant", "type": "answer", "content": msg.content, "content_type": "text"})


@cl.on_stop
def on_stop():
    print("The user wants to stop the task!")
    task_id = cl.user_session.get("task_id")
    print('task_id-------', task_id)
    if task_id:
        url = f"{dify_base_url}/chat-messages/{task_id}/stop"
        print('url', url)
        headers = {
            "Authorization": f"Bearer {dify_api_key}",
            "Content-Type": "application/json"
        }
        print(headers)
        data = {"user": "tarzan"}
        with requests.post(
                url,
                headers=headers,
                data=data,
        ) as resp:
            print('resp',resp.content)


async def fetch_sse(url, headers, data):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=data) as response:
            async for line in response.content:
                if line:  # 过滤掉空行
                    data = line.decode('utf-8').rstrip('\n\r')
                    print(f"Received: {line}")
                    # 检查是否为事件类型行
                    if data.startswith('data:'):
                        data = data.split(':', 1)[1].strip()  # 提取数据内容
                        # 如果数据包含换行符，可能需要进一步处理（这取决于你的具体需求）
                        # 这里我们简单地打印出来
                        # print(f"Received data for event 'conversation.message.delta': {data}")
                        yield json.loads(data)

