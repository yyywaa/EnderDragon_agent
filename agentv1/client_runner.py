import asyncio
import websockets
import json
import time
import requests
import api4agent
from typing import Optional
from session_manager import session_manager
from config import BOT_CONFIG, SERVER_CONFIG, CONNECTION_CONFIG
ids ={}
def msg_judge(msg_dict):
    if not isinstance(msg_dict, dict):
        msg = msg_dict[-1]
    else:
        msg = msg_dict
    msg_id = msg.get("msg_id", None)
    if msg_id is None:
        return False
    else:
        if msg_id in ids.keys():
            return False
        else:
            return time_judge(msg_dict)

def time_judge(msg_dict):
    if not isinstance(msg_dict, dict):
        msg = msg_dict[-1]
    else:
        msg = msg_dict
    msg_time_raw = msg.get("timestamp")
    
    if msg_time_raw is None:
        return False
    else:
        msg_time = int(msg_time_raw)//1000
        now = time.time()
        if now - msg_time > 60:
            return False
        return True


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

    while True:
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
                msg_count = 0
                dlt_count = 0
                retry_attempt = 0
                msg_buffer =[]
                last_ping = time.time()

                async for raw_msg in ws:
                    try:
                        if time.time() - last_ping > heartbeat_interval:
                            await ws.ping()
                            last_ping = time.time()

                        msg_data = json.loads(raw_msg)

                        # 过滤有效聊天消息（必须有text字段）
                        valid_messages = []
                        if isinstance(msg_data, list):
                            for msg in msg_data:
                                if isinstance(msg, dict) and 'text' in msg:
                                    valid_messages.append(msg)
                        elif isinstance(msg_data, dict) and 'text' in msg_data:
                            valid_messages.append(msg_data)
                        
                        if not valid_messages:
                            continue  # 没有有效聊天消息，跳过后续处理
                        
                        # 只对有效聊天消息计数
                        msg_count += len(valid_messages)
                        print('msg_count', msg_count)
                        
                        # 添加到缓冲区
                        msg_buffer.extend(valid_messages)

                        if len(msg_buffer) > buffer_max:
                            #从51开始触发
                            dlt_count += len(msg_buffer) - buffer_max
                            print('dlt_count', dlt_count)
                            msg_buffer = msg_buffer[-buffer_max:]
                            print('buffer长度:',len(msg_buffer))
                        
                        # 使用最后一条有效消息进行判断
                        last_msg = msg_buffer[-1]
                        already_read = (msg_count - dlt_count) == len(msg_buffer) and msg_count>=51 and msg_judge(last_msg)
                           #51前不允许通过，51后满足条件才通过
                        print(f'准备进入的语句为:{last_msg['text']}')
                        print(already_read)
                        if  last_msg.get("sender_username") != "EnderDragon" and already_read:
                            print(f'通过循环的语句为:{last_msg['text']}')
                            ident = api4agent.dragon_eyes( msg_buffer )
                            read_id = last_msg['msg_id']
                            ids[read_id] = ident
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
    impression_get()
    asyncio.run(run())
