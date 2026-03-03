import asyncio
import websockets
import json
import time
import requests
import api4agent
from typing import Optional
from session_manager import session_manager
from config import BOT_CONFIG, SERVER_CONFIG, CONNECTION_CONFIG


def get_history_json(room):
    cookie = session_manager.get_session()
    if cookie is None:
        print("[History] 无法获取session cookie")
        return None

    http_base = SERVER_CONFIG["http_base"]
    history_url = f"{http_base}/api/room/{room}/export?limit=all"
    
    try:
        response = requests.get(history_url, headers={"Cookie": cookie}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success", False):
                return data.get("messages", [])
            else:
                print("[History] API返回success为false")
                return None
        else:
            print(f"[History] 获取历史记录失败: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"[History] 获取历史记录异常: {e}")
        return None


async def run(room: Optional[str] = None):
    room_name = room or BOT_CONFIG["room"]
    ws_base = SERVER_CONFIG["ws_base"]
    heartbeat_interval = CONNECTION_CONFIG["heartbeat_interval"]
    buffer_max = CONNECTION_CONFIG["message_buffer_max"]
    memory_interval = CONNECTION_CONFIG["memory_interval"]

    
    retry_attempt = 0
    base_delay = CONNECTION_CONFIG["initial_retry_delay"]
    max_delay = CONNECTION_CONFIG["max_retry_delay"]

    msg_buffer = []

    while True:
        msg_count = 0
        dlt_count = 0
        cookie = session_manager.get_session(force_refresh=False)
        if cookie is None:
            delay = min(base_delay * (2 ** retry_attempt), max_delay)
            print(f"[Connection] 无法获取session，{delay}秒后重试... (attempt {retry_attempt})")
            retry_attempt += 1
            await asyncio.sleep(delay)
            continue

        ws_url = f"{ws_base}/{room_name}"
        request_head = {"Cookie": cookie}
        print(f"[Connection] 连接WebSocket: {ws_url}")

        try:
            async with websockets.connect(ws_url, additional_headers=request_head) as ws:
                print(f"[Connection] 已连接到房间: {room_name}")
                retry_attempt = 0
                last_ping = time.time()

                async for raw_msg in ws:
                    msg_count+=1
                    print('msg_count',msg_count)
                    try:
                        if time.time() - last_ping > heartbeat_interval:
                            await ws.ping()
                            last_ping = time.time()

                        msg_data = json.loads(raw_msg)

                        if isinstance(msg_data, list):
                            msg_buffer.extend(msg_data)
                        else:
                            msg_buffer.append(msg_data)

                        if len(msg_buffer) > buffer_max:
                            #从51开始触发
                            dlt_count += len(msg_buffer) - buffer_max
                            print('dlt_count', dlt_count)
                            msg_buffer = msg_buffer[-buffer_max:]
                            print('buffer长度:',len(msg_buffer))
                        already_read = (msg_count - dlt_count) == len(msg_buffer) and msg_count>=51    #51前不允许通过，51后满足条件才通过
                        print(f'准备进入的语句为:{msg_buffer[-1]['text']}')
                        print(already_read)
                        if  msg_buffer[-1].get("sender_username") != "EnderDragon" and already_read:
                            print(f'通过循环的语句为:{msg_buffer[-1]['text']}')
                            ident = api4agent.dragon_eyes( msg_buffer )
                            dragon_msg = None

                            if ident == "yes":
                                dragon_msg = api4agent.dragon_speaking( msg_buffer )
                                await ws.send(dragon_msg)
                                print(f"[Bot] 发送回复: {dragon_msg}")
                            
                            
                        
                            if (msg_count - (msg_count // memory_interval) *memory_interval) == 0:
                                print(f"[Memory] 已处理 {msg_count} 条消息，正在总结记忆...")
                                await asyncio.to_thread(api4agent.memory_conclude, msg_buffer)
                                print("[Memory] 记忆总结完成")

                    except json.JSONDecodeError:
                        print(f"[Parse] JSON解析错误: {raw_msg[:50]}")
                    except Exception as e:
                        print(f"[Process] 处理消息异常: {e}")

        except websockets.exceptions.ConnectionClosed as e:
            print(f"[Connection] WebSocket断开: {e.code} - {e.reason}")
            if e.code in [1008, 1003]:
                print("[Connection] 身份验证失败，清除session")
                session_manager.invalidate()
            else:
                print("[Connection] 连接因非认证原因断开，保留session")
            retry_attempt += 1

        except Exception as e:
            print(f"[Connection] WebSocket异常: {e}")
            retry_attempt += 1

        delay = min(base_delay * (2 ** retry_attempt), max_delay)
        print(f"[Connection] {delay}秒后重连... (attempt {retry_attempt})")
        await asyncio.sleep(delay)


def impression_get(room="minecraft"):
    content = get_history_json(room)
    if content is None:
        print("[Memory] 获取历史记录失败，无法进行记忆总结")
        return
    api4agent.memory_conclude(content)


if __name__ == "__main__":
    asyncio.run(run())
