import json
import time
import os
import requests
from typing import Optional
from config import BOT_CONFIG, SERVER_CONFIG, COOKIE_CACHE_FILE


class SessionManager:
    def __init__(self):
        self._cached_cookie: Optional[str] = None
        self._cookie_timestamp: float = 0
        self._load_cache()

    def _load_cache(self):
        if COOKIE_CACHE_FILE.exists():
            try:
                with open(COOKIE_CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._cached_cookie = data.get("cookie")
                    self._cookie_timestamp = data.get("timestamp", 0)
            except Exception:
                pass

    def _save_cache(self, cookie: str):
        try:
            with open(COOKIE_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "cookie": cookie,
                    "timestamp": time.time()
                }, f)
        except Exception as e:
            print(f"[Session] 保存cookie缓存失败: {e}")

    def _login(self) -> Optional[str]:
        username = BOT_CONFIG["username"]
        access_token = BOT_CONFIG["access_token"]
        login_url = SERVER_CONFIG["login_url"]

        session = requests.Session()
        login_json = {"access_token": access_token, "username": username}

        try:
            print(f"[Session] 尝试登录: {username}")
            response = session.post(login_url, data=login_json, timeout=10)
            print(f"[Session] 登录响应: HTTP {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"[Session] 登录JSON: {data}")
                    if not data.get("success", False):
                        print("[Session] 登录失败: API返回success为false")
                        return None
                except Exception as json_err:
                    print(f"[Session] 解析登录响应JSON失败: {json_err}")
                
                cookies = session.cookies.get_dict()
                print(f"[Session] 获取到的cookies: {cookies}")
                if "session" in cookies:
                    cookie_str = "session=" + cookies["session"]
                    print("[Session] 登录成功，获取新session")
                    return cookie_str
                else:
                    print("[Session] 登录失败: 未获取到session cookie")
            else:
                print(f"[Session] 登录失败: HTTP {response.status_code}, 响应文本: {response.text[:100]}")
        except Exception as e:
            print(f"[Session] 登录请求异常: {e}")
        return None

    def _validate_cookie(self, cookie: str) -> bool:
        http_base = SERVER_CONFIG["http_base"]
        test_url = f"{http_base}/api/user"

        try:
            response = requests.get(test_url, headers={"Cookie": cookie}, timeout=5)
            print(f"[Session] 验证cookie: HTTP {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"[Session] 验证响应: {data}")
                    return data.get("success", False) if "success" in data else True
                except Exception as e:
                    print(f"[Session] 解析JSON失败: {e}")
                    return True
            return False
        except Exception as e:
            print(f"[Session] 验证请求异常: {e}")
            return False

    def get_session(self, force_refresh: bool = False) -> Optional[str]:
        if not force_refresh and self._cached_cookie:
            if self._cookie_timestamp and (time.time() - self._cookie_timestamp) < 7776000:
                if self._validate_cookie(self._cached_cookie):
                    return self._cached_cookie
                else:
                    print("[Session] 缓存cookie验证失败，尝试重新登录")
        cookie = self._login()
        if cookie:
            self._cached_cookie = cookie
            self._cookie_timestamp = time.time()
            self._save_cache(cookie)
        return cookie

    def invalidate(self):
        self._cached_cookie = None
        self._cookie_timestamp = 0
        if COOKIE_CACHE_FILE.exists():
            COOKIE_CACHE_FILE.unlink()


session_manager = SessionManager()
