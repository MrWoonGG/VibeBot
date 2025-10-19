import threading
import queue
import time
from typing import Any, Callable
from mysql.connector import pooling
from pydantic import BaseModel
from config import DB_CFG

class LRUCache:
    def __init__(self, max_size=128, ttl=60):
        self.max_size = max_size
        self.ttl = ttl
        self.cache = {}
        self.access_time = {}

    def get(self, key):
        if key in self.cache:
            if time.time() - self.access_time[key] < self.ttl:
                self.access_time[key] = time.time()
                return self.cache[key]
            else:
                self.delete(key)
        return None

    def set(self, key, value):
        if len(self.cache) >= self.max_size:
            oldest = min(self.access_time, key=lambda k: self.access_time[k])
            self.delete(oldest)
        self.cache[key] = value
        self.access_time[key] = time.time()

    def delete(self, key):
        if key in self.cache:
            del self.cache[key]
            del self.access_time[key]

    def clear(self):
        self.cache.clear()
        self.access_time.clear()

class DB:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.pool = pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=10,
            host=DB_CFG['host'],
            user=DB_CFG['user'],
            password=DB_CFG['password'],
            database=DB_CFG['database'],
            autocommit=True
        )
        self.cache = LRUCache(max_size=256, ttl=60)
        self.queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    @classmethod
    def get(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = cls()
        return cls._instance

    def _worker(self):
        while True:
            func, args, kwargs, result_holder = self.queue.get()
            try:
                result = func(*args, **kwargs)
                if result_holder is not None:
                    result_holder["result"] = result
            except Exception as e:
                if result_holder is not None:
                    result_holder["error"] = e
            self.queue.task_done()

    def _run_sync(self, func, *args, **kwargs):
        result_holder = {}
        self.queue.put((func, args, kwargs, result_holder))
        while "result" not in result_holder and "error" not in result_holder:
            time.sleep(0.001)
        if "error" in result_holder:
            raise result_holder["error"]
        return result_holder["result"]

    def get_cursor(self):
        conn = self.pool.get_connection()
        return conn, conn.cursor(dictionary=True)

    def query(self, sql: str, args: tuple = (), use_cache=False, cache_key=None) -> Any:
        def do_query():
            if use_cache and cache_key:
                cached = self.cache.get(cache_key)
                if cached is not None:
                    return cached
            conn, cursor = self.get_cursor()
            try:
                cursor.execute(sql, args)
                result = cursor.fetchall()
            finally:
                cursor.close()
                conn.close()
            if use_cache and cache_key:
                self.cache.set(cache_key, result)
            return result

        return self._run_sync(do_query)

    def execute(self, sql: str, args: tuple = ()) -> None:
        def do_execute():
            conn, cursor = self.get_cursor()
            try:
                cursor.execute(sql, args)
                conn.commit()
            finally:
                cursor.close()
                conn.close()

        self._run_sync(do_execute)

    def clear_cache(self):
        self.cache.clear()
