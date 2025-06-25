#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : downloader.py

import aiohttp
import asyncio
import aiosqlite
import os
import time
import random
import orjson  # 比json更快的JSON库
from fake_useragent import UserAgent
from typing import List, Set, Dict, Any
import logging
import ssl
import certifi
from aiohttp_retry import RetryClient, ExponentialRetry
import functools
import concurrent.futures

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 配置参数
MAX_RETRIES = 3  # 最大重试次数
DB_POOL_SIZE = 5  # 数据库连接池大小，调整为更小的值，因为是单文件下载

# 内存缓存，减少数据库操作
ID_CACHE = {
    "ok_ids": set(),
    "fail_ids": set(),
    "last_update": 0
}

# 创建数据库连接池
db_pool = None
DB_PATH = os.path.expanduser("~/.nber_cli_state.db") # 数据库路径，放在用户主目录下

async def create_db_pool():
    """创建数据库连接池"""
    global db_pool
    if db_pool is None:
        db_pool = [await aiosqlite.connect(DB_PATH) for _ in range(DB_POOL_SIZE)]

async def close_db_pool():
    """关闭数据库连接池"""
    if db_pool:
        for conn in db_pool:
            await conn.close()

async def get_db_conn():
    """从连接池中获取一个数据库连接"""
    return random.choice(db_pool)

async def init_db():
    """初始化数据库"""
    conn = await get_db_conn()
    try:
        await conn.execute(
            """CREATE TABLE IF NOT EXISTS paper_state (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        await conn.commit()
    finally:
        pass # 不关闭连接，因为它是从连接池中获取的

async def load_ids_from_db():
    """从数据库加载已处理的ID到内存缓存"""
    conn = await get_db_conn()
    try:
        async with conn.execute("SELECT id, status FROM paper_state") as cursor:
            async for row in cursor:
                if row[1] == 'ok':
                    ID_CACHE["ok_ids"].add(row[0])
                else:
                    ID_CACHE["fail_ids"].add(row[0])
        ID_CACHE["last_update"] = time.time()
        logger.info(f"Loaded {len(ID_CACHE['ok_ids'])} ok ids and {len(ID_CACHE['fail_ids'])} fail ids from db.")
    finally:
        pass

async def get_paper_state(paper_id: str) -> str:
    """获取特定论文的下载状态"""
    if paper_id in ID_CACHE["ok_ids"]:
        return "ok"
    if paper_id in ID_CACHE["fail_ids"]:
        return "fail"
    return None

async def update_paper_state(paper_id: str, status: str):
    """更新论文的下载状态"""
    conn = await get_db_conn()
    try:
        await conn.execute(
            "INSERT OR REPLACE INTO paper_state (id, status) VALUES (?, ?)",
            (paper_id, status)
        )
        await conn.commit()
        if status == 'ok':
            ID_CACHE["ok_ids"].add(paper_id)
            if paper_id in ID_CACHE["fail_ids"]:
                ID_CACHE["fail_ids"].remove(paper_id)
        else:
            ID_CACHE["fail_ids"].add(paper_id)
            if paper_id in ID_CACHE["ok_ids"]:
                ID_CACHE["ok_ids"].remove(paper_id)
    finally:
        pass

async def download_paper(paper_id: str, save_path: str):
    """下载单个NBER论文"""
    filepath = os.path.join(save_path, f"{paper_id}.pdf")

    # 确保保存路径存在
    os.makedirs(save_path, exist_ok=True)

    state = await get_paper_state(paper_id)
    if state == 'ok' and os.path.exists(filepath):
        logger.info(f"Skipping {paper_id}, already downloaded.")
        return
    if state == 'ok' and not os.path.exists(filepath):
        logger.info(f"{paper_id} marked as downloaded but file missing, re-downloading.")

    url = f"https://www.nber.org/papers/{paper_id}.pdf"

    ua = UserAgent()
    headers = {'User-Agent': ua.random}
    retry_options = ExponentialRetry(attempts=MAX_RETRIES)
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    try:
        async with RetryClient(retry_options=retry_options, headers=headers) as session:
            async with session.get(url, timeout=30, ssl=ssl_context) as response:
                if response.status == 200:
                    content = await response.read()
                    with open(filepath, 'wb') as f:
                        f.write(content)
                    logger.info(f"Successfully downloaded {paper_id} to {filepath}")
                    await update_paper_state(paper_id, 'ok')
                else:
                    logger.error(f"Failed to download {paper_id}, status code: {response.status}")
                    await update_paper_state(paper_id, 'fail')
    except Exception as e:
        logger.error(f"An error occurred while downloading {paper_id}: {e}")
        await update_paper_state(paper_id, 'fail')

async def main_download(paper_id: str, save_path: str):
    """主下载函数，用于CLI调用"""
    await create_db_pool()
    await init_db()
    await load_ids_from_db()
    await download_paper(paper_id, save_path)
    await close_db_pool()


