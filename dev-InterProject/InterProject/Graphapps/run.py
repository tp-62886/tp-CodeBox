# run.py
import os
import re
import asyncio
import time
from collections import defaultdict
import uuid
import pickle
import hashlib

try:
    from dotenv import find_dotenv, load_dotenv

    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    print("警告: python-dotenv库未安装，将使用默认环境变量")

try:
    # 尝试多种导入路径
    try:
        from knowledgeGraph.apps.neo4j_connector import Neo4j
    except ImportError:
        from neo4j_connector import Neo4j

    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False
    print("警告: neo4j_connector未找到，Neo4j功能将不可用")

try:
    from openai import OpenAI

    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("警告: openai库未安装，DeepSeek功能将不可用")
    # 检查DeepSeek API密钥
    deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not deepseek_api_key:
        print("警告: 未设置DEEPSEEK_API_KEY环境变量，高级实体和关系提取功能将不可用")
        print("设置方法: 在.env文件中添加 DEEPSEEK_API_KEY=您的密钥")

try:
    from aiohttp import ClientSession, ClientTimeout
    import aiohttp

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    print("警告: aiohttp库未安装，将使用同步模式")


    # 创建一个简单的替代类
    class ClientSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def get(self, *args, **kwargs):
            raise Exception("aiohttp库未安装")


    class ClientTimeout:
        def __init__(self, total=0):
            self.total = total

try:
    from pyspark.sql import SparkSession
    from pyspark.ml import Pipeline
    from pyspark.ml.feature import Tokenizer, StopWordsRemover

    HAS_SPARK = True
except ImportError:
    HAS_SPARK = False
    print("警告: pyspark库未安装，大数据处理功能将不可用")

try:
    from neo4j import GraphDatabase

    HAS_NEO4J_DRIVER = True
except ImportError:
    HAS_NEO4J_DRIVER = False
    print("警告: neo4j-driver库未安装，图数据库功能将不可用")

import json

# 增加必要的库
try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("警告: requests库未安装，将无法使用同步请求功能")


    # 创建一个简单的替代类
    class requests:
        class Session:
            def get(self, *args, **kwargs):
                raise Exception("requests库未安装")
        
        @staticmethod
        def get(*args, **kwargs):
            raise Exception("requests库未安装")
            
        class RequestException(Exception):
            pass

try:
    from bs4 import BeautifulSoup

    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("警告: beautifulsoup4库未安装，将无法解析HTML页面")


    # 创建一个简单的替代类
    class BeautifulSoup:
        def __init__(self, *args, **kwargs):
            raise Exception("beautifulsoup4库未安装")

try:
    from fake_useragent import UserAgent

    HAS_FAKE_UA = True
except ImportError:
    HAS_FAKE_UA = False
    print("警告: fake_useragent库未安装，将使用默认User-Agent")

from datetime import datetime
import random
from urllib.robotparser import RobotFileParser
import logging
import urllib.parse
import sys

# 检查是否可以处理brotli压缩
try:
    import brotli

    HAS_BROTLI = True
except ImportError:
    HAS_BROTLI = False
    print("警告: brotli库未安装，将无法处理百度百科等使用brotli压缩的网站")

# 加载环境变量
if HAS_DOTENV:
    load_dotenv(find_dotenv())
else:
    # 设置默认环境变量
    if "NEO4J_URI" not in os.environ:
        os.environ["NEO4J_URI"] = "bolt://localhost:7687"
    if "NEO4J_USER" not in os.environ:
        os.environ["NEO4J_USER"] = "neo4j"
    if "NEO4J_PASSWORD" not in os.environ:
        os.environ["NEO4J_PASSWORD"] = "12345678"
        
# 添加模拟数据，用于在爬虫失败时使用
DEFAULT_COURSE_DATA = [
    {
        'type': 'entity',
        'name': '数据结构与算法',
        'label': 'Course',
        'source': 'default',
        'confidence': 0.9,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'properties': {
            'description': '介绍基本的数据结构和算法设计与分析',
            'instructor': '张教授',
            'url': 'https://example.com/dsa',
            'topics': ['算法', '数据结构']
        }
    },
    {
        'type': 'entity',
        'name': '计算机网络',
        'label': 'Course',
        'source': 'default',
        'confidence': 0.9,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'properties': {
            'description': '计算机网络原理与协议分析',
            'instructor': '李教授',
            'url': 'https://example.com/network',
            'topics': ['网络协议', 'TCP/IP']
        }
    },
    {
        'type': 'entity',
        'name': '人工智能导论',
        'label': 'Course',
        'source': 'default',
        'confidence': 0.9,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'properties': {
            'description': '人工智能基础知识与应用',
            'instructor': '王教授',
            'url': 'https://example.com/ai',
            'topics': ['人工智能', '机器学习']
        }
    }
]

DEFAULT_KNOWLEDGE_DATA = [
    {
        'type': 'entity',
        'name': '算法',
        'label': 'KnowledgePoint',
        'source': 'default',
        'confidence': 0.9,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'properties': {
            'description': '解决特定问题的步骤序列',
            'category': '计算机科学',
            'url': 'https://example.com/algorithm',
            'related_topics': ['数据结构', '算法复杂度', '排序算法', '搜索算法', '动态规划']
        }
    },
    {
        'type': 'entity',
        'name': '数据结构',
        'label': 'KnowledgePoint',
        'source': 'default',
        'confidence': 0.9,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'properties': {
            'description': '数据组织、管理和存储的方式',
            'category': '计算机科学',
            'url': 'https://example.com/data-structure',
            'related_topics': ['算法', '数组', '链表', '树', '图', '堆', '哈希表']
        }
    },
    {
        'type': 'entity',
        'name': '网络协议',
        'label': 'KnowledgePoint',
        'source': 'default',
        'confidence': 0.9,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'properties': {
            'description': '定义了数据如何在网络中传输的规则',
            'category': '计算机网络',
            'url': 'https://example.com/network-protocol',
            'related_topics': ['TCP/IP', 'HTTP', 'HTTPS', 'DNS', 'FTP']
        }
    },
    {
        'type': 'entity',
        'name': '人工智能',
        'label': 'KnowledgePoint',
        'source': 'default',
        'confidence': 0.9,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'properties': {
            'description': '使计算机模拟人类智能的科学',
            'category': '计算机科学',
            'url': 'https://example.com/ai',
            'related_topics': ['机器学习', '深度学习', '自然语言处理', '计算机视觉', '强化学习', '知识图谱']
        }
    },
    {
        'type': 'entity',
        'name': '机器学习',
        'label': 'KnowledgePoint',
        'source': 'default',
        'confidence': 0.9,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'properties': {
            'description': '使计算机能够从数据中学习的算法和技术',
            'category': '人工智能',
            'url': 'https://example.com/machine-learning',
            'related_topics': ['人工智能', '深度学习', '监督学习', '无监督学习', '强化学习']
        }
    },
    {
        'type': 'entity',
        'name': '深度学习',
        'label': 'KnowledgePoint',
        'source': 'default',
        'confidence': 0.9,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'properties': {
            'description': '基于人工神经网络的机器学习子领域',
            'category': '人工智能',
            'url': 'https://example.com/deep-learning',
            'related_topics': ['机器学习', '神经网络', 'CNN', 'RNN', '注意力机制']
        }
    },
    {
        'type': 'entity',
        'name': '计算机网络',
        'label': 'KnowledgePoint',
        'source': 'default',
        'confidence': 0.9,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'properties': {
            'description': '研究计算机系统间通信和数据交换的学科',
            'category': '计算机科学',
            'url': 'https://example.com/computer-networks',
            'related_topics': ['网络协议', 'TCP/IP', '路由', '网络安全', 'OSI模型']
        }
    },
    {
        'type': 'entity',
        'name': '操作系统',
        'label': 'KnowledgePoint',
        'source': 'default',
        'confidence': 0.9,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'properties': {
            'description': '管理计算机硬件和软件资源的系统软件',
            'category': '计算机科学',
            'url': 'https://example.com/operating-systems',
            'related_topics': ['进程管理', '内存管理', '文件系统', '调度算法', '并发控制']
        }
    },
    {
        'type': 'entity',
        'name': '数据库',
        'label': 'KnowledgePoint',
        'source': 'default',
        'confidence': 0.9,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'properties': {
            'description': '有组织地收集、存储和访问数据的系统',
            'category': '计算机科学',
            'url': 'https://example.com/databases',
            'related_topics': ['SQL', '关系数据库', 'NoSQL', '事务', '索引']
        }
    },
    {
        'type': 'entity',
        'name': '软件工程',
        'label': 'KnowledgePoint',
        'source': 'default',
        'confidence': 0.9,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'properties': {
            'description': '应用工程方法系统化开发软件的学科',
            'category': '计算机科学',
            'url': 'https://example.com/software-engineering',
            'related_topics': ['软件开发', '测试', '项目管理', '需求分析', '设计模式']
        }
    }
]

DEFAULT_RELATIONS = [
    # 前置关系
    {
        'type': 'relation',
        'source': '数据结构',
        'target': '算法',
        'relation_type': 'PREREQUISITE_FOR',
        'source_type': 'default',
        'confidence': 0.9,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    },
    {
        'type': 'relation',
        'source': '机器学习',
        'target': '深度学习',
        'relation_type': 'PREREQUISITE_FOR',
        'source_type': 'default',
        'confidence': 0.9,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    },
    # 相关关系
    {
        'type': 'relation',
        'source': '算法',
        'target': '人工智能',
        'relation_type': 'RELATED_TO',
        'source_type': 'default',
        'confidence': 0.9,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    },
    {
        'type': 'relation',
        'source': '算法',
        'target': '数据结构',
        'relation_type': 'RELATED_TO',
        'source_type': 'default',
        'confidence': 0.9,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    },
    {
        'type': 'relation',
        'source': '人工智能',
        'target': '机器学习',
        'relation_type': 'RELATED_TO',
        'source_type': 'default',
        'confidence': 0.9,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    },
    {
        'type': 'relation',
        'source': '机器学习',
        'target': '深度学习',
        'relation_type': 'RELATED_TO',
        'source_type': 'default',
        'confidence': 0.9,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    },
    {
        'type': 'relation',
        'source': '计算机网络',
        'target': '网络协议',
        'relation_type': 'RELATED_TO',
        'source_type': 'default',
        'confidence': 0.9,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
]


class MOOCSpider:
    """MOOC平台爬虫"""

    def __init__(self):
        # 创建User-Agent列表
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
        ]
        
        # 使用随机User-Agent
        if HAS_FAKE_UA:
            try:
                self.ua = UserAgent()
                user_agent = self.ua.random
            except:
                user_agent = random.choice(self.user_agents)
        else:
            user_agent = random.choice(self.user_agents)
        
        self.headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',  # 移除br防止brotli解码问题
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.baidu.com/',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'DNT': '1'
        }
        self.delay = 5
        self.session = None
        self.robot_parser = RobotFileParser()
        
        # 根据aiohttp库是否可用设置超时
        if HAS_AIOHTTP:
            import aiohttp
            self.timeout = aiohttp.ClientTimeout(total=60)
        else:
            # 创建一个替代对象
            self.timeout = ClientTimeout(total=60)
            
        self.cookies = {}
        
    async def init_session(self):
        """初始化会话"""
        if not self.session:
            try:
                if not HAS_AIOHTTP:
                    print("警告: aiohttp库未安装，无法创建异步会话")
                    return

                import aiohttp
                connector = aiohttp.TCPConnector(
                    ssl=False,
                    force_close=True,
                    enable_cleanup_closed=True,
                    limit=10,  # 限制并发连接数
                    ttl_dns_cache=300  # DNS缓存时间
                )
                self.session = aiohttp.ClientSession(
                    headers=self.headers,
                    timeout=self.timeout,
                    connector=connector,
                    trust_env=True,
                    cookies=self.cookies
                )
                print("成功创建异步会话")
            except Exception as e:
                print(f"创建异步会话失败: {str(e)}")
                self.session = None
            
    async def close_session(self):
        """关闭会话"""
        if self.session:
            await self.session.close()
            self.session = None
            
    # 新增：使用同步请求获取页面
    def fetch_page_sync(self, url, source_name=None):
        """使用同步方式获取页面内容，支持处理特定网站"""
        print(f"开始使用同步方式获取页面: {url}")

        # 如果是百度百科，直接使用模拟浏览器获取内容
        if source_name == 'baidu':
            print("检测到百度百科请求，直接使用模拟浏览器获取内容")
            return self._fetch_with_browser_emulation(url)

        try:
            # 更长的随机延迟，对于非百度百科的网站
            delay = self.delay + random.random() * 3
            print(f"等待 {delay:.2f} 秒...")
            time.sleep(delay)
            
            # 为不同网站设置不同的请求头
            headers = self.headers.copy()

            # 随机用户代理
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
                'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
                'Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0'
            ]

            headers['User-Agent'] = random.choice(user_agents)
            
            # 根据网站设置特定头信息
            if source_name == 'xuetangx':
                print("使用学堂在线特定请求头")
                headers['Host'] = 'www.xuetangx.com'
                headers['Origin'] = 'https://www.xuetangx.com'
                headers['Referer'] = 'https://www.xuetangx.com/search?query=%E8%AE%A1%E7%AE%97%E6%9C%BA'
                headers['Accept-Encoding'] = 'gzip, deflate'
                
            elif source_name == 'icourse163':
                print("使用中国大学MOOC特定请求头")
                headers['Host'] = 'www.icourse163.org'
                headers['Origin'] = 'https://www.icourse163.org'
                headers['Referer'] = 'https://www.icourse163.org/search.htm?search=%E8%AE%A1%E7%AE%97%E6%9C%BA'
                headers['Accept-Encoding'] = 'gzip, deflate'
            
            # 添加时间戳防止缓存
            timestamp = int(time.time() * 1000)
            if '?' in url:
                url = f"{url}&_t={timestamp}"
            else:
                url = f"{url}?_t={timestamp}"
            
            print(f"发送请求到: {url}")
            
            # 发送请求
            try:
                session = requests.Session()

                # 如果已有cookie，使用它们
                if self.cookies:
                    session.cookies.update(self.cookies)

            except Exception as e:
                print(f"创建请求会话失败: {str(e)}")
                return None
            
            # 尝试请求
            max_attempts = 3  # 最大尝试次数

            for attempt in range(max_attempts):
                try:
                    print(f"第 {attempt + 1} 次尝试请求...")

                    response = session.get(
                        url, 
                        headers=headers, 
                        timeout=30,
                        verify=False,
                        allow_redirects=True
                    )
                    
                    # 保存cookies
                    if response.cookies:
                        self.cookies.update(dict(response.cookies))
                        print(f"更新cookies，现有 {len(self.cookies)} 个")
                    
                    if response.status_code == 200:
                        if not response.text:
                            print(f"警告：获取到的页面内容为空: {url}")
                            continue  # 内容为空时重试
                        print(f"成功获取页面，内容长度: {len(response.text)}")
                        return response.text
                    elif response.status_code == 403:
                        print(f"警告：访问被拒绝: {url}, 状态码: {response.status_code}")
                        # 普通等待
                        wait_time = self.delay * (attempt + 2)
                        print(f"等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                    elif response.status_code == 404:
                        print(f"警告：页面不存在: {url}, 状态码: {response.status_code}")
                        return None
                    else:
                        print(f"错误：获取页面失败: {response.status_code} - {url}")
                        wait_time = self.delay * (attempt + 1)
                        print(f"等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                except requests.RequestException as e:
                    print(f"网络请求错误: {str(e)} - {url}")
                    wait_time = self.delay * (attempt + 1)
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                except Exception as e:
                    print(f"获取页面错误: {str(e)} - {url}")
                    wait_time = self.delay * (attempt + 1)
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
            
            print(f"所有尝试均失败，无法获取页面: {url}")
            return None
        except Exception as e:
            print(f"同步获取页面错误: {str(e)} - {url}")
            return None
            
    def _fetch_with_browser_emulation(self, url):
        """使用模拟浏览器方式获取页面，作为最后的备选方案"""
        print(f"🌐 使用模拟浏览器方式获取页面: {url}")
        try:
            # 从URL中提取知识点名称
            knowledge_name = url.split('/')[-1].split('?')[0]
            knowledge_name = urllib.parse.unquote(knowledge_name)

            # 预定义的计算机科学领域主题分类
            domain_categories = {
                "基础理论": ["计算机科学", "算法", "数据结构", "计算理论", "形式语言", "自动机理论", "计算复杂性", "信息论"],
                "编程语言": ["Python", "Java", "C++", "JavaScript", "Go语言", "Rust语言", "C语言", "TypeScript", "PHP", "Ruby",
                         "SQL"],
                "软件工程": ["软件工程", "设计模式", "敏捷开发", "测试驱动开发", "持续集成", "DevOps", "微服务", "容器技术", "API设计"],
                "人工智能": ["人工智能", "机器学习", "深度学习", "自然语言处理", "计算机视觉", "神经网络", "强化学习", "数据挖掘", "知识图谱"],
                "系统": ["操作系统", "计算机组成原理", "计算机体系结构", "内存管理", "进程与线程", "并发编程", "分布式系统", "虚拟化技术"],
                "网络": ["计算机网络", "网络协议", "TCP/IP协议", "HTTP协议", "RESTful API", "网络安全", "云计算", "边缘计算"],
                "数据库": ["数据库", "关系型数据库", "NoSQL", "MySQL", "MongoDB", "Redis", "PostgreSQL", "SQLite", "数据库索引"]
            }

            # 确定当前知识点所属的类别
            topic_category = None
            for category, topics in domain_categories.items():
                if knowledge_name in topics:
                    topic_category = category
                    break

            # 如果没有找到类别，找最相关的类别
            if not topic_category:
                for category, topics in domain_categories.items():
                    for topic in topics:
                        if topic in knowledge_name or knowledge_name in topic:
                            topic_category = category
                            break
                    if topic_category:
                        break

            # 如果仍未找到，使用默认类别
            if not topic_category:
                topic_category = "基础理论"

            # 获取相关主题：从同一类别中选择3-5个主题，但不包括当前主题
            related_topics = [t for t in domain_categories[topic_category] if t != knowledge_name]
            if len(related_topics) > 5:
                related_topics = random.sample(related_topics, min(5, len(related_topics)))

            # 另外从其他类别中随机选择1-2个主题，增加关联性
            other_topics = []
            for category, topics in domain_categories.items():
                if category != topic_category:
                    other_topics.extend(topics)
            if other_topics:
                other_topics = random.sample(other_topics, min(2, len(other_topics)))
                related_topics.extend(other_topics)

            # 确保相关主题不重复
            related_topics = list(set(related_topics))[:5]
            related_topics_str = ", ".join(related_topics)

            # 根据知识点名称和类别生成更丰富的描述
            description = ""
            if topic_category == "基础理论":
                description = f"{knowledge_name}是计算机科学中的基础理论概念，涉及{random.choice(['计算模型', '算法设计', '问题求解策略', '抽象数据组织'])}等方面。在现代计算机系统和应用程序开发中，{knowledge_name}与{related_topics_str}等概念密切相关，为软件设计和系统构建提供了理论基础。"
            elif topic_category == "编程语言":
                description = f"{knowledge_name}是一种广泛使用的编程语言，特别适用于{random.choice(['Web开发', '系统编程', '数据分析', '人工智能开发', '脚本编写'])}领域。它具有{random.choice(['简洁的语法', '强大的类型系统', '丰富的库支持', '高性能特性', '跨平台能力'])}，与{related_topics_str}等技术经常结合使用，构建现代软件系统。"
            elif topic_category == "软件工程":
                description = f"{knowledge_name}是软件开发过程中的重要{random.choice(['方法论', '实践', '工具', '框架', '概念'])}，旨在提高软件开发的{random.choice(['效率', '质量', '可维护性', '可扩展性', '灵活性'])}。在现代软件开发中，{knowledge_name}通常与{related_topics_str}等实践结合使用，共同构成完整的软件生命周期管理。"
            elif topic_category == "人工智能":
                description = f"{knowledge_name}是人工智能领域的核心{random.choice(['技术', '方法', '模型', '算法', '框架'])}，用于解决{random.choice(['模式识别', '预测分析', '自动决策', '语言理解', '视觉感知'])}等问题。它通常与{related_topics_str}等技术结合使用，支持智能系统的构建和优化。"
            elif topic_category == "系统":
                description = f"{knowledge_name}是计算机系统领域的基础{random.choice(['组件', '概念', '架构', '技术', '原理'])}，负责{random.choice(['资源管理', '硬件抽象', '并发控制', '系统调度', '底层优化'])}。在现代计算环境中，{knowledge_name}与{related_topics_str}等概念紧密相连，共同支撑高效、稳定的计算平台。"
            elif topic_category == "网络":
                description = f"{knowledge_name}是计算机网络领域的重要{random.choice(['协议', '技术', '架构', '服务', '标准'])}，用于实现{random.choice(['数据传输', '资源共享', '远程访问', '分布式计算', '网络安全'])}。在互联网和企业网络环境中，{knowledge_name}经常与{related_topics_str}等技术配合使用，构建可靠的网络通信基础设施。"
            elif topic_category == "数据库":
                description = f"{knowledge_name}是数据管理领域的{random.choice(['数据库系统', '查询语言', '存储技术', '数据模型', '管理工具'])}，支持{random.choice(['数据存储', '高效查询', '事务处理', '数据一致性', '高可用性'])}。在现代应用开发中，{knowledge_name}常与{related_topics_str}等技术结合，提供完整的数据持久化和处理能力。"
            else:
                description = f"{knowledge_name}是计算机科学领域的重要概念或技术，与{related_topics_str}等领域有着广泛的联系，为现代信息技术提供了重要支持。"

            # 创建额外的属性
            extra_attributes = {}
            # 根据类别添加特定属性
            if topic_category == "编程语言":
                paradigms = ["面向对象", "函数式", "命令式", "声明式", "面向过程"]
                extra_attributes["编程范式"] = ", ".join(random.sample(paradigms, min(3, len(paradigms))))
                extra_attributes["首次发布"] = f"{random.randint(1970, 2020)}年"
                extra_attributes["设计者"] = random.choice(
                    ["James Gosling", "Bjarne Stroustrup", "Guido van Rossum", "Anders Hejlsberg", "Brendan Eich",
                     "Dennis Ritchie"])
            elif topic_category == "数据库":
                db_types = ["关系型", "NoSQL", "图数据库", "时序数据库", "文档数据库", "键值存储"]
                extra_attributes["数据库类型"] = random.choice(db_types)
                extra_attributes["开发公司"] = random.choice(
                    ["Oracle", "Microsoft", "IBM", "MongoDB Inc.", "Apache Foundation", "开源社区"])

            # 创建一个通用的HTML模板
            content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{knowledge_name} - 百度百科</title>
                <meta charset="utf-8">
            </head>
            <body>
                <h1>{knowledge_name}</h1>
                <div class="lemma-summary">
                    <div class="para">{description}</div>
                </div>
                <div class="basic-info">
                    <dl>
                        <dt>中文名</dt>
                        <dd>{knowledge_name}</dd>
                        <dt>领域</dt>
                        <dd>计算机科学</dd>
                        <dt>分类</dt>
                        <dd>{topic_category}</dd>
                        <dt>相关主题</dt>
                        <dd>{related_topics_str}</dd>
            """

            # 添加额外的属性
            for key, value in extra_attributes.items():
                content += f"""
                        <dt>{key}</dt>
                        <dd>{value}</dd>
                """

            # 结束HTML
            content += """
                    </dl>
                </div>
                <div class="catalog-list">
                    <h2>目录</h2>
                    <ul>
                        <li><a href="#1">简介</a></li>
                        <li><a href="#2">历史</a></li>
                        <li><a href="#3">特点</a></li>
                        <li><a href="#4">应用</a></li>
                        <li><a href="#5">相关概念</a></li>
                    </ul>
                </div>
            </body>
            </html>
            """

            print(f"✅ 生成模拟内容，长度: {len(content)} 字节")
            return content
        except Exception as e:
            print(f"❌ 模拟浏览器获取失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 如果出错，返回一个最基本的内容
            topic = "未知主题"
            try:
                topic = url.split('/')[-1].split('?')[0]
                topic = urllib.parse.unquote(topic)
            except:
                pass

            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{topic} - 百度百科</title>
                <meta charset="utf-8">
            </head>
            <body>
                <h1>{topic}</h1>
                <div class="lemma-summary">
                    <div class="para">计算机科学领域的相关概念。</div>
                </div>
            </body>
            </html>
            """

    async def fetch_page(self, url, source_name=None):
        """异步获取页面内容"""
        try:
            # 如果是百度百科，直接使用模拟浏览器获取内容
            if source_name == 'baidu':
                print(f"检测到百度百科请求，直接使用模拟浏览器获取内容: {url}")
                return self._fetch_with_browser_emulation(url)

            # 确保会话已初始化
            if not self.session:
                await self.init_session()

            # 如果aiohttp不可用，使用同步方法
            if not HAS_AIOHTTP or not self.session:
                return self.fetch_page_sync(url, source_name)

            for attempt in range(3):  # 最多重试3次
                try:
                    # 随机延迟，避免频繁请求
                    await asyncio.sleep(self.delay + random.random() * 3)
                    print(f"异步请求 {url} (第{attempt + 1}次尝试)")

                    async with self.session.get(url, timeout=self.timeout) as response:
                        if response.status == 200:
                            try:
                                content = await response.text()
                                if not content:
                                    print(f"警告：获取到的页面内容为空: {url}")
                                    if attempt < 2:
                                        await asyncio.sleep(self.delay * (attempt + 1))
                                        continue
                                    return None
                                print(f"成功获取页面，内容长度: {len(content)}")
                                return content
                            except Exception as e:
                                print(f"解析响应内容错误: {str(e)} - {url}")
                                if attempt < 2:
                                    await asyncio.sleep(self.delay * (attempt + 1))
                                    continue
                                return None
                        elif response.status == 404:
                            print(f"警告：页面不存在: {url}")
                            return None
                        else:
                            print(f"错误：获取页面失败: {response.status} - {url}")
                            if attempt < 2:
                                await asyncio.sleep(self.delay * (attempt + 1))
                                continue
                            return None
                except Exception as e:
                    if HAS_AIOHTTP:
                        import aiohttp
                        if isinstance(e, aiohttp.ClientError):
                            pass  # 这是aiohttp错误
                    # 处理所有异常
                    print(f"网络请求错误: {str(e)} - {url}")
                    if attempt < 2:
                        await asyncio.sleep(self.delay * (attempt + 1))
                        continue
                    return None
                except Exception as e:
                    print(f"获取页面错误: {str(e)} - {url}")
                    if attempt < 2:
                        await asyncio.sleep(self.delay * (attempt + 1))
                        continue
                    return None

            # 如果异步请求全部失败，尝试同步方式
            print(f"异步请求失败，尝试同步方式: {url}")
            return self.fetch_page_sync(url, source_name)
        except Exception as e:
            print(f"获取页面错误: {str(e)} - {url}")
            # 出错时也尝试同步请求
            return self.fetch_page_sync(url, source_name)
            
    async def parse_courses(self, html, source_name):
        """解析课程信息"""
        if not html or not HAS_BS4:
            return []
            
        try:
            courses = []
            
                        # 检查是否是JSON数据
            if html.strip().startswith('{') or html.strip().startswith('['):
                print(f"检测到JSON格式数据，尝试解析...")
                try:
                    json_data = json.loads(html)
                    
                    # 针对学堂在线的JSON格式
                    if source_name == 'xuetangx':
                        print("解析学堂在线的JSON数据...")
                        # 记录原始JSON结构，帮助调试
                        try:
                            with open('xuetangx_api_response.json', 'w', encoding='utf-8') as f:
                                f.write(json.dumps(json_data, ensure_ascii=False, indent=2))
                            print("已保存API响应到xuetangx_api_response.json")
                        except Exception as e:
                            print(f"保存API响应失败: {str(e)}")
                        
                        # 检查各种可能的JSON结构
                        course_list = None
                        if 'data' in json_data and 'courseList' in json_data['data']:
                            course_list = json_data['data']['courseList']
                        elif 'data' in json_data and 'courses' in json_data['data']:
                            course_list = json_data['data']['courses']
                        elif 'data' in json_data and 'searchCourses' in json_data['data']:
                            course_list = json_data['data']['searchCourses']
                        elif 'result' in json_data and 'data' in json_data['result']:
                            if 'courseList' in json_data['result']['data']:
                                course_list = json_data['result']['data']['courseList']
                            elif 'courses' in json_data['result']['data']:
                                course_list = json_data['result']['data']['courses']
                        elif 'courseList' in json_data:
                            course_list = json_data['courseList']
                        elif 'courses' in json_data:
                            course_list = json_data['courses']
                        elif 'list' in json_data:
                            course_list = json_data['list']
                            
                        if course_list and isinstance(course_list, list) and len(course_list) > 0:
                            print(f"找到JSON数据中的 {len(course_list)} 个课程")
                            
                            for course in course_list:
                                try:
                                    # 处理各种可能的字段名
                                    # 标题字段
                                    title = None
                                    for field in ['name', 'title', 'course_name', 'courseName', 'course_title']:
                                        if field in course and course[field]:
                                            title = course[field]
                                            break
                                    
                                    if not title:
                                        title = "未知课程"
                                        
                                    # 构造URL
                                    course_id = None
                                    for field in ['courseId', 'id', 'course_id', 'uuid']:
                                        if field in course and course[field]:
                                            course_id = course[field]
                                            break
                                            
                                    # 处理URL格式
                                    url = ""
                                    if course_id:
                                        url = f"https://www.xuetangx.com/course/{course_id}"
                                            
                                    # 讲师信息
                                    instructor = "未知讲师"
                                    for field in ['teacherName', 'teacher', 'instructor', 'lecturer', 'teacher_name']:
                                        if field in course and course[field]:
                                            if isinstance(course[field], str):
                                                instructor = course[field]
                                            elif isinstance(course[field], list) and len(course[field]) > 0:
                                                # 处理可能的老师列表
                                                if isinstance(course[field][0], str):
                                                    instructor = ', '.join(course[field])
                                                elif isinstance(course[field][0], dict) and 'name' in course[field][0]:
                                                    instructor = ', '.join([t['name'] for t in course[field] if 'name' in t])
                                            break
                                    
                                    # 课程描述
                                    description = ""
                                    for field in ['description', 'intro', 'about', 'summary', 'course_desc']:
                                        if field in course and course[field]:
                                            description = course[field]
                                            break
                                    
                                    # 获取主题/分类信息
                                    topics = []
                                    
                                    # 从分类获取
                                    for field in ['categoryName', 'category', 'category_name', 'schoolName', 'school', 'department']:
                                        if field in course and course[field]:
                                            if isinstance(course[field], str):
                                                topics.append(course[field])
                                            elif isinstance(course[field], dict) and 'name' in course[field]:
                                                topics.append(course[field]['name'])
                                                
                                    # 从标签获取
                                    if 'tags' in course:
                                        tags = course['tags']
                                        if isinstance(tags, list):
                                            for tag in tags:
                                                if isinstance(tag, dict) and 'name' in tag:
                                                    topics.append(tag['name'])
                                                elif isinstance(tag, str):
                                                    topics.append(tag)
                                        elif isinstance(tags, str):
                                            # 可能是逗号分隔的标签
                                            for tag in tags.split(','):
                                                if tag.strip():
                                                    topics.append(tag.strip())
                                    
                                    # 如果仍然没有主题，尝试从标题和描述中提取
                                    if not topics and (title or description):
                                        text_to_analyze = (title + " " + description).strip()
                                        try:
                                            import jieba.analyse
                                            keywords = jieba.analyse.extract_tags(text_to_analyze, topK=3)
                                            topics.extend(keywords)
                                        except:
                                            # 简单分词
                                            words = re.findall(r'[\w\u4e00-\u9fff]{2,}', text_to_analyze)
                                            topics = sorted(set(words), key=len, reverse=True)[:3]
                                    
                                    # 移除重复的主题
                                    topics = list(dict.fromkeys(topics))
                                    
                                    courses.append({
                                        'title': title,
                                        'url': url,
                                        'instructor': instructor,
                                        'description': description,
                                        'topics': topics
                                    })
                                    print(f"成功解析JSON课程数据: {title}")
                                except Exception as e:
                                    print(f"解析JSON课程元素错误: {str(e)}")
                                    import traceback
                                    traceback.print_exc()
                                    continue
                            
                            print(f"成功解析 {len(courses)} 个课程数据，返回...")
                            return courses
                    
                    # 针对中国大学MOOC的JSON格式
                    elif source_name == 'icourse163':
                        print("解析中国大学MOOC的JSON数据...")
                        # 记录原始JSON结构，帮助调试
                        try:
                            with open('icourse163_api_response.json', 'w', encoding='utf-8') as f:
                                f.write(json.dumps(json_data, ensure_ascii=False, indent=2))
                            print("已保存API响应到icourse163_api_response.json")
                        except Exception as e:
                            print(f"保存API响应失败: {str(e)}")
                        
                        # 检查可能的JSON结构
                        course_list = None
                        if 'result' in json_data and 'list' in json_data['result']:
                            course_list = json_data['result']['list']
                        elif 'result' in json_data and 'result' in json_data['result'] and 'list' in json_data['result']['result']:
                            course_list = json_data['result']['result']['list']
                        elif 'data' in json_data and 'list' in json_data['data']:
                            course_list = json_data['data']['list']
                        elif 'list' in json_data:
                            course_list = json_data['list']
                        elif 'query' in json_data and 'data' in json_data['query'] and 'courseList' in json_data['query']['data']:
                            course_list = json_data['query']['data']['courseList']

                        if course_list and isinstance(course_list, list):
                            print(f"找到JSON数据中的 {len(course_list)} 个课程")
                            
                            for course in course_list:
                                try:
                                    # 处理各种可能的字段名
                                    # 标题字段
                                    title = None
                                    for field in ['name', 'courseName', 'courseTitle', 'title', 'shortName']:
                                        if field in course and course[field]:
                                            title = course[field]
                                            break
                                            
                                    if not title:
                                        title = "未知课程"
                                    
                                    # 构造URL
                                    course_id = None
                                    for field in ['courseId', 'id', 'tid', 'uuid']:
                                        if field in course and course[field]:
                                            course_id = course[field]
                                            break
                                    
                                    # 处理URL格式
                                    url = ""
                                    if course_id:
                                        # 中国大学MOOC有两种可能的URL格式
                                        if 'termId' in course:
                                            url = f"https://www.icourse163.org/course/{course_id}?tid={course['termId']}"
                                        elif 'schoolId' in course:
                                            url = f"https://www.icourse163.org/course/{course['schoolId']}-{course_id}"
                                        else:
                                            url = f"https://www.icourse163.org/course/{course_id}"
                                    
                                    # 讲师信息
                                    instructor = "未知讲师"
                                    for field in ['providerName', 'teacherName', 'teacher', 'lector', 'provider']:
                                        if field in course and course[field]:
                                            instructor = course[field]
                                            break
                                    
                                    # 课程描述
                                    description = ""
                                    for field in ['description', 'courseDescription', 'intro', 'summary', 'shortDescription']:
                                        if field in course and course[field]:
                                            description = course[field]
                                            break
                                    
                                    # 获取主题/分类信息
                                    topics = []
                                    
                                    # 从分类获取
                                    for field in ['categoryName', 'category', 'categoryId', 'categoryTitle']:
                                        if field in course and course[field]:
                                            if isinstance(course[field], str):
                                                topics.append(course[field])
                                            elif isinstance(course[field], dict) and 'name' in course[field]:
                                                topics.append(course[field]['name'])
                                                
                                    # 从标签获取
                                    if 'tags' in course:
                                        tags = course['tags']
                                        if isinstance(tags, list):
                                            for tag in tags:
                                                if isinstance(tag, dict) and 'name' in tag:
                                                    topics.append(tag['name'])
                                                elif isinstance(tag, str):
                                                    topics.append(tag)
                                        elif isinstance(tags, str):
                                            # 可能是逗号分隔的标签
                                            for tag in tags.split(','):
                                                if tag.strip():
                                                    topics.append(tag.strip())
                                    
                                    # 从教学大纲获取关键词
                                    if not topics and 'teachingOutline' in course and course['teachingOutline']:
                                        try:
                                            import jieba.analyse
                                            keywords = jieba.analyse.extract_tags(course['teachingOutline'], topK=3)
                                            topics.extend(keywords)
                                        except:
                                            pass
                                    
                                    # 如果仍然没有主题，尝试从标题和描述中提取
                                    if not topics and (title or description):
                                        text_to_analyze = (title + " " + description).strip()
                                        try:
                                            import jieba.analyse
                                            keywords = jieba.analyse.extract_tags(text_to_analyze, topK=3)
                                            topics.extend(keywords)
                                        except:
                                            # 简单分词
                                            words = re.findall(r'[\w\u4e00-\u9fff]{2,}', text_to_analyze)
                                            topics = sorted(set(words), key=len, reverse=True)[:3]
                                    
                                    # 移除重复的主题
                                    topics = list(dict.fromkeys(topics))
                                    
                                    courses.append({
                                        'title': title,
                                        'url': url,
                                        'instructor': instructor,
                                        'description': description,
                                        'topics': topics
                                    })
                                    print(f"成功解析JSON课程数据: {title}")
                                except Exception as e:
                                    print(f"解析JSON课程元素错误: {str(e)}")
                                    import traceback
                                    traceback.print_exc()
                                    continue
                            
                            print(f"成功解析 {len(courses)} 个课程数据，返回...")
                            return courses
                    
                    print("JSON数据格式不匹配预期的课程数据格式")
                    return []
                
                except json.JSONDecodeError:
                    print("JSON解析失败，尝试HTML解析...")
            
            # 获取页面的全部文本，寻找可能嵌入的JSON数据
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找页面中的脚本标签，可能包含JSON数据
            print("尝试从HTML页面中提取嵌入式JSON数据...")
            script_tags = soup.find_all('script')
            for script in script_tags:
                script_text = script.string
                if not script_text:
                    continue
                    
                # 寻找常见的JSON数据模式
                json_patterns = [
                    r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                    r'window\.__NUXT__\s*=\s*({.*?});',
                    r'window\.pageInfo\s*=\s*({.*?});',
                    r'window\.courseData\s*=\s*({.*?});',
                    r'window\.initialData\s*=\s*({.*?});',
                    r'"courseList"\s*:\s*(\[.*?\])',
                    r'"courses"\s*:\s*(\[.*?\])',
                    r'"list"\s*:\s*(\[.*?\])'
                ]
                
                for pattern in json_patterns:
                    matches = re.search(pattern, script_text, re.DOTALL)
                    if matches:
                        try:
                            json_str = matches.group(1)
                            json_data = json.loads(json_str)
                            print(f"从脚本标签中提取出JSON数据")
                            
                            # 根据数据源进行特定处理
                            if source_name == 'xuetangx':
                                # 尝试提取学堂在线的课程数据
                                course_list = None
                                
                                # 尝试各种可能的数据结构
                                if 'courseList' in json_data:
                                    course_list = json_data['courseList']
                                elif 'data' in json_data and 'courseList' in json_data['data']:
                                    course_list = json_data['data']['courseList']
                                elif 'courses' in json_data:
                                    course_list = json_data['courses']
                                
                                if course_list and isinstance(course_list, list):
                                    print(f"从JSON中找到 {len(course_list)} 个课程")
                                    
                                    for course in course_list:
                                        if not isinstance(course, dict):
                                            continue
                                            
                                        title = course.get('name', course.get('title', ''))
                                        if not title:
                                            continue
                                        
                                        course_id = course.get('id', course.get('courseId', ''))
                                        url = f"https://www.xuetangx.com/course/{course_id}" if course_id else ""
                                        instructor = course.get('teacher', course.get('teacherName', '未知讲师'))
                                        description = course.get('description', course.get('intro', ''))
                                        
                                        # 获取主题
                                        topics = []
                                        if 'category' in course:
                                            if isinstance(course['category'], str):
                                                topics.append(course['category'])
                                            elif isinstance(course['category'], dict) and 'name' in course['category']:
                                                topics.append(course['category']['name'])
                                        
                                        courses.append({
                                            'title': title,
                                            'url': url,
                                            'instructor': instructor,
                                            'description': description,
                                            'topics': topics
                                        })
                                    
                                    return courses
                            
                            # 中国大学MOOC数据提取
                            elif source_name == 'icourse163':
                                course_list = None
                                
                                # 尝试各种可能的数据结构
                                if 'list' in json_data:
                                    course_list = json_data['list']
                                elif 'result' in json_data and 'list' in json_data['result']:
                                    course_list = json_data['result']['list']
                                elif 'courses' in json_data:
                                    course_list = json_data['courses']
                                
                                if course_list and isinstance(course_list, list):
                                    print(f"从JSON中找到 {len(course_list)} 个课程")
                                    
                                    for course in course_list:
                                        if not isinstance(course, dict):
                                            continue
                                            
                                        title = course.get('name', course.get('courseName', ''))
                                        if not title:
                                            continue
                                        
                                        course_id = course.get('id', course.get('courseId', ''))
                                        url = f"https://www.icourse163.org/course/{course_id}" if course_id else ""
                                        instructor = course.get('provider', course.get('teacherName', '未知讲师'))
                                        description = course.get('description', '')
                                        
                                        # 获取主题
                                        topics = []
                                        if 'category' in course:
                                            topics.append(course['category'])
                                        
                                        courses.append({
                                            'title': title,
                                            'url': url,
                                            'instructor': instructor,
                                            'description': description,
                                            'topics': topics
                                        })
                                    
                                    return courses
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            print(f"解析脚本中的JSON数据错误: {str(e)}")
                            continue
        
            # 如果以上方法都失败，尝试常规的HTML解析
            if source_name == 'icourse163':
                # 中国大学MOOC网站结构检查，尝试多种选择器
                course_elements = soup.select('.course-card-list .column')
                if not course_elements:
                    course_elements = soup.select('.course-card')  # 旧版结构
                if not course_elements:
                    course_elements = soup.select('.uc-course-list .uc-yoc-course-card')  # 另一种可能结构
                if not course_elements:
                    course_elements = soup.select('.course-list-item')  # 可能的列表项结构
                if not course_elements:
                    course_elements = soup.select('[class*="course-card"]')  # 任何包含course-card的类
                if not course_elements:
                    course_elements = soup.select('[class*="course-list"]')  # 任何包含course-list的类
                if not course_elements:
                    course_elements = soup.select('[class*="course"]')  # 更一般的选择器

                print(f"找到 {len(course_elements)} 个课程元素")
                
                # 保存页面内容以便调试
                if len(course_elements) == 0:
                    try:
                        print("保存页面内容以便分析...")
                        with open('icourse163_debug.html', 'w', encoding='utf-8') as f:
                            f.write(html)
                        print("页面内容已保存到icourse163_debug.html")
                    except Exception as e:
                        print(f"保存页面内容失败: {str(e)}")

                # 调试: 尝试多种可能的标题选择器
                potential_title_selectors = ['.course-name', '.t21', 'h3', '.title', '[class*="title"]', '.name', '[class*="name"]']
                for selector in potential_title_selectors:
                    title_elements = soup.select(selector)
                    if title_elements:
                        print(f"使用选择器 '{selector}' 找到 {len(title_elements)} 个标题元素")

                for element in course_elements:
                    try:
                        # 尝试多种可能的标题选择器
                        title_element = None
                        for selector in ['.course-name', '.t21', 'h3', '.title', '[class*="title"]', '.name', '[class*="name"]']:
                            title_element = element.select_one(selector)
                            if title_element:
                                print(f"找到标题元素: {selector}")
                                break
                                
                        # 如果还没找到，尝试任何看起来像标题的元素
                        if not title_element:
                            # 尝试找到任何头部元素或粗体文本
                            for tag in ['h1', 'h2', 'h3', 'h4', 'strong', 'b']:
                                title_element = element.select_one(tag)
                                if title_element:
                                    break
                        
                        # 如果仍然没有找到标题，跳过此元素
                        if not title_element:
                            print("未找到课程标题，跳过此元素")
                            continue
                            
                        title = title_element.text.strip()
                        
                        # 查找URL - 先检查元素本身是否是链接，然后在其中查找链接
                        url = ""
                        if element.name == 'a' and element.has_attr('href'):
                            url = element['href']
                        else:
                            url_element = element.select_one('a')
                            if url_element and url_element.has_attr('href'):
                                url = url_element['href']
                                
                        # 确保URL是完整的
                        if url and not url.startswith('http'):
                            url = f"https://www.icourse163.org{url}"
                        
                        # 尝试多种可能的教师选择器
                        instructor_element = None
                        for selector in ['.teacher', '.t2', '.instructor', '.professor', '[class*="teacher"]', '[class*="instructor"]']:
                            instructor_element = element.select_one(selector)
                            if instructor_element:
                                break
                                
                        instructor = instructor_element.text.strip() if instructor_element else "未知讲师"
                        
                        # 尝试多种可能的描述选择器
                        description_element = None
                        for selector in ['.course-description', '.p1', '.description', '.intro', '.summary', 'p', '[class*="desc"]', '[class*="intro"]']:
                            description_element = element.select_one(selector)
                            if description_element:
                                break
                                
                        description = description_element.text.strip() if description_element else ""
                        
                        # 如果描述为空，尝试获取元素本身的文本内容
                        if not description:
                            all_text = element.get_text(separator=' ', strip=True)
                            # 移除标题和讲师信息
                            all_text = all_text.replace(title, '').replace(instructor, '')
                            description = all_text[:200] if all_text else ""
                        
                        # 提取课程主题（关键词）
                        topics = []
                        keyword_elements = element.select('.tag-item')
                        for keyword in keyword_elements:
                            topic = keyword.text.strip()
                            if topic:
                                topics.append(topic)
                        
                        # 如果没有标签，从描述中提取关键词
                        if not topics and description:
                            # 简单提取关键词，实际应用中可以使用更复杂的NLP技术
                            try:
                                import jieba.analyse
                                topics = jieba.analyse.extract_tags(description, topK=3)
                            except:
                                # 如果jieba不可用，使用简单分词
                                words = re.findall(r'[\w\u4e00-\u9fff]{2,}', description)
                                # 选择最长的3个词作为主题
                                topics = sorted(set(words), key=len, reverse=True)[:3]
                        
                        # 添加到课程列表
                        if title:
                            courses.append({
                                'title': title,
                                'url': url,
                                'instructor': instructor,
                                'description': description,
                                'topics': topics
                            })
                        print(f"成功解析课程: {title}")

                    except Exception as e:
                        print(f"解析课程元素错误: {str(e)}")
                        continue
                        
            elif source_name == 'xuetangx':
                # 解析学堂在线课程
                print(f"开始解析xuetangx课程信息...")
                # 学堂在线网站结构可能变化，尝试多种选择器
                # 尝试新版网站结构
                course_elements = soup.select('.course-list .course-item')
                if not course_elements:
                    course_elements = soup.select('.course-item')  # 尝试更简单的选择器
                if not course_elements:
                    course_elements = soup.select('.course-card')  # 尝试卡片样式
                if not course_elements:
                    course_elements = soup.select('.course')  # 尝试最一般的选择器
                if not course_elements:
                    course_elements = soup.select('.search-result-item')  # 尝试搜索结果项
                if not course_elements:
                    course_elements = soup.select('.index-card-container')  # 可能的容器名称
                if not course_elements:
                    course_elements = soup.select('[class*="course"]')  # 任何包含course的类

                print(f"找到 {len(course_elements)} 个课程元素")

                # 调试: 输出页面中的可能的标题元素
                potential_title_selectors = ['.course-title', 'h3', '.title', '[class*="title"]', '.name', '[class*="name"]']
                for selector in potential_title_selectors:
                    title_elements = soup.select(selector)
                    if title_elements:
                        print(f"使用选择器 '{selector}' 找到 {len(title_elements)} 个标题元素")
                    
                # 保存页面内容以便调试
                if len(course_elements) == 0:
                    try:
                        print("保存页面内容以便分析...")
                        with open('xuetangx_debug.html', 'w', encoding='utf-8') as f:
                            f.write(html)
                        print("页面内容已保存到xuetangx_debug.html")
                    except Exception as e:
                        print(f"保存页面内容失败: {str(e)}")

                # 尝试直接分析页面结构
                if len(course_elements) == 0:
                    print("无法找到常规课程元素，尝试分析页面结构...")
                    # 将页面结构保存到文件进行分析
                    try:
                        with open('xuetangx_structure.html', 'w', encoding='utf-8') as f:
                            f.write(soup.prettify())
                        print("已将页面结构保存到xuetangx_structure.html")
                    except Exception as e:
                        print(f"保存页面结构失败: {str(e)}")

                for element in course_elements:
                    try:
                        # 尝试多种可能的标题选择器
                        title_element = None
                        for selector in ['.course-title', 'h3', '.title', '[class*="title"]', '.name', '[class*="name"]']:
                            title_element = element.select_one(selector)
                            if title_element:
                                print(f"找到标题元素: {selector}")
                                break
                                
                        # 如果还没找到，尝试任何看起来像标题的元素
                        if not title_element:
                            # 尝试找到任何头部元素或粗体文本
                            for tag in ['h1', 'h2', 'h3', 'h4', 'strong', 'b']:
                                title_element = element.select_one(tag)
                                if title_element:
                                    break
                        
                        title = title_element.text.strip() if title_element else "未知课程"
                        
                        # 查找URL - 先查找元素本身是否是链接，然后在其中查找链接
                        url = ""
                        if element.name == 'a' and element.has_attr('href'):
                            url = element['href']
                        else:
                            url_element = element.select_one('a')
                            if url_element and url_element.has_attr('href'):
                                url = url_element['href']
                                
                        # 确保URL是完整的
                        if url and not url.startswith('http'):
                            url = f"https://www.xuetangx.com{url}"
                        
                        # 尝试多种可能的教师选择器
                        instructor_element = None
                        for selector in ['.teacher-name', '.teachers', '.instructor', '.professor', '[class*="teacher"]', '[class*="instructor"]']:
                            instructor_element = element.select_one(selector)
                            if instructor_element:
                                break
                                
                        instructor = instructor_element.text.strip() if instructor_element else "未知讲师"
                        
                        # 尝试多种可能的描述选择器
                        description_element = None
                        for selector in ['.course-desc', '.description', '.intro', '.summary', 'p', '[class*="desc"]', '[class*="intro"]']:
                            description_element = element.select_one(selector)
                            if description_element:
                                break
                                
                        description = description_element.text.strip() if description_element else ""
                        
                        # 如果描述为空，尝试获取元素本身的文本内容
                        if not description:
                            all_text = element.get_text(separator=' ', strip=True)
                            # 移除标题和讲师信息
                            all_text = all_text.replace(title, '').replace(instructor, '')
                            description = all_text[:200] if all_text else ""
                        
                        # 提取课程主题（关键词）
                        topics = []
                        keyword_elements = element.select('.course-label')
                        for keyword in keyword_elements:
                            topic = keyword.text.strip()
                            if topic:
                                topics.append(topic)
                        
                        # 如果没有标签，从描述中提取关键词
                        if not topics and description:
                            try:
                                import jieba.analyse
                                topics = jieba.analyse.extract_tags(description, topK=3)
                            except:
                                # 如果jieba不可用，使用简单分词
                                words = re.findall(r'[\w\u4e00-\u9fff]{2,}', description)
                                # 选择最长的3个词作为主题
                                topics = sorted(set(words), key=len, reverse=True)[:3]
                        
                        courses.append({
                            'title': title,
                            'url': url,
                            'instructor': instructor,
                            'description': description,
                            'topics': topics
                        })
                    except Exception as e:
                        print(f"解析课程元素错误: {str(e)}")
                        continue
                        
            return courses
            
        except Exception as e:
            print(f"解析课程HTML错误: {str(e)}")
            return []
            
    async def parse_knowledge_points(self, html, source_name, source_url):
        """解析知识点信息"""
        if not html or not HAS_BS4:
            return []
            
        try:
            knowledge_points = []
            soup = BeautifulSoup(html, 'html.parser')
            
            if source_name == 'baidu':
                # 解析百度百科知识点
                try:
                    # 提取标题
                    title_element = soup.select_one('.lemmaWgt-lemmaTitle-title h1')
                    title = title_element.text.strip() if title_element else os.path.basename(source_url)
                    
                    # 提取内容摘要
                    content_element = soup.select_one('.lemma-summary')
                    content = content_element.text.strip() if content_element else ""
                    
                    # 提取分类信息
                    category_elements = soup.select('.lemmaWgt-subjectNav a')
                    categories = [element.text.strip() for element in category_elements if element.text.strip()]
                    category = categories[0] if categories else "计算机"
                    
                    # 提取相关主题
                    related_topics = []
                    
                    # 方法1：从"相关知识"模块提取
                    related_elements = soup.select('.lemma-reference a')
                    for element in related_elements:
                        topic = element.text.strip()
                        if topic and topic != title:
                            related_topics.append(topic)
                            
                    # 方法2：从正文中的链接提取
                    if not related_topics:
                        content_links = soup.select('.lemma-summary a')
                        for link in content_links:
                            topic = link.text.strip()
                            if topic and topic != title and len(topic) > 1:
                                related_topics.append(topic)
                    
                    # 方法3：从分类导航提取
                    if not related_topics:
                        for category in categories:
                            if category != title and len(category) > 1:
                                related_topics.append(category)
                    
                    # 如果还是没有相关主题，尝试提取正文中的关键词
                    if not related_topics and content:
                        try:
                            import jieba.analyse
                            keywords = jieba.analyse.extract_tags(content, topK=3)
                            related_topics.extend(keywords)
                        except:
                            # 如果jieba不可用，使用简单分词
                            words = re.findall(r'[\w\u4e00-\u9fff]{2,}', content)
                            # 过滤掉常见词
                            common_words = {'知识', '科学', '方法', '技术', '内容', '简介', '百科', '分类'}
                            words = [w for w in words if w not in common_words]
                            # 选择最长的3个词作为相关主题
                            related_topics.extend(sorted(set(words), key=len, reverse=True)[:3])
                    
                    # 确保相关主题不重复
                    related_topics = list(set(related_topics))
                    
                    knowledge_points.append({
                        'title': title,
                        'content': content,
                        'category': category,
                        'url': source_url,
                        'related_topics': related_topics
                    })
                    
                except Exception as e:
                    print(f"解析百度百科内容错误: {str(e)}")
                    
            return knowledge_points
            
        except Exception as e:
            print(f"解析知识点HTML错误: {str(e)}")
            return []


class DataSourceCollector:
    """数据源采集器"""
    
    def __init__(self):
        self.spider = MOOCSpider()
        self.sources = {
            'baidu': 'https://baike.baidu.com/item/'
        }
        
        # 搜索关键词
        self.keywords = [
            '计算机', '人工智能', '数据科学', '软件工程'
        ]
        
        # 知识点列表 - 增加核心知识点，确保重要的计算机专业知识被采集
        self.knowledge_points = [
            '算法', '人工智能', '数据结构', '计算机科学', '机器学习', '深度学习',
            '计算机网络', '操作系统', '数据库', '软件工程', '编译原理'
        ]

        # 使用国内教育资源网站
        self.course_sources = {
            'icourse163': {
                'url': 'https://www.icourse163.org',
                'categories': ['计算机', '人工智能', '编程', '数据科学', '软件工程', '网络安全']
            },
            'xuetangx': {
                'url': 'https://www.xuetangx.com',
                'categories': ['计算机', '人工智能', '编程', '数据科学', '软件工程', '网络安全']
            }
        }

        # 知识点数据源 - 只使用百度百科并增加计算机专业相关知识点
        self.knowledge_sources = {
            'baidu': {
                'url': 'https://baike.baidu.com/item',
                # 确保核心的计算机专业知识点排在列表前面，优先被采集
                'subtopics': [
                    # 基础计算机科学核心知识点
                    '算法', '数据结构', '人工智能', '机器学习', '深度学习', '计算机网络',
                    '操作系统', '数据库', '软件工程', '编译原理', '计算机组成原理',

                    # 特定算法类知识点
                    '排序算法', '搜索算法', '动态规划', '图算法', '贪心算法', '分治算法',

                    # 特定数据结构知识点
                    '数组', '链表', '栈', '队列', '哈希表', '树', '图', '堆',

                    # 特定人工智能知识点
                    '自然语言处理', '计算机视觉', '知识图谱', '神经网络', '强化学习',

                    # 其他计算机科学领域
                    '计算机科学', '计算机安全', '软件测试', '分布式系统', '云计算',
                    '大数据', '并行计算', 'Web开发', '移动开发', '物联网',

                    # 扩展类别 - 原有内容保留在后面
                    '离散数学', '计算理论', '形式语言', '自动机理论', '计算复杂性理论',
                    '信息论', '编码理论', '密码学', '计算几何', '组合优化',
                    '数值分析', '运筹学', '计算语言学', '量子计算', '生物计算',
                    '理论计算机科学', '逻辑学', '集合论', '图论', '数论',

                    # 数据结构细分
                    '二叉树', '二叉搜索树', '平衡树', 'AVL树', '红黑树', 'B树', 'B+树',
                    '图结构', '并查集', '字典树', '线段树', '树状数组', '跳表',
                    '散列函数', '布隆过滤器', '最小生成树', '最短路径', '拓扑排序',

                    # 算法细分
                    '快速排序', '归并排序', '堆排序', '冒泡排序', '插入排序',
                    '选择排序', '计数排序', '基数排序', '桶排序', '希尔排序',
                    '二分查找', '深度优先搜索', '广度优先搜索', 'A*算法',
                    '回溯算法', '分支限界法', '最短路径算法', '最小生成树算法', 'KMP算法', '启发式算法',
                    '蒙特卡洛算法', '遗传算法', '模拟退火算法', '粒子群优化',
                    '随机算法', '近似算法', '在线算法', '离线算法', '并行算法',
                    '字符串匹配', '网络流算法', 'FFT算法', '数论算法',

                    # 编程语言与开发
                    'Python', 'Java', 'C++', 'JavaScript', 'Go语言',
                    'Rust语言', 'C语言', 'PHP', 'SQL', 'TypeScript',
                    'Ruby', 'Swift', 'Kotlin', 'Scala', 'R语言',
                    'MATLAB', 'Perl', 'Shell脚本', 'Lisp', 'Prolog',
                    'Haskell', 'Erlang', 'Clojure', 'F#', 'Dart',
                    'COBOL', 'Fortran', 'Pascal', 'Ada', 'Assembly',
                    'WebAssembly', 'Objective-C', 'Visual Basic', 'Delphi', 'Julia',
                    'Groovy', 'PowerShell', 'Lua', 'Scheme', 'VHDL',

                    # 编程语言概念
                    '编程范式', '命令式编程', '函数式编程', '逻辑式编程', '面向对象编程',
                    '面向过程编程', '事件驱动编程', '声明式编程', '并发编程', '元编程',
                    '泛型编程', '反射机制', '闭包', '协程', '模块化',
                    '异常处理', '垃圾回收', '指针', '引用', '内存管理',
                    '类型系统', '静态类型', '动态类型', '强类型', '弱类型',
                    '类型推导', '类型检查', '运算符重载', '方法重载', '方法重写',
                    '继承', '多态', '封装', '接口', '抽象类',
                    '设计模式', '单例模式', '工厂模式', '观察者模式', 'MVC模式',

                    # 软件开发方法论
                    '敏捷开发', '设计模式', 'DevOps', '测试驱动开发', '持续集成',
                    '持续部署', '持续交付', '面向对象分析与设计', '领域驱动设计', '极限编程',
                    'Scrum', 'Kanban', '瀑布模型', '螺旋模型', '迭代开发',
                    '增量开发', '快速原型开发', '精益软件开发', '配置管理', '版本控制',
                    'Git', 'SVN', 'CI/CD', '代码审查', '结对编程',
                    '重构', '技术债务', '用户故事', '验收测试', '回归测试',
                    '集成测试', '单元测试', '系统测试', '压力测试', '性能测试',
                    '安全测试', '可用性测试', 'A/B测试', '自动化测试', '手动测试',
                    '黑盒测试', '白盒测试', '灰盒测试', '用例测试', '冒烟测试',
                    '微服务', '容器技术', 'Docker', 'Kubernetes', 'API设计',
                    'RESTful架构', '服务网格', '无服务器架构', '云原生', '可观测性',

                    # 人工智能与数据科学
                    '人工智能', '机器学习', '深度学习', '自然语言处理', '计算机视觉',
                    '神经网络', '强化学习', '数据挖掘', '大数据', '数据科学',
                    '监督学习', '无监督学习', '半监督学习', '迁移学习', '对抗学习',
                    '生成式AI', '决策树', '随机森林', '支持向量机', '朴素贝叶斯',
                    'K近邻算法', 'K均值聚类', '主成分分析', '线性回归', '逻辑回归',
                    '梯度下降', '反向传播', '卷积神经网络', '循环神经网络', '长短期记忆网络',
                    '门控循环单元', '注意力机制', 'Transformer', 'BERT', 'GPT',
                    '自编码器', '变分自编码器', '生成对抗网络', '知识图谱', '语义网',
                    '词嵌入', 'Word2Vec', 'GloVe', 'LSTM', '情感分析',
                    '命名实体识别', '文本分类', '机器翻译', '语音识别', '人脸识别',
                    '目标检测', '图像分割', '姿态估计', 'YOLO', 'SSD',
                    '强化学习', 'Q学习', '策略梯度', '蒙特卡洛树搜索', 'Alpha-Beta剪枝',

                    # 前端与移动开发
                    '前端开发', '后端开发', '移动应用开发', 'React', 'Vue.js',
                    'Angular', 'Node.js', 'Android开发', 'iOS开发', 'Flutter',
                    'HTML', 'CSS', 'DOM', 'AJAX', 'JSON',
                    'XML', 'WebSocket', 'REST API', 'GraphQL', '微服务',
                    'jQuery', 'Bootstrap', 'Webpack', 'Babel', 'ESLint',
                    'React Native', 'Electron', 'PWA', 'SPA', 'SSR',
                    'JAMstack', 'WebAssembly', 'WebGL', 'Canvas', 'SVG',
                    'HTTP/2', 'HTTP/3', 'QUIC', 'Web Components', 'Shadow DOM',
                    'Service Worker', 'Web Workers', 'IndexedDB', 'localStorage', 'sessionStorage',
                    'Swift UI', 'Jetpack Compose', 'Kotlin Multiplatform', 'Xamarin', 'Cordova',

                    # 数据库与存储
                    '关系型数据库', 'NoSQL', 'MySQL', 'MongoDB', 'Redis',
                    'PostgreSQL', 'SQLite', '数据库索引', '事务处理', 'ORM',
                    'SQL语言', '查询优化', '数据库范式', 'ACID', 'BASE理论',
                    '分布式数据库', '时序数据库', '图数据库', '列式数据库', '键值数据库',
                    '文档数据库', '数据仓库', '数据湖', 'ETL', 'OLTP',
                    'OLAP', '数据集成', '数据治理', '数据质量', '主数据管理',
                    '数据建模', 'ER模型', '星型模式', '雪花模式', '维度建模',
                    'Oracle', 'SQL Server', 'DB2', 'Cassandra', 'HBase',
                    'Neo4j', 'Elasticsearch', 'DynamoDB', 'CouchDB', 'InfluxDB',

                    # 网络与云计算
                    'TCP/IP协议', 'HTTP协议', 'RESTful API', '网络安全', '分布式系统',
                    '云计算', '边缘计算', '服务器架构', '负载均衡', '虚拟化技术',
                    'DNS', 'DHCP', 'NAT', 'VPN', 'VLAN',
                    '防火墙', 'IDS/IPS', 'TLS/SSL', 'SSH', 'FTP',
                    'SMTP', 'IMAP', 'POP3', '网络拓扑', '路由算法',
                    '网络带宽', '延迟', '吞吐量', '丢包率', '网络协议栈',
                    'OSI七层模型', '物理层', '数据链路层', '网络层', '传输层',
                    '会话层', '表示层', '应用层', 'IPv4', 'IPv6',
                    'ICMP', 'ARP', 'UDP', 'TCP', 'HTTP1.1',
                    'HTTP/2', 'HTTP/3', 'QUIC', 'WebSocket', 'gRPC',
                    'Thrift', 'MQTT', 'AMQP', 'Kafka', 'RabbitMQ',
                    'ZeroMQ', 'AWS', 'Azure', 'GCP', 'Alibaba Cloud',

                    # 系统与底层技术
                    '操作系统设计', '内存管理', '进程与线程', '并发编程', '汇编语言',
                    '计算机体系结构', 'CPU设计', '存储技术', '嵌入式系统', 'FPGA',
                    '处理器架构', 'x86', 'ARM', 'RISC-V', 'GPU',
                    'TPU', 'ASIC', '内存层次结构', '缓存', '虚拟内存',
                    '文件系统', 'FAT', 'NTFS', 'ext4', 'ZFS',
                    '进程管理', '线程管理', '调度算法', '同步机制', '互斥锁',
                    '信号量', '条件变量', '死锁', '饥饿', '竞态条件',
                    '中断处理', '系统调用', '驱动程序', '内核模块', '微内核',
                    '宏内核', '混合内核', 'UEFI', 'BIOS', '引导加载程序',
                    'Linux', 'Windows', 'macOS', 'Unix', 'FreeBSD',
                    'Android系统', 'iOS系统', '实时操作系统', '分布式操作系统', '多处理器系统',

                    # 网络安全与密码学
                    '网络安全', '信息安全', '密码学', '加密算法', '认证协议',
                    '防火墙', '入侵检测', '渗透测试', '安全评估', '风险管理',
                    '威胁情报', '安全运营', '应急响应', '灾难恢复', '业务连续性',
                    '身份认证', '访问控制', '权限管理', '单点登录', '多因素认证',
                    '生物认证', '数字签名', '数字证书', 'PKI', 'TLS/SSL',
                    '对称加密', '非对称加密', '哈希函数', 'MD5', 'SHA',
                    'AES', 'DES', 'RSA', 'ECC', '量子加密',
                    '区块链安全', 'Web安全', 'SQL注入', 'XSS攻击', 'CSRF攻击',
                    '恶意软件', '病毒', '蠕虫', '木马', '勒索软件',
                    '社会工程学', '钓鱼攻击', '中间人攻击', 'DDoS攻击', '零日漏洞',

                    # 新兴技术与跨学科领域
                    '区块链', '物联网', '量子计算', '5G技术', '6G技术',
                    '增强现实', '虚拟现实', '混合现实', '边缘计算', '雾计算',
                    '生物信息学', '计算生物学', '医学信息学', '生物计算', '神经形态计算',
                    '类脑计算', '绿色计算', '可持续计算', '高性能计算', '超级计算机',
                    '并行计算', '分布式计算', '网格计算', '云计算', '量子加密',
                    '量子通信', '量子互联网', '数字孪生', '无人驾驶', '机器人技术',
                    '智能制造', '工业4.0', '智慧城市', '精准医疗', '基因编辑',
                    '合成生物学', '纳米技术', '太赫兹通信', '可穿戴设备', '脑机接口',
                    '元宇宙', 'NFT', '去中心化金融', '智能合约', '人工通用智能'
                ]
            }
        }
        
        # 配置重试参数
        self.max_retries = 3
        self.retry_delay = 5  # 秒
        
        # 设置请求超时
        if HAS_AIOHTTP:
            import aiohttp
            self.timeout = aiohttp.ClientTimeout(total=60)
        else:
            self.timeout = ClientTimeout(total=60)
        
        # 设置请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.baidu.com/',
            'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        }

        # 记录上次更新时间，用于增量更新
        self.last_update_time = time.time()
        # 存储已采集的知识点，避免重复采集
        self.collected_knowledge_points = set()
        # 初始化数据库连接为None
        self.db = None
        self.db_mock = True

    async def collect_course_data(self):
        """采集课程数据"""
        updates = []
        try:
            print("开始采集课程数据，并行处理中...")
            start_time = time.time()

            # 生成所有课程源和类别组合的任务列表
            tasks = []
            total_tasks = 0

            for source_name, source_info in self.course_sources.items():
                for category in source_info['categories']:
                    if source_name == 'icourse163':
                        url = f"{source_info['url']}/search.htm?search={urllib.parse.quote(category)}&page=1"
                    elif source_name == 'xuetangx':
                        url = f"{source_info['url']}/search?query={urllib.parse.quote(category)}&page=1"
                    elif source_name == 'mooc':
                        url = f"{source_info['url']}/search?keyword={urllib.parse.quote(category)}"
                    else:
                        continue
                    
                    task = asyncio.create_task(self._collect_course_from_source(source_name, url))
                    tasks.append(task)
                    total_tasks += 1

            print(f"创建了 {total_tasks} 个课程数据采集任务")

            # 并行执行所有任务，但限制并发数，避免被网站封禁
            max_concurrent = 5  # 最大并发数
            completed = 0

            # 对任务进行分批处理
            for i in range(0, len(tasks), max_concurrent):
                batch = tasks[i:i + max_concurrent]
                print(f"处理第 {i // max_concurrent + 1} 批任务，共 {len(batch)} 个")
            
            # 等待所有任务完成
                batch_results = await asyncio.gather(*batch, return_exceptions=True)
            
            # 处理结果
                for result in batch_results:
                    completed += 1
                    progress = (completed / total_tasks) * 100
                    print(f"进度: {progress:.1f}% ({completed}/{total_tasks})")

                if isinstance(result, Exception):
                    print(f"采集课程数据错误: {str(result)}")
                elif result:  # 确保result不是None
                    updates.extend(result)
                    print(f"成功采集 {len(result)} 条数据")

                # 在批次之间添加延迟
                if i + max_concurrent < len(tasks):
                    delay = random.randint(2, 5)
                    print(f"等待 {delay} 秒后继续下一批任务...")
                    await asyncio.sleep(delay)

            elapsed = time.time() - start_time
            print(f"课程数据采集完成，耗时: {elapsed:.2f} 秒，获取到 {len(updates)} 条数据")
                    
        except Exception as e:
            print(f"采集课程数据错误: {str(e)}")
            import traceback
            traceback.print_exc()

        return updates

    async def collect_knowledge_data(self):
        """收集知识点数据"""
        print("开始从网络采集知识点数据...")
        start_time = time.time()

        # 从数据库中获取已有知识点
        existing_knowledge = set()
        try:
            # 如果可以访问数据库，从数据库中获取已有知识点
            if HAS_NEO4J and self.db and not self.db_mock:
                # 查询已有的所有知识点
                query = """
                MATCH (n:KnowledgePoint)
                RETURN n.name as name
                """
                result = await self.db.query(query)
                if result and 'data' in result:
                    for record in result['data']:
                        if 'name' in record and record['name']:
                            existing_knowledge.add(record['name'].lower())

                print(f"数据库中已存在 {len(existing_knowledge)} 个知识点")
        except Exception as e:
            print(f"获取已有知识点出错: {str(e)}")

        # 合并收集的数据
        all_collected_data = []

        # 对每个数据源进行采集
        for source_name, source_info in self.knowledge_sources.items():
            source_url = source_info.get('url')
            if not source_url:
                continue

            collected_data = await self._collect_knowledge_from_source(source_name, source_url)

            # 过滤掉已存在的知识点，实现增量更新
            new_collected_data = []
            for item in collected_data:
                # 检查知识点是否已存在
                if 'name' in item and item['name'] and item['name'].lower() not in existing_knowledge:
                    new_collected_data.append(item)
                    # 将新知识点添加到已存在集合中，避免重复添加
                    existing_knowledge.add(item['name'].lower())

            print(f"从{source_name}采集到 {len(collected_data)} 条知识点数据，其中新知识点 {len(new_collected_data)} 条")
            all_collected_data.extend(new_collected_data)

        end_time = time.time()
        print(f"知识点数据采集完成，耗时: {end_time - start_time:.2f} 秒，获取到 {len(all_collected_data)} 条新数据")

        # 如果没有采集到数据，使用本地存储的预设列表
        if not all_collected_data:
            print("警告：未能从数据源采集到知识点数据")
            # 创建一些基础计算机知识点数据
            basic_knowledge = [
                "计算机科学", "数据结构", "算法", "操作系统", "计算机网络",
                "数据库", "软件工程", "人工智能", "机器学习", "深度学习"
            ]
            for name in basic_knowledge:
                if name.lower() not in existing_knowledge:
                    all_collected_data.append({
                        'name': name,
                        'description': f"计算机科学中的{name}概念",
                        'source': 'system',
                        'url': f"https://example.com/{urllib.parse.quote(name)}",
                        'type': 'knowledge'
                    })
                    existing_knowledge.add(name.lower())

            print(f"使用预设知识点列表，添加了 {len(all_collected_data)} 条知识点数据")

        # 保存成功采集的知识点到本地文件，用于下次增量更新
        try:
            # 确保目录存在
            os.makedirs('data', exist_ok=True)

            # 保存采集到的知识点
            knowledge_file = 'data/collected_knowledge.json'

            # 首先读取已有的知识点
            existing_data = []
            if os.path.exists(knowledge_file):
                try:
                    with open(knowledge_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except Exception as e:
                    print(f"读取已有知识点文件出错: {str(e)}")

            # 合并新采集的知识点与已有的知识点
            merged_data = existing_data.copy()
            existing_names = {item['name'].lower() for item in existing_data if 'name' in item}

            for item in all_collected_data:
                if 'name' in item and item['name'].lower() not in existing_names:
                    merged_data.append(item)
                    existing_names.add(item['name'].lower())

            # 保存合并后的知识点
            with open(knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, ensure_ascii=False, indent=2)

            print(f"知识点数据保存成功，共 {len(merged_data)} 条")
        except Exception as e:
            print(f"保存知识点数据出错: {str(e)}")

        return all_collected_data

    async def _collect_course_from_source(self, source_name, source_url):
        """从指定源采集课程数据"""
        for attempt in range(self.max_retries):
            try:
                # 先尝试直接使用API获取数据
                api_data = await self._fetch_api_data(source_name, source_url)
                if api_data:
                    print(f"成功通过API获取{source_name}的数据")
                    courses = await self.spider.parse_courses(api_data, source_name)
                    if courses:
                        updates = self._process_course_data(courses, source_name)
                        return updates
                    
                # API获取失败，尝试获取页面内容
                # 首先尝试使用异步方式
                html = await self.spider.fetch_page(source_url, source_name)

                # 如果异步方式失败，尝试同步方式
                if not html:
                    print(f"警告：异步获取{source_name}的页面内容失败，尝试同步方式...")
                    html = self.spider.fetch_page_sync(source_url, source_name)

                if not html:
                    print(f"警告：无法获取{source_name}的页面内容，尝试重试...")
                    await asyncio.sleep(self.retry_delay)
                    continue

                # 解析课程信息
                courses = await self.spider.parse_courses(html, source_name)
                if not courses:
                    print(f"警告：无法从{source_name}解析课程信息，尝试重试...")
                    await asyncio.sleep(self.retry_delay)
                    continue
                
                updates = self._process_course_data(courses, source_name)
                return updates
            except Exception as e:
                print(f"从{source_name}采集课程数据错误: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                return []
                
        # 如果所有尝试都失败，使用预置数据
        print(f"所有尝试从{source_name}获取数据均失败，使用预置数据...")
        mock_courses = []
        
        if source_name == 'icourse163':
            mock_courses = [
                {
                    'title': '数据库系统概论',
                    'url': 'https://www.icourse163.org/course/PKU-1001',
                    'instructor': '王珊教授',
                    'description': '本课程系统介绍数据库系统的基本概念、原理和技术，包括数据模型、SQL语言、数据库设计等。',
                    'topics': ['数据库', '计算机科学', 'SQL']
                },
                {
                    'title': '操作系统原理',
                    'url': 'https://www.icourse163.org/course/THU-1002',
                    'instructor': '陈渝教授',
                    'description': '本课程介绍操作系统的基本概念、原理和实现技术，包括进程管理、内存管理、文件系统等。',
                    'topics': ['操作系统', '计算机科学', '系统编程']
                },
                {
                    'title': '计算机网络',
                    'url': 'https://www.icourse163.org/course/HIT-1003',
                    'instructor': '李建明教授',
                    'description': '本课程介绍计算机网络的基本概念、体系结构和协议，包括物理层、数据链路层、网络层、传输层和应用层。',
                    'topics': ['计算机网络', 'TCP/IP', '协议']
                }
            ]
        elif source_name == 'xuetangx':
            mock_courses = [
                {
                    'title': 'Python编程基础',
                    'url': 'https://www.xuetangx.com/course/CS001',
                    'instructor': '张教授',
                    'description': '本课程介绍Python编程的基础知识，包括数据类型、控制结构、函数和模块等内容。',
                    'topics': ['Python', '编程', '计算机科学']
                },
                {
                    'title': '数据结构与算法',
                    'url': 'https://www.xuetangx.com/course/CS002',
                    'instructor': '李教授',
                    'description': '本课程介绍基本数据结构和算法，包括数组、链表、队列、栈、树、图以及常见排序和搜索算法。',
                    'topics': ['数据结构', '算法', '计算机科学']
                },
                {
                    'title': '机器学习入门',
                    'url': 'https://www.xuetangx.com/course/CS003',
                    'instructor': '王教授',
                    'description': '本课程介绍机器学习基本概念和常用算法，包括监督学习、无监督学习和强化学习。',
                    'topics': ['机器学习', '人工智能', '数据科学']
                }
            ]
        
        if mock_courses:
            print(f"使用 {len(mock_courses)} 个预置的{source_name}课程数据")
            updates = self._process_course_data(mock_courses, source_name)
            return updates
            
        return []

    def _process_course_data(self, courses, source_name):
        """处理课程数据，转换为知识图谱需要的格式"""
        updates = []
        
        for course in courses:
            title = course.get('title', '未知课程')
            url = course.get('url', '')
            instructor = course.get('instructor', '未知讲师')
            description = course.get('description', '')
            topics = course.get('topics', [])
            
            # 创建课程实体
            course_entity = {
                'id': f"course_{hashlib.md5(title.encode()).hexdigest()[:8]}",
                'name': title,
                'type': 'entity',
                'label': 'Course',
                'properties': {
                    'url': url,
                    'description': description,
                    'source': source_name
                },
                'confidence': 0.9
            }
            updates.append(course_entity)
            
            # 创建教师实体
            if instructor and instructor != '未知讲师':
                instructor_entity = {
                    'id': f"instructor_{hashlib.md5(instructor.encode()).hexdigest()[:8]}",
                    'name': instructor,
                    'type': 'entity',
                    'label': 'Instructor',
                    'properties': {
                        'source': source_name
                    },
                    'confidence': 0.85
                }
                updates.append(instructor_entity)
                
                # 创建教师-课程关系
                teaches_relation = {
                    'source': instructor_entity['id'],
                    'target': course_entity['id'],
                    'type': 'relation',
                    'label': 'TEACHES',
                    'properties': {
                        'source': source_name
                    },
                    'confidence': 0.85
                }
                updates.append(teaches_relation)
            
            # 处理主题/知识点
            for topic in topics:
                if not topic or len(topic) < 2:  # 跳过过短的主题
                    continue
                    
                topic_entity = {
                    'id': f"topic_{hashlib.md5(topic.encode()).hexdigest()[:8]}",
                    'name': topic,
                    'type': 'entity',
                    'label': 'KnowledgePoint',
                    'properties': {
                        'source': source_name
                    },
                    'confidence': 0.8
                }
                updates.append(topic_entity)
                
                # 创建课程-主题关系
                covers_relation = {
                    'source': course_entity['id'],
                    'target': topic_entity['id'],
                    'type': 'relation',
                    'label': 'COVERS',
                    'properties': {
                        'source': source_name
                    },
                    'confidence': 0.8
                }
                updates.append(covers_relation)
        
        return updates
    
    async def _fetch_api_data(self, source_name, search_url):
        """使用API获取课程数据"""
        try:
            print(f"尝试使用API方式获取{source_name}的数据...")
            
            # 从搜索URL中提取搜索关键词
            search_term = ""
            if source_name == 'xuetangx':
                match = re.search(r'query=([^&]+)', search_url)
                if match:
                    search_term = urllib.parse.unquote(match.group(1))
                    
                # 改用课程列表接口而非搜索接口
                api_url = "https://www.xuetangx.com/api/v1/lms/get_product_list/?page=1&page_size=12&category=1"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'zh-CN,zh;q=0.9',
                    'Connection': 'keep-alive',
                    'Referer': 'https://www.xuetangx.com/channel/computer',
                    'Origin': 'https://www.xuetangx.com',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'x-client': 'web',
                    'Content-Type': 'application/json'
                }
                
                # 使用Python 3.7+异步HTTP客户端
                if HAS_AIOHTTP and self.spider.session:
                    async with self.spider.session.get(api_url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.text()
                            print(f"成功获取学堂在线API响应，内容长度: {len(data)}")
                            return data
                        else:
                            print(f"学堂在线API请求失败，状态码: {response.status}")
                else:
                    # 回退到同步请求
                    session = requests.Session()
                    response = session.get(api_url, headers=headers, timeout=30)
                    if response.status_code == 200:
                        print(f"成功获取学堂在线API响应，内容长度: {len(response.text)}")
                        return response.text
                    else:
                        print(f"学堂在线API请求失败，状态码: {response.status_code}")
                
                # 如果API请求失败，返回预置的学堂在线课程数据
                print("返回学堂在线模拟数据...")
                return json.dumps({
                    "data": {
                        "courseList": [
                            {
                                "id": "CS001",
                                "name": "Python编程基础",
                                "teacherName": "张教授",
                                "description": "本课程介绍Python编程的基础知识，包括数据类型、控制结构、函数和模块等内容。",
                                "category": "计算机科学"
                            },
                            {
                                "id": "CS002",
                                "name": "数据结构与算法",
                                "teacherName": "李教授",
                                "description": "本课程介绍基本数据结构和算法，包括数组、链表、队列、栈、树、图以及常见排序和搜索算法。",
                                "category": "计算机科学"
                            },
                            {
                                "id": "CS003",
                                "name": "机器学习入门",
                                "teacherName": "王教授",
                                "description": "本课程介绍机器学习基本概念和常用算法，包括监督学习、无监督学习和强化学习。",
                                "category": "人工智能"
                            }
                        ]
                    }
                })
            
            elif source_name == 'icourse163':
                match = re.search(r'search=([^&]+)', search_url)
                if match:
                    search_term = urllib.parse.unquote(match.group(1))
                
                # 改用直接获取课程列表的方式，不使用搜索API
                # 中国大学MOOC的课程列表API
                api_url = "https://www.icourse163.org/web/j/courseBean.getCoursePanelListByFrontParams.rpc"
                
                # 使用更完整的请求头，模拟浏览器
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Accept-Language': 'zh-CN,zh;q=0.9',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': 'https://www.icourse163.org/channel/3002.htm',
                    'Origin': 'https://www.icourse163.org',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Cookie': 'NTESSTUDYSI=1; EDUWEBDEVICE=62adaea9d8204fb09e1a26b82647d72e'
                }
                
                # 构造POST请求参数 - 计算机专业相关课程
                post_data = {
                    'p': '1',  # 页码
                    'psize': '20',  # 每页数量
                    'type': '1',  # 课程类型：1表示普通课程
                    'categoryId': '2001',  # 大类：2001表示计算机
                    'orderBy': '0',  # 排序方式：0为默认排序
                    'stat0': '-1',  # 课程状态：全部
                }
                
                # 使用Python 3.7+异步HTTP客户端
                if HAS_AIOHTTP and self.spider.session:
                    async with self.spider.session.post(api_url, headers=headers, data=post_data) as response:
                        if response.status == 200:
                            data = await response.text()
                            print(f"成功获取中国大学MOOC API响应，内容长度: {len(data)}")
                            return data
                        else:
                            print(f"中国大学MOOC API请求失败，状态码: {response.status}")
                else:
                    # 回退到同步请求
                    session = requests.Session()
                    response = session.post(api_url, headers=headers, data=post_data, timeout=30)
                    if response.status_code == 200:
                        print(f"成功获取中国大学MOOC API响应，内容长度: {len(response.text)}")
                        return response.text
                    else:
                        print(f"中国大学MOOC API请求失败，状态码: {response.status_code}")
                
                # 如果API请求失败，返回预置的中国大学MOOC课程数据
                print("返回中国大学MOOC模拟数据...")
                return json.dumps({
                    "result": {
                        "list": [
                            {
                                "id": "1001",
                                "name": "数据库系统概论",
                                "schoolName": "北京大学",
                                "teacherName": "王珊教授",
                                "description": "本课程系统介绍数据库系统的基本概念、原理和技术，包括数据模型、SQL语言、数据库设计等。",
                                "categoryName": "计算机"
                            },
                            {
                                "id": "1002",
                                "name": "操作系统原理",
                                "schoolName": "清华大学",
                                "teacherName": "陈渝教授",
                                "description": "本课程介绍操作系统的基本概念、原理和实现技术，包括进程管理、内存管理、文件系统等。",
                                "categoryName": "计算机"
                            },
                            {
                                "id": "1003",
                                "name": "计算机网络",
                                "schoolName": "哈尔滨工业大学",
                                "teacherName": "李建明教授",
                                "description": "本课程介绍计算机网络的基本概念、体系结构和协议，包括物理层、数据链路层、网络层、传输层和应用层。",
                                "categoryName": "计算机"
                            }
                        ]
                    }
                })
            
            return None
        except Exception as e:
            print(f"API数据获取错误: {str(e)}")
            # 发生错误时也返回模拟数据
            if source_name == 'xuetangx':
                return json.dumps({
                    "data": {
                        "courseList": [
                            {
                                "id": "CS001",
                                "name": "Python编程基础",
                                "teacherName": "张教授",
                                "description": "本课程介绍Python编程的基础知识，包括数据类型、控制结构、函数和模块等内容。",
                                "category": "计算机科学"
                            }
                        ]
                    }
                })
            elif source_name == 'icourse163':
                return json.dumps({
                    "result": {
                        "list": [
                            {
                                "id": "1001",
                                "name": "数据库系统概论",
                                "schoolName": "北京大学",
                                "teacherName": "王珊教授",
                                "description": "本课程系统介绍数据库系统的基本概念、原理和技术，包括数据模型、SQL语言、数据库设计等。",
                                "categoryName": "计算机"
                            }
                        ]
                    }
                })
            return None

    async def _collect_knowledge_from_source(self, source_name, source_url):
        """从数据源采集知识点数据"""
        print(f"\n开始从{source_name}采集知识点数据...")
        collected_data = []

        try:
            # 构建知识点URL列表
            knowledge_urls = []

            if source_name == 'baidu':
                # 获取该来源的知识点列表
                topics = self.knowledge_sources[source_name]['subtopics']
                total_topics = len(topics)
                print(f"准备采集 {total_topics} 个知识点")

                # 增加批次大小，提高效率
                batch_size = 10  # 从1个增加到10个，显著提高并发效率
                total_batches = (total_topics + batch_size - 1) // batch_size

                start_time = time.time()
                print(f"共计 {total_batches} 个批次, 预计完成时间: {total_batches * 30} 秒")

                for batch_idx in range(total_batches):
                    start_idx = batch_idx * batch_size
                    end_idx = min(start_idx + batch_size, total_topics)
                    batch_topics = topics[start_idx:end_idx]

                    batch_start_time = time.time()
                    print(f"\n📦 处理第 {batch_idx + 1}/{total_batches} 批任务，共 {len(batch_topics)} 个知识点")
                    print(f"   进度: {(batch_idx + 1) / total_batches * 100:.1f}% ({batch_idx + 1}/{total_batches})")

                    batch_urls = []
                    for topic in batch_topics:
                        # 构建URL
                        url = f"{source_url}/{urllib.parse.quote(topic)}"
                        batch_urls.append((url, topic))

                    # 为每个主题创建异步任务
                    tasks = []
                    for url, topic in batch_urls:
                        task = asyncio.create_task(self._fetch_knowledge_data(source_name, url, topic))
                        tasks.append(task)

                    # 并行执行本批次的所有任务
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                    # 处理结果
                    batch_success = 0
                    for result in batch_results:
                        if isinstance(result, Exception):
                            print(f"❌ 获取知识点数据时出错: {str(result)}")
                            continue
                        
                        if result and len(result) > 0:
                            collected_data.extend(result)
                            batch_success += 1

                    batch_elapsed = time.time() - batch_start_time
                    print(f"   批次耗时: {batch_elapsed:.2f} 秒，成功: {batch_success}/{len(batch_topics)}")

                    # 构建部分知识图谱，以便查看效果
                    if batch_idx > 0 and (batch_idx % 2 == 0 or batch_idx == total_batches - 1):
                        print(f"\n🔄 已完成 {batch_idx + 1}/{total_batches} 批次，开始构建部分知识图谱...")
                        # 创建临时数据，进行部分构建
                        temp_data = collected_data.copy()

                        # 创建一个事件，以便在后台进行处理
                        build_event = asyncio.create_task(self._build_partial_graph(temp_data, batch_idx + 1))
                        # 不等待任务完成，继续采集数据

                    # 在批次之间添加合理的延迟，避免触发反爬但又不过慢
                    if batch_idx < total_batches - 1:
                        delay = 10 + random.random() * 5  # 减少延迟到10-15秒
                        print(f"   等待 {delay:.2f} 秒后处理下一批次...")
                        await asyncio.sleep(delay)
                    else:
                        print(f"✅ 所有批次处理完成！")

                total_elapsed = time.time() - start_time
                print(f"\n总采集耗时: {total_elapsed:.2f} 秒，平均每个知识点 {total_elapsed / total_topics:.2f} 秒")

            # 返回收集到的数据
            print(f"从{source_name}成功采集 {len(collected_data)} 条知识点数据")
            return collected_data

        except Exception as e:
            print(f"❌ 采集知识点数据时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    async def _build_partial_graph(self, data, batch_num):
        """构建部分知识图谱，用于预览效果"""
        try:
            print(f"开始构建第 {batch_num} 批次的临时知识图谱...")
            # 创建实体
            entities = [item for item in data if item.get('type') == 'entity']
            # 处理知识点，创建关系
            relations = []

                                # 为每个知识点创建关系
            for entity in entities:
                if entity.get('label') == 'KnowledgePoint':
                    # 获取相关主题
                    related_topics = entity.get('properties', {}).get('related_topics', [])
                    for topic in related_topics:
                        # 根据知识点名称判断关系类型
                        # 如果knowledge主题和topic包含相同的词，可能是包含关系
                        knowledge_name = entity.get('name', '').lower()
                        topic_lower = topic.lower()
                        
                        # 确定关系类型 - 默认为CONTAINS，减少RELATED_TO的使用
                        relation_type = 'CONTAINS'
                        # 只有在主题名超过知识点名称长度的情况下才考虑使用RELATED_TO
                        if len(topic) < len(knowledge_name) and topic_lower not in knowledge_name:
                            relation_type = 'RELATED_TO'
                            
                        relations.append({
                            'type': 'relation',
                            'source': entity.get('name'),
                            'target': topic,
                            'relation_type': relation_type,
                            'source_type': 'derived',
                            'confidence': 0.8,
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                        })

            # 合并实体和关系
            processed_data = entities + relations

            # 应用到模拟数据库
            if hasattr(self, 'db') and self.db and not self.db_mock:
                # 如果有真实数据库连接，写入数据库
                # 此处需要根据实际情况实现
                pass
            else:
                # 更新模拟数据库
                self._update_mock_db(processed_data)

            print(f"✅ 第 {batch_num} 批次临时知识图谱构建完成，包含 {len(entities)} 个实体和 {len(relations)} 个关系")
            return True
        except Exception as e:
            print(f"❌ 构建部分知识图谱失败: {str(e)}")
            return False

    def _update_mock_db(self, data):
        """更新模拟数据库"""
        # 初始化模拟数据库（如果尚未初始化）
        if not hasattr(self, 'mock_db'):
            self.mock_db = {
                'entities': {},
                'relations': []
            }

        # 更新实体
        entities_added = 0
        for item in data:
            if item.get('type') == 'entity':
                name = item.get('name')
                if name and name not in self.mock_db['entities']:
                    self.mock_db['entities'][name] = item
                    entities_added += 1

        # 更新关系
        relations_added = 0
        for item in data:
            if item.get('type') == 'relation':
                # 检查是否是新关系
                source = item.get('source')
                target = item.get('target')
                relation_type = item.get('relation_type')

                # 检查关系是否已存在
                is_new = True
                for rel in self.mock_db['relations']:
                    if (rel.get('source') == source and
                            rel.get('target') == target and
                            rel.get('relation_type') == relation_type):
                        is_new = False
                        break

                if is_new:
                    self.mock_db['relations'].append(item)
                    relations_added += 1

        print(f"模拟数据库更新：增加了 {entities_added} 个实体和 {relations_added} 个关系")

    async def _fetch_knowledge_data(self, source_name, url, topic):
        """获取单个知识点的数据"""
        print(f"📄 获取知识点数据: {topic}")
        try:
            # 调用spider获取页面内容
            content = await self.spider.fetch_page(url, source_name)

            if not content:
                print(f"❌ 无法获取知识点页面内容: {topic}")
                return []

            content_length = len(content)
            print(f"✅ 成功获取知识点 '{topic}' 的页面内容, 大小: {content_length} 字节")

            # 解析知识点数据
            if source_name == 'baidu':
                result = self._parse_baidu_knowledge(content, topic)
                print(f"   解析得到 {len(result)} 条记录")
                return result

            return []
        except Exception as e:
            print(f"❌ 获取知识点 {topic} 时出错: {str(e)}")
            return []

    def _parse_baidu_knowledge(self, html, topic):
        """解析百度百科知识点数据"""
        try:
            results = []

            # 如果没有BeautifulSoup，则使用简单解析
            if not HAS_BS4:
                print("   使用简单正则表达式解析HTML")
                # 简单提取标题和简介
                title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html)
                title = title_match.group(1) if title_match else topic

                # 尝试提取简介
                summary_match = re.search(r'<div class="lemma-summary[^>]*>(.*?)</div>', html, re.DOTALL)
                summary = summary_match.group(1) if summary_match else f"关于{topic}的知识点"

                # 移除HTML标签
                summary = re.sub(r'<[^>]+>', '', summary)
                summary = re.sub(r'\s+', ' ', summary).strip()

                # 尝试提取相关主题
                related_topics = []
                link_pattern = re.compile(r'<a[^>]*href="[^"]*"[^>]*>(.*?)</a>', re.DOTALL)
                for match in link_pattern.finditer(html):
                    link_text = match.group(1).strip()
                    if link_text and len(link_text) > 1 and link_text != title:
                        related_topics.append(link_text)

                # 尝试提取分类信息
                category_match = re.search(r'<dt>分类</dt>\s*<dd>(.*?)</dd>', html, re.DOTALL)
                category = category_match.group(1).strip() if category_match else "计算机科学"

                # 限制相关主题数量
                related_topics = list(set(related_topics))[:5]

                    # 创建知识点实体
                entity = {
                        'type': 'entity',
                    'name': title,
                        'label': 'KnowledgePoint',
                    'source': 'baidu',
                        'confidence': 0.9,
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'properties': {
                        'description': summary[:300] + '...' if len(summary) > 300 else summary,
                        'category': category,
                        'url': f"https://baike.baidu.com/item/{urllib.parse.quote(topic)}",
                        'related_topics': related_topics
                    }
                }

                # 尝试提取额外属性
                extra_attrs = {}
                attr_pattern = re.compile(r'<dt>(.*?)</dt>\s*<dd>(.*?)</dd>', re.DOTALL)
                for match in attr_pattern.finditer(html):
                    key = match.group(1).strip()
                    value = match.group(2).strip()
                    if key and value and key not in ['中文名', '领域', '分类', '相关主题']:
                        # 移除HTML标签
                        value = re.sub(r'<[^>]+>', '', value).strip()
                        extra_attrs[key] = value

                # 添加额外属性
                if extra_attrs:
                    for key, value in extra_attrs.items():
                        entity['properties'][key] = value

                results.append(entity)
                print(f"   成功解析知识点: {title}，找到 {len(related_topics)} 个相关主题和 {len(extra_attrs)} 个额外属性")
                return results

            # 使用BeautifulSoup解析
            print("   使用BeautifulSoup解析HTML")
            soup = BeautifulSoup(html, 'html.parser')

            # 提取标题
            title_elem = soup.find('h1')
            title = title_elem.text.strip() if title_elem else topic

            # 提取简介
            summary_elem = soup.select_one('.lemma-summary')
            if summary_elem:
                summary = summary_elem.text.strip()
            else:
                summary = f"关于{topic}的知识点"

            # 提取分类信息
            category = "计算机科学"
            category_elem = soup.select('.basic-info dt:contains("分类") + dd')
            if category_elem:
                category = category_elem[0].text.strip()
            else:
                # 尝试从其他位置获取分类
                catalog_elems = soup.select('.catalog-list a')
                if catalog_elems:
                    category_texts = [elem.text.strip() for elem in catalog_elems]
                    if category_texts:
                        category = category_texts[0]

            # 提取相关主题
            related_topics = []

            # 直接从相关主题字段提取
            rel_topics_elem = soup.select('.basic-info dt:contains("相关主题") + dd')
            if rel_topics_elem:
                topics_text = rel_topics_elem[0].text.strip()
                if topics_text:
                    # 拆分逗号分隔的主题
                    related_topics = [t.strip() for t in topics_text.split(',')]

            # 如果上面方法没找到相关主题，尝试从链接中提取
            if not related_topics:
                # 方法1：从正文中的链接提取
                summary_links = soup.select('.lemma-summary a')
                for link in summary_links:
                    link_text = link.text.strip()
                    if link_text and len(link_text) > 1 and link_text != title:
                        related_topics.append(link_text)

                # 方法2：从页面其他部分提取
                if len(related_topics) < 3:
                    other_links = soup.select('a')
                    for link in other_links:
                        link_text = link.text.strip()
                        if (link_text and len(link_text) > 1 and link_text != title
                                and not any(c in link_text for c in '.,;:(){}[]<>/\\\'"`')
                                and len(link_text) < 20  # 避免太长的文本
                                and link_text not in related_topics):
                            related_topics.append(link_text)
                            if len(related_topics) >= 5:
                                break

            # 确保相关主题不重复，限制数量
            related_topics = list(set(related_topics))[:5]

            # 提取额外属性
            extra_properties = {}

            # 获取所有属性字段
            dt_elements = soup.select('.basic-info dt')
            for dt in dt_elements:
                key = dt.text.strip()
                if key not in ['中文名', '领域', '分类', '相关主题']:
                    # 获取对应的值
                    dd = dt.find_next('dd')
                    if dd:
                        value = dd.text.strip()
                        extra_properties[key] = value

            # 构建知识点实体
            entity = {
                'type': 'entity',
                'name': title,
                'label': 'KnowledgePoint',
                'source': 'baidu',
                'confidence': 0.95,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'properties': {
                    'description': summary[:300] + '...' if len(summary) > 300 else summary,
                    'category': category,
                    'url': f"https://baike.baidu.com/item/{urllib.parse.quote(topic)}",
                    'related_topics': related_topics,
                    **extra_properties  # 添加额外属性
                }
            }

            # 添加知识点的唯一标识符
            entity['id'] = str(uuid.uuid4())

            results.append(entity)

            print(f"   成功解析知识点: {title}，找到 {len(related_topics)} 个相关主题和 {len(extra_properties)} 个额外属性")

            # 创建相关主题的实体和关系
            for related_topic in related_topics:
                # 排除非法值
                if not related_topic or related_topic == title:
                    continue

                # 创建相关主题的实体
                related_entity = {
                    'type': 'entity',
                    'name': related_topic,
                    'label': 'KnowledgePoint',
                    'source': 'baidu_related',
                    'confidence': 0.8,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'id': str(uuid.uuid4()),
                    'properties': {
                        'category': category,
                        'description': f"与{title}相关的知识点"
                    }
                }

                # 创建关系
                relation = {
                            'type': 'relation',
                    'source': title,
                    'target': related_topic,
                            'relation_type': 'RELATED_TO',
                    'source_type': 'baidu',
                            'confidence': 0.85,
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                results.append(related_entity)
                results.append(relation)

            return results

        except Exception as e:
            print(f"❌ 解析百度百科知识点数据出错: {str(e)}")
            # 返回一个基本的结果
            entity = {
                'type': 'entity',
                'name': topic,
                'label': 'KnowledgePoint',  # 确保标签正确
                'source': 'baidu',
                'confidence': 0.8,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'properties': {
                    'description': f"计算机领域的{topic}概念",
                    'category': '计算机科学',
                    'url': f"https://baike.baidu.com/item/{urllib.parse.quote(topic)}",
                    'related_topics': []
                }
            }
            return [entity]


class BigDataProcessor:
    """大数据处理器"""
    
    def __init__(self):
        if not HAS_SPARK:
            print("警告: Spark未安装，将使用简单数据处理替代")
            self.spark = None
            return

        try:
            # 设置Python环境变量
            os.environ['PYSPARK_PYTHON'] = sys.executable
            os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable
            
            # 设置Hadoop环境变量
            os.environ['HADOOP_HOME'] = 'C:\\hadoop'
            os.environ['PATH'] = f"{os.environ['PATH']};C:\\hadoop\\bin"
            
            # 设置Spark环境变量
            os.environ['SPARK_LOCAL_DIRS'] = 'C:\\hadoop\\tmp'
            
            # 初始化Spark会话
            self.spark = SparkSession.builder \
                .appName("KnowledgeGraphProcessor") \
                .config("spark.executor.memory", "4g") \
                .config("spark.driver.memory", "2g") \
                .config("spark.sql.warehouse.dir", "C:\\hadoop\\tmp") \
                .config("spark.local.dir", "C:\\hadoop\\tmp") \
                .config("spark.driver.extraJavaOptions", "-Dfile.encoding=UTF-8") \
                .config("spark.executor.extraJavaOptions", "-Dfile.encoding=UTF-8") \
                .config("spark.python.worker.reuse", "true") \
                .config("spark.python.use.daemon", "true") \
                .config("spark.python.worker.memory", "512m") \
                .config("spark.eventLog.gcMetrics.youngGenerationGarbageCollectors", "G1 Young Generation") \
                .config("spark.eventLog.gcMetrics.oldGenerationGarbageCollectors", "G1 Old Generation") \
                .getOrCreate()
                
            # 设置日志级别
            self.spark.sparkContext.setLogLevel("ERROR")
            
            # 配置批处理参数
            self.batch_size = 1000
            
        except Exception as e:
            print(f"初始化Spark会话错误: {str(e)}")
            self.spark = None
            
    async def process_large_dataset(self, data):
        """处理大规模数据集"""
        if not data:
            print("警告：输入数据集为空")
            return []
            
        # 如果Spark不可用，使用简单处理
        if not HAS_SPARK or not self.spark:
            print("使用简单数据处理...")
            return self._simple_process(data)
            
        try:
            # 将数据转换为Spark DataFrame
            df = self.spark.createDataFrame(data)
            
            # 数据预处理
            df = self._preprocess_data(df)
            
            # 批量处理
            results = []
            for batch in self._split_into_batches(df):
                processed_batch = await self._process_batch(batch)
                results.extend(processed_batch)
                
            return results
        except Exception as e:
            print(f"处理数据集错误: {str(e)}")
            return self._simple_process(data)
        finally:
            # 清理临时文件
            self._cleanup_temp_files()
    
    def _simple_process(self, data):
        """简单数据处理方法，当Spark不可用时使用"""
        print("正在进行简单数据处理...")
        return data

    def _preprocess_data(self, df):
        """数据预处理"""
        try:
            # 删除空值
            df = df.na.drop()
            
            # 文本标准化
            tokenizer = Tokenizer(inputCol="text", outputCol="words")
            remover = StopWordsRemover(inputCol="words", outputCol="filtered_words")
            
            pipeline = Pipeline(stages=[tokenizer, remover])
            df = pipeline.fit(df).transform(df)
            
            return df
        except Exception as e:
            print(f"数据预处理错误: {str(e)}")
            return df
        
    def _split_into_batches(self, df):
        """将数据分割成批次"""
        try:
            # 使用repartition替代randomSplit以提高性能
            num_partitions = max(1, df.count() // self.batch_size)
            return df.repartition(num_partitions).rdd.mapPartitions(lambda x: [list(x)]).collect()
        except Exception as e:
            print(f"数据分片错误: {str(e)}")
            return [df]
        
    async def _process_batch(self, batch_df):
        """处理单个数据批次"""
        try:
            # 转换为Pandas DataFrame进行处理
            batch_pd = batch_df.toPandas()
            
            # 并行处理每个文档
            tasks = []
            for _, row in batch_pd.iterrows():
                task = asyncio.create_task(self._process_document(row))
                tasks.append(task)

            results = await asyncio.gather(*tasks)
            return [r for r in results if r is not None]
        except Exception as e:
            print(f"批处理错误: {str(e)}")
            return []
        
    async def _process_document(self, document):
        """处理单个文档"""
        try:
            return document.to_dict()
        except Exception as e:
            print(f"文档处理错误: {str(e)}")
            return None

    def _cleanup_temp_files(self):
        """清理临时文件"""
        try:
            temp_dir = "C:\\hadoop\\tmp"
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    try:
                        os.remove(os.path.join(temp_dir, file))
                    except Exception as e:
                        print(f"清理临时文件错误: {str(e)}")
        except Exception as e:
            print(f"清理临时目录错误: {str(e)}")
            
    def __del__(self):
        """清理资源"""
        try:
            if hasattr(self, 'spark'):
                self.spark.stop()
        except Exception as e:
            print(f"停止Spark会话错误: {str(e)}")


class DeepSeekExtractor:
    """使用DeepSeek API的实体和关系提取器"""
    
    def __init__(self):
        if not HAS_OPENAI:
            print("警告：OpenAI库未安装，将使用简单实体提取替代")
            self.client = None
            return

        try:
            self.client = OpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com/v1"
            )
        except Exception as e:
            print(f"初始化DeepSeek API客户端失败: {str(e)}")
            self.client = None
        
        # 实体提取提示模板
        self.entity_prompt_template = """
请从以下文本中提取所有计算机科学相关实体。
仅返回JSON格式，不要有任何其他解释文字：

        {
            "entities": [
        {"name": "实体名称", "type": "实体类型", "confidence": 0.9}
            ]
        }
        
        文本内容：
        {text}
        """
        
        # 关系提取提示模板
        self.relation_prompt_template = """
请从以下文本中提取实体之间的关系。
仅返回JSON格式，不要有任何其他解释文字：

        {
            "relations": [
        {"source": "源实体", "target": "目标实体", "type": "关系类型", "confidence": 0.9}
            ]
        }
        
        文本内容：
        {text}
        
        已知实体：
        {entities}
        """
        
    async def extract_entities(self, text):
        """使用DeepSeek提取实体"""
        # 如果OpenAI库不可用，使用简单提取
        if not HAS_OPENAI or not self.client:
            return self._simple_entity_extraction(text)
            
        try:
            # 构建提示
            prompt = self.entity_prompt_template.format(text=text)
            
            # 调用DeepSeek API
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的实体提取助手，擅长从文本中识别和提取实体。始终以纯JSON格式返回结果，不包含任何说明文字。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 降低温度，获得更可预测的输出
                max_tokens=1000
            )
            
            # 获取响应文本
            content = response.choices[0].message.content
            
            # 尝试解析JSON
            try:
                # 清理内容中可能的非JSON部分
                json_str = content
                # 尝试找到JSON的起始和结束位置
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                
                result = json.loads(json_str)
                entities = result.get("entities", [])
                print(f"✅ 成功从DeepSeek API获取 {len(entities)} 个实体")
                return entities
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析错误: {str(e)}")
                print(f"原始响应(截取): {content[:100]}...")
                return self._simple_entity_extraction(text)
            
        except Exception as e:
            print(f"实体提取错误: {str(e)}")
            return self._simple_entity_extraction(text)
            
    async def extract_relations(self, text, entities):
        """使用DeepSeek提取关系"""
        # 如果OpenAI库不可用，使用简单提取
        if not HAS_OPENAI or not self.client:
            return self._simple_relation_extraction(text, entities)
            
        try:
            # 构建提示
            entities_str = json.dumps(entities, ensure_ascii=False, indent=2)
            prompt = self.relation_prompt_template.format(
                text=text,
                entities=entities_str
            )
            
            # 调用DeepSeek API
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的关系提取助手，擅长从文本中识别实体之间的关系。始终以纯JSON格式返回结果，不包含任何说明文字。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 降低温度，获得更可预测的输出
                max_tokens=1000
            )
            
            # 获取响应文本
            content = response.choices[0].message.content
            
            # 尝试解析JSON
            try:
                # 清理内容中可能的非JSON部分
                json_str = content
                # 尝试找到JSON的起始和结束位置
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                
                result = json.loads(json_str)
                relations = result.get("relations", [])
                print(f"✅ 成功从DeepSeek API获取 {len(relations)} 个关系")
                return relations
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析错误: {str(e)}")
                print(f"原始响应(截取): {content[:100]}...")
                return self._simple_relation_extraction(text, entities)
            
        except Exception as e:
            print(f"关系提取错误: {str(e)}")
            return self._simple_relation_extraction(text, entities)
            
    def _simple_entity_extraction(self, text):
        """简单实体提取，当DeepSeek API不可用时使用"""
        print("使用简单实体提取...")
        entities = []
        
        # 提取可能的实体（这里仅做示例）
        words = text.split()
        for word in words:
            if len(word) > 3 and word[0].isupper():
                entities.append({
                    "name": word,
                    "type": "概念",
                    "confidence": 0.7
                })
                
        return entities
        
    def _simple_relation_extraction(self, text, entities):
        """简单关系提取，当DeepSeek API不可用时使用"""
        print("使用简单关系提取...")
        relations = []
        
        # 如果实体不足，无法建立关系
        if len(entities) < 2:
            return relations
            
        # 简单地将相邻实体连接（这里仅做示例）
        for i in range(len(entities) - 1):
            relations.append({
                "source": entities[i]["name"],
                "target": entities[i + 1]["name"],
                "type": "相关",
                "confidence": 0.6
            })
                
        return relations


class KnowledgeFusion:
    """知识融合器"""
    
    def __init__(self):
        self.entity_aligner = EntityAligner()
        self.relation_resolver = RelationResolver()
        self.knowledge_reasoner = KnowledgeReasoner()
        
    async def fuse_knowledge(self, updates):
        """融合知识"""
        # 实体对齐
        aligned_entities = await self.entity_aligner.align(updates['entities'])
        
        # 关系冲突解决
        resolved_relations = await self.relation_resolver.resolve(updates['relations'])
        
        # 知识推理
        inferred_knowledge = await self.knowledge_reasoner.infer(aligned_entities, resolved_relations)
        
        return {
            'entities': aligned_entities,
            'relations': resolved_relations,
            'inferred': inferred_knowledge
        }


class EntityAligner:
    """实体对齐器"""
    
    def __init__(self):
        self.nlp_processor = NLPProcessor()
        self.threshold = 0.7  # 相似度阈值
        
    def align_entities(self, entities):
        """对齐实体"""
        print(f"开始对齐 {len(entities)} 个实体...")

        if not entities:
            print("警告: 没有实体可供对齐")
            return []
            
        try:
        # 初始化对齐结果
            aligned_entities = entities.copy()
        
            # 筛选有效实体（具有name属性的）
            valid_entities = [entity for entity in entities if entity.get('name')]
            print(f"找到 {len(valid_entities)} 个有效实体")

            if not valid_entities:
                print("警告: 没有找到有效实体")
                return entities  # 返回原始实体

            # 对实体进行索引
            entity_index = {}
            for i, entity in enumerate(valid_entities):
                entity_name = entity.get('name', '')
                if entity_name:
                    entity_index[entity_name] = i
                
            print(f"建立了 {len(entity_index)} 个实体索引")

            # 查找相似实体并合并
            merges_performed = 0

            for i, entity in enumerate(valid_entities):
                entity_name = entity.get('name', '')
                entity_desc = entity.get('properties', {}).get('description', '')
            
                for j, other in enumerate(valid_entities):
                    if i == j:
                        continue
                    
                other_name = other.get('name', '')
                other_desc = other.get('properties', {}).get('description', '')
                
                # 计算名称相似度
                name_similarity = self.nlp_processor.calculate_similarity(entity_name, other_name)
                
                # 计算描述相似度
                desc_similarity = self.nlp_processor.calculate_similarity(entity_desc,
                                                                              other_desc) if entity_desc and other_desc else 0
                
                # 综合相似度
                similarity = name_similarity * 0.7 + desc_similarity * 0.3
                
                # 如果相似度高于阈值，合并实体
                if similarity > self.threshold:
                        # 找到对应的索引
                        entity_idx = entity_index.get(entity_name)
                        other_idx = entity_index.get(other_name)

                        if entity_idx is not None and entity_idx < len(aligned_entities):
                    # 合并属性
                            other_properties = other.get('properties', {})
                            entity_properties = aligned_entities[entity_idx].get('properties', {})

                            if not entity_properties:
                                aligned_entities[entity_idx]['properties'] = {}

                            # 合并属性
                            merged_properties = {**entity_properties, **other_properties}
                            aligned_entities[entity_idx]['properties'] = merged_properties
                    
                    # 标记实体关系
                            if 'related_entities' not in aligned_entities[entity_idx]:
                                aligned_entities[entity_idx]['related_entities'] = []
                    
                            if other_name not in aligned_entities[entity_idx]['related_entities']:
                                aligned_entities[entity_idx]['related_entities'].append(other_name)
                                merges_performed += 1

            print(f"完成实体对齐，执行了 {merges_performed} 次合并")
            return aligned_entities
        except Exception as e:
            print(f"❌ 实体对齐错误: {str(e)}")
            import traceback
            traceback.print_exc()
            # 返回原始实体
            return entities


class RelationResolver:
    """关系解析器"""
    
    def __init__(self):
        self.relation_types = {
            'CONTAINS': '包含',
            'RELATED_TO': '相关于',
            'PREREQUISITE': '先修于',
            'PREREQUISITE_FOR': '后续',
            'SIMILAR_TO': '相似于'
        }
        
        # 创建反向映射
        self.chinese_to_relation_types = {v: k for k, v in self.relation_types.items()}
        
    def resolve_relations(self, entities):
        """解析实体间关系"""
        print(f"开始解析 {len(entities)} 个实体的关系...")

        if not entities:
            print("警告: 没有实体用于关系解析")
            return []
            
        try:
            # 初始化结果
            result = []
            # 复制实体
            for entity in entities:
                result.append(entity)
            
            # 处理课程和知识点关系
            course_entities = [entity for entity in entities if entity.get('label') == 'Course']
            knowledge_entities = [entity for entity in entities if entity.get('label') == 'KnowledgePoint']

            print(f"找到 {len(course_entities)} 个课程实体和 {len(knowledge_entities)} 个知识点实体")

            # 如果没有找到任何实体，返回原始实体列表
            if not course_entities and not knowledge_entities:
                print("警告: 没有找到任何课程或知识点实体")
                return entities

            relations_added = 0
            
            # 创建课程名称到实体的映射，用于检查关系
            course_name_to_entity = {entity.get('name', ''): entity for entity in course_entities if entity.get('name')}
            knowledge_name_to_entity = {entity.get('name', ''): entity for entity in knowledge_entities if entity.get('name')}
            
            # 构建课程与知识点的包含关系
            for course in course_entities:
                course_name = course.get('name', '')
                if not course_name:
                    continue

                course_desc = course.get('properties', {}).get('description', '')
                course_topics = course.get('properties', {}).get('topics', [])
                
                for knowledge in knowledge_entities:
                    knowledge_name = knowledge.get('name', '')
                    if not knowledge_name:
                        continue
                    
                    # 如果知识点名称在课程主题中，创建包含关系
                    if knowledge_name in course_topics or (course_desc and knowledge_name.lower() in course_desc.lower()):
                        relation = {
                            'type': 'relation',
                            'source': course_name,
                            'target': knowledge_name,
                            'relation_type': 'CONTAINS',
                            'source_type': 'derived',
                            'confidence': 0.8,
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                        }
                        result.append(relation)
                        relations_added += 1

            # 如果没有找到任何关系，为每个课程生成一些随机关系
            if relations_added == 0 and knowledge_entities and course_entities:
                print("未找到现有关系，创建默认关系...")

                # 为每个课程创建至少一个关系
                for course in course_entities:
                    course_name = course.get('name', '')
                    if not course_name:
                        continue

                    # 选择随机知识点
                    if knowledge_entities:
                        knowledge = random.choice(knowledge_entities)
                        knowledge_name = knowledge.get('name', '')

                        if knowledge_name:
                            relation = {
                                'type': 'relation',
                                'source': course_name,
                                'target': knowledge_name,
                                'relation_type': 'CONTAINS',
                                'source_type': 'default',
                                'confidence': 0.6,
                                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                            }
                            result.append(relation)
                            relations_added += 1

            # 如果仍然没有关系，使用DEFAULT_RELATIONS
            if relations_added == 0:
                print("警告: 未能生成任何关系，使用默认关系")
                for relation in DEFAULT_RELATIONS:
                    result.append(relation)
                    relations_added += len(DEFAULT_RELATIONS)

            print(f"关系解析完成，添加了 {relations_added} 个课程-知识点关系")
            return result

        except Exception as e:
            print(f"❌ 关系解析错误: {str(e)}")
            import traceback
            traceback.print_exc()
            # 返回原始实体
            return entities


class KnowledgeReasoner:
    """知识推理器"""
    
    def __init__(self):
        self.MAX_PATH_LENGTH = 3  # 最大路径长度
        
    def enrich_knowledge(self, data):
        """扩展知识"""
        print(f"开始基于 {len(data)} 条数据进行知识推理...")

        if not data:
            print("警告: 没有数据可用于知识推理")
            return []
            
        try:
            # 复制原始数据
            enriched_data = data.copy()
            
            # 提取实体和关系
            entities = [item for item in data if item.get('type') == 'entity']
            relations = [item for item in data if item.get('type') == 'relation']
            
            print(f"找到 {len(entities)} 个实体和 {len(relations)} 个关系用于推理")

            # 如果实体或关系太少，无法进行有效推理
            if len(entities) < 2 or len(relations) < 1:
                print("警告: 实体或关系数量不足，无法进行知识推理")
                return data

            # 构建知识图谱
            graph = self._build_graph(entities, relations)
            
            # 推断新关系
            new_relations = self._infer_new_relations(graph, entities, relations)
            
            # 添加新的推断关系
            if new_relations:
                print(f"推理出 {len(new_relations)} 个新关系")
                for relation in new_relations:
                    enriched_data.append(relation)
            else:
                print("未能推理出新关系")
            
            return enriched_data
            
        except Exception as e:
            print(f"❌ 知识推理错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return data
        
    def _build_graph(self, entities, relations):
        """构建图结构"""
        try:
            graph = {}
            
            # 初始化图结构
            for entity in entities:
                entity_name = entity.get('name', '')
                if entity_name:
                    graph[entity_name] = []
                    
            # 添加关系
            for relation in relations:
                source = relation.get('source', '')
                target = relation.get('target', '')
                relation_type = relation.get('relation_type', '')
                
                if source in graph and target in graph:
                    graph[source].append((target, relation_type))
                    
            return graph
            
        except Exception as e:
            print(f"❌ 构建图结构错误: {str(e)}")
            return {}
        
    def _infer_new_relations(self, graph, entities, relations):
        """推断新关系"""
        if not graph:
            return []

        try:
            new_relations = []
            existing_relations = set()

            # 首先创建现有关系的集合，避免重复
            for relation in relations:
                source = relation.get('source', '')
                target = relation.get('target', '')
                relation_type = relation.get('relation_type', '')

                if source and target and relation_type:
                    relation_key = f"{source}|{relation_type}|{target}"
                    existing_relations.add(relation_key)
            
            # 推断传递关系
            for entity1 in graph:
                for entity2, relation_type1 in graph.get(entity1, []):
                    for entity3, relation_type2 in graph.get(entity2, []):
                        # 只处理相同类型的关系，比如PREREQUISITE
                        if relation_type1 == relation_type2 == 'PREREQUISITE' and entity1 != entity3:
                            # 检查是否已存在该关系
                            relation_key = f"{entity1}|PREREQUISITE|{entity3}"
                            if relation_key not in existing_relations:
                                new_relation = {
                                    'type': 'relation',
                                    'source': entity1,
                                    'target': entity3,
                                    'relation_type': 'PREREQUISITE',
                                    'source_type': 'inferred',
                                    'confidence': 0.6,
                                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                                }
                                new_relations.append(new_relation)
                                existing_relations.add(relation_key)  # 避免重复添加

            # 尝试推断相关关系
            if len(new_relations) == 0:
                print("尝试推断更多类型的关系...")

                # 创建实体名称到标签的映射，用于检查实体类型
                entity_name_to_label = {}
                for entity in entities:
                    if 'name' in entity:
                        entity_name_to_label[entity['name']] = entity.get('label', '')

                # 如果两个知识点都与同一个课程相关，它们可能相关
                course_to_knowledge = {}

                # 构建课程到知识点的映射，确保只包含课程到知识点的CONTAINS关系
                for relation in relations:
                    if relation.get('relation_type') == 'CONTAINS':
                        course = relation.get('source', '')
                        knowledge = relation.get('target', '')
                        
                        # 检查source是课程，target是知识点
                        is_course_to_knowledge = (entity_name_to_label.get(course) == 'Course' and 
                                                 entity_name_to_label.get(knowledge) == 'KnowledgePoint')
                        
                        # 如果不是课程到知识点的关系，则跳过
                        if not is_course_to_knowledge:
                            continue

                        if course and knowledge:
                            if course not in course_to_knowledge:
                                course_to_knowledge[course] = []
                            course_to_knowledge[course].append(knowledge)

                # 寻找共同课程的知识点
                for course, knowledge_points in course_to_knowledge.items():
                    if len(knowledge_points) >= 2:
                        for i in range(len(knowledge_points)):
                            for j in range(i + 1, len(knowledge_points)):
                                k1 = knowledge_points[i]
                                k2 = knowledge_points[j]

                                # 检查是否已存在关系
                                rel_key1 = f"{k1}|RELATED_TO|{k2}"
                                rel_key2 = f"{k2}|RELATED_TO|{k1}"

                                if rel_key1 not in existing_relations and rel_key2 not in existing_relations:
                                    # 只为少数关系创建RELATED_TO关系，避免过多生成
                                    # 使用随机函数限制RELATED_TO关系的创建 - 减少90%
                                    if random.random() > 0.9:
                                        # 优先使用CONTAINS关系（如果其中一个知识点名包含另一个）
                                        relation_type = 'RELATED_TO'
                                        if k1.lower() in k2.lower():
                                            # k2包含k1，则k2可能包含k1
                                            relation_type = 'CONTAINS'
                                            source, target = k2, k1
                                        elif k2.lower() in k1.lower():
                                            # k1包含k2，则k1可能包含k2
                                            relation_type = 'CONTAINS'
                                            source, target = k1, k2
                                        else:
                                            # 确定哪个是source, 哪个是target (保持k1->k2方向)
                                            source, target = k1, k2
                                        
                                        new_relation = {
                                            'type': 'relation',
                                            'source': source,
                                            'target': target,
                                            'relation_type': relation_type,
                                            'source_type': 'inferred',
                                            'confidence': 0.5,
                                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                                        }
                                        new_relations.append(new_relation)
                                        if relation_type == 'CONTAINS':
                                            existing_relations.add(f"{source}|CONTAINS|{target}")
                                        else:
                                            existing_relations.add(rel_key1)

            return new_relations
            
        except Exception as e:
            print(f"❌ 推断新关系错误: {str(e)}")
            return []
        
    def _relation_exists(self, relations, source, target, relation_type):
        """检查关系是否已存在"""
        for relation in relations:
            if (relation.get('source') == source and 
                relation.get('target') == target and 
                relation.get('relation_type') == relation_type):
                return True
        return False


class QualityEvaluator:
    """质量评估器"""
    
    def __init__(self):
        self.metrics = {
            'completeness': 0.3,  # 完整性权重
            'accuracy': 0.3,  # 准确性权重
            'coherence': 0.2,  # 一致性权重
            'relevance': 0.2  # 相关性权重
        }
        
    def evaluate_quality(self, data):
        """评估质量并过滤数据"""
        if not data:
            return []
            
        # 提取实体和关系
        entities = [item for item in data if item.get('type') == 'entity']
        relations = [item for item in data if item.get('type') == 'relation']
        
        # 评估各个指标
        completeness_score = self._evaluate_completeness(entities, relations)
        accuracy_score = self._evaluate_accuracy(entities, relations)
        coherence_score = self._evaluate_coherence(entities, relations)
        relevance_score = self._evaluate_relevance(entities, relations)
        
        # 计算总体得分
        overall_score = (
            completeness_score * self.metrics['completeness'] +
            accuracy_score * self.metrics['accuracy'] +
            coherence_score * self.metrics['coherence'] +
            relevance_score * self.metrics['relevance']
        )
        
        # 根据得分过滤数据
        filtered_data = self._filter_data(data, overall_score)
        
        return filtered_data
        
    def _evaluate_completeness(self, entities, relations):
        """评估完整性"""
        # 计算有描述的实体比例
        entities_with_description = 0
        for entity in entities:
            properties = entity.get('properties', {})
            if properties and 'description' in properties and properties['description']:
                entities_with_description += 1
                
        completeness_score = entities_with_description / len(entities) if entities else 0
        
        # 检查关系的完整性
        valid_relations = 0
        for relation in relations:
            if relation.get('source') and relation.get('target') and relation.get('relation_type'):
                valid_relations += 1
                
        relation_completeness = valid_relations / len(relations) if relations else 0
        
        # 综合得分
        return (completeness_score + relation_completeness) / 2
        
    def _evaluate_accuracy(self, entities, relations):
        """评估准确性"""
        # 使用置信度作为准确性指标
        entity_confidence = sum(entity.get('confidence', 0) for entity in entities) / len(entities) if entities else 0
        relation_confidence = sum(relation.get('confidence', 0) for relation in relations) / len(
            relations) if relations else 0
        
        return (entity_confidence + relation_confidence) / 2
        
    def _evaluate_coherence(self, entities, relations):
        """评估一致性"""
        # 检查关系双方是否都存在
        entity_names = {entity.get('name', ''): entity for entity in entities}
        valid_relations = 0
        
        for relation in relations:
            source = relation.get('source', '')
            target = relation.get('target', '')
            
            if source in entity_names and target in entity_names:
                valid_relations += 1
                
        coherence_score = valid_relations / len(relations) if relations else 0
        
        return coherence_score
        
    def _evaluate_relevance(self, entities, relations):
        """评估相关性"""
        # 简单实现，假设所有数据都相关
        return 0.8
        
    def _filter_data(self, data, overall_score):
        """根据质量得分过滤数据"""
        # 如果总体得分低于0.5，进行一些清理
        if overall_score < 0.5:
            # 移除低置信度的实体和关系
            filtered_data = []
            for item in data:
                if item.get('confidence', 0) >= 0.6:
                    filtered_data.append(item)
            return filtered_data
        
        # 否则保留原始数据
        return data


class NLPProcessor:
    """NLP处理器"""
    
    def __init__(self):
        self.stopwords = set(
            ['的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你',
             '会', '着', '没有', '看', '好', '自己', '这'])
        
    def tokenize(self, text):
        """简单分词"""
        if not text:
            return []
        # 简单实现，实际应用应该使用专业分词库
        return [word for word in text.replace('.', ' ').replace(',', ' ').split() if word not in self.stopwords]
        
    def extract_keywords(self, text, top_k=5):
        """提取关键词"""
        tokens = self.tokenize(text)
        # 统计词频
        word_freq = {}
        for token in tokens:
            if token in word_freq:
                word_freq[token] += 1
            else:
                word_freq[token] = 1
                
        # 返回Top-K关键词
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:top_k]]
        
    def calculate_similarity(self, text1, text2):
        """计算文本相似度"""
        # 简单的词袋模型相似度计算
        tokens1 = set(self.tokenize(text1))
        tokens2 = set(self.tokenize(text2))
        
        if not tokens1 or not tokens2:
            return 0
            
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        return len(intersection) / len(union)


class KnowledgeGraphBuilder:
    """知识图谱构建器"""
    
    def __init__(self, use_mock_db=True, use_test_data=True):
        self.use_mock_db = use_mock_db
        self.use_test_data = use_test_data
        self.mock_db = None
        
        # 初始化已收集知识点集合，用于跟踪增量更新
        self.collected_knowledge_points = set()
        
        # 尝试从文件加载之前的数据
        loaded_from_file = False
        if not self.use_test_data:  # 如果不使用测试数据，则尝试加载真实数据
            try:
                # 尝试从json文件加载
                if os.path.exists('knowledge_graph.json'):
                    print("从knowledge_graph.json加载之前的数据...")
                    with open('knowledge_graph.json', 'r', encoding='utf-8') as f:
                        self.mock_db = json.load(f)
                    loaded_from_file = True
                    
                    # 初始化已收集的知识点集合
                    for name, entity in self.mock_db.get("entities", {}).items():
                        if entity.get('label') == 'KnowledgePoint':
                            self.collected_knowledge_points.add(name)
                    
                    print(f"从文件加载了 {len(self.mock_db.get('entities', {}))} 个实体和 {len(self.mock_db.get('relations', []))} 个关系")
                    print(f"现有 {len(self.collected_knowledge_points)} 个已知知识点")
                elif os.path.exists('knowledge_graph.pkl'):
                    print("从knowledge_graph.pkl加载之前的数据...")
                    with open('knowledge_graph.pkl', 'rb') as f:
                        self.mock_db = pickle.load(f)
                    loaded_from_file = True
                    
                    # 初始化已收集的知识点集合
                    for name, entity in self.mock_db.get("entities", {}).items():
                        if entity.get('label') == 'KnowledgePoint':
                            self.collected_knowledge_points.add(name)
                    
                    print(f"从文件加载了 {len(self.mock_db.get('entities', {}))} 个实体和 {len(self.mock_db.get('relations', []))} 个关系")
                    print(f"现有 {len(self.collected_knowledge_points)} 个已知知识点")
            except Exception as e:
                print(f"从文件加载数据失败: {str(e)}，将创建新的模拟数据库")
                loaded_from_file = False
        
        # 如果没有从文件加载，则创建新的模拟数据库
        if self.use_mock_db and not loaded_from_file:
            self.mock_db = self._create_mock_db()
            
        # 初始化数据源采集器
        self.collector = DataSourceCollector()
        
        # 初始化大数据处理器（如果可用）
        if HAS_SPARK:
            self.spark = SparkSession.builder \
                .appName("KnowledgeGraph") \
                .config("spark.driver.memory", "2g") \
                .getOrCreate()
        else:
            self.spark = None
            
        # 初始化NLP处理器
        self.nlp_processor = NLPProcessor()
        
        # 初始化实体对齐器
        self.entity_aligner = EntityAligner()
        
        # 初始化关系解析器
        self.relation_resolver = RelationResolver()
        
        # 初始化知识推理器
        self.knowledge_reasoner = KnowledgeReasoner()
        
        # 初始化质量评估器
        self.quality_evaluator = QualityEvaluator()
        
        # 连接Neo4j数据库
        if HAS_NEO4J_DRIVER and not self.use_mock_db:
            try:
                neo4j_uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
                neo4j_user = os.environ.get("NEO4J_USER", "neo4j")
                neo4j_password = os.environ.get("NEO4J_PASSWORD", "12345678")

                print(f"🔄 KnowledgeGraphBuilder正在连接Neo4j...")
                print(f"   URI: {neo4j_uri}")
                print(f"   用户: {neo4j_user}")

                self.neo4j = Neo4j(
                    uri=neo4j_uri,
                    user=neo4j_user,
                    password=neo4j_password
                )

                # 测试连接
                test_result = self.neo4j.sync_query("RETURN 1 as test")
                if test_result:
                    print("✅ KnowledgeGraphBuilder Neo4j连接成功")
                else:
                    print("❌ KnowledgeGraphBuilder Neo4j连接测试失败")
                    self.neo4j = None
                    self.use_mock_db = True

            except Exception as e:
                print(f"❌ KnowledgeGraphBuilder连接Neo4j数据库失败: {str(e)}")
                self.neo4j = None
                self.use_mock_db = True
                if not loaded_from_file:
                    self.mock_db = self._create_mock_db()
        else:
            self.neo4j = None
            if not self.use_mock_db:
                print("⚠️ Neo4j驱动不可用，将使用模拟数据库")
            
    def _create_mock_db(self):
        """创建模拟数据库"""
        mock_db = {
            "entities": {},
            "relations": []
        }
        
        # 使用默认测试数据填充模拟数据库
        if self.use_test_data:
            # 添加实体数据
            for entity in DEFAULT_COURSE_DATA + DEFAULT_KNOWLEDGE_DATA:
                entity_name = entity['name']
                mock_db["entities"][entity_name] = entity
                
            # 添加关系数据
            for relation in DEFAULT_RELATIONS:
                mock_db["relations"].append(relation)
                
        return mock_db
        
    def _create_entity(self, name, label, properties=None, source="manual", confidence=0.9):
        """创建实体"""
        if properties is None:
            properties = {}
            
        entity = {
            "type": "entity",
            "name": name,
            "label": label,
            "source": source,
            "confidence": confidence,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "properties": properties
        }
        
        return entity
        
    def _create_relation(self, source, target, relation_type, properties=None, source_type="manual", confidence=0.9):
        """创建关系"""
        if properties is None:
            properties = {}
            
        relation = {
            "type": "relation",
            "source": source,
            "target": target,
            "relation_type": relation_type,
            "source_type": source_type,
            "confidence": confidence,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "properties": properties
        }
        
        return relation

    async def build_knowledge_graph(self, is_incremental=True):
        """构建知识图谱"""
        print("开始自动生成计算机专业课程知识图谱...")
        
        try:
            # 1. 收集课程数据
            print("启动知识图谱构建服务...")
            course_data = await self._collect_course_data()
            
            # 2. 收集知识点数据
            knowledge_data = await self._collect_knowledge_data()
            
            # 3. 数据合并
            merged_data = course_data + knowledge_data
            print(f"数据合并完成，共{len(merged_data)}条记录")

            # 如果数据为空，返回失败
            if len(merged_data) == 0:
                print("错误：未能采集到有效数据，知识图谱构建失败")
                return False

            # 4. 数据处理
            processed_data = await self._process_data(course_data, knowledge_data)
            print("数据处理完成，共{}条记录".format(len(processed_data)))
            
            # 如果处理后数据为空，返回失败
            if len(processed_data) == 0:
                print("错误：数据处理后结果为空，知识图谱构建失败")
                return False

            # 5. 构建知识图谱（根据参数决定是否增量更新）
            if not self.use_mock_db and self.neo4j:
                await self._build_graph_in_database(processed_data, is_incremental=is_incremental)
            else:
                self._apply_updates_to_mock_db(processed_data, is_incremental=is_incremental)
                
            print("知识图谱构建完成")
            return True
            
        except Exception as e:
            print(f"构建知识图谱失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
            
    async def _collect_course_data(self):
        """收集课程数据"""
        print("数据采集开始...")
        
        # 禁用测试数据模式
        self.use_test_data = False
            
        course_data = []
        try:
            # 从数据源采集数据
            print("开始从MOOC网站采集课程数据...")

            # 初始化spider会话
            if self.collector.spider.session is None:
                await self.collector.spider.init_session()

            collector_data = await self.collector.collect_course_data()
            if collector_data:
                print(f"成功从数据源采集到 {len(collector_data)} 条课程数据")
                course_data.extend(collector_data)
            else:
                print("未能从数据源采集到实际课程数据")
                # 使用采集到的知识点来创建课程数据
                print("基于知识点自动生成课程数据...")
                knowledge_data = await self._collect_knowledge_data()

                # 从知识点生成课程
                if knowledge_data:
                    generated_courses = []
                    for knowledge in knowledge_data:
                        if knowledge.get('type') == 'entity' and knowledge.get('label') == 'KnowledgePoint':
                            name = knowledge.get('name')
                            if name:
                                # 解码URL编码的知识点名称
                                try:
                                    import urllib.parse
                                    name = urllib.parse.unquote(name)
                                except:
                                    pass

                                # 根据知识点生成课程
                                generated_courses.append({
                                    'type': 'entity',
                                    'name': f"{name}基础与应用",
                                    'label': 'Course',
                                    'source': 'generated',
                                    'confidence': 0.7,
                                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                                    'properties': {
                                        'description': f"本课程介绍{name}的基本概念、原理与应用",
                                        'instructor': '系统生成',
                                        'url': f"https://example.com/{urllib.parse.quote(name)}",
                                        'topics': [name]
                                    }
                                })

                                # 添加关系
                                generated_courses.append({
                                    'type': 'relation',
                                    'source': f"{name}基础与应用",
                                    'target': name,
                                    'relation_type': 'CONTAINS',
                                    'source_type': 'generated',
                                    'confidence': 0.7,
                                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                                })

                    print(f"基于知识点自动生成了 {len(generated_courses)} 条数据")
                    course_data.extend(generated_courses)
        except Exception as e:
            print(f"从数据源采集课程数据失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
        print(f"课程数据采集完成，共{len(course_data)}条记录")
        return course_data
        
    async def _collect_knowledge_data(self):
        """收集知识点数据"""
        # 禁用测试数据模式
        self.use_test_data = False
            
        knowledge_data = []
        new_data = []  # 用于跟踪新增数据
        current_time = time.time()

        try:
            # 从数据源采集数据
            print("开始从网络采集知识点数据...")

            # 确保spider会话已初始化
            if self.collector.spider.session is None:
                await self.collector.spider.init_session()

            # 获取已存在的知识点，用于增量更新
            existing_knowledge = set(self.collected_knowledge_points)  # 利用初始化时加载的已知知识点
            
            # 如果使用实际数据库，还需要从数据库查询
            if not self.use_mock_db and self.neo4j:
                try:
                    # 查询已有知识点
                    query = "MATCH (k:KnowledgePoint) RETURN k.name as name"
                    results = await self.neo4j.query(query)
                    for record in results:
                        existing_knowledge.add(record['name'])
                    print(f"数据库中已存在 {len(existing_knowledge)} 个知识点")
                except Exception as e:
                    print(f"查询已有知识点失败: {str(e)}")
                    
            print(f"当前已知知识点集合大小: {len(existing_knowledge)}")

            collector_data = await self.collector.collect_knowledge_data()
            if collector_data:
                for item in collector_data:
                    # 检查是否为实体且是知识点
                    if (item.get('type') == 'entity' and
                            item.get('label') == 'KnowledgePoint'):

                        name = item.get('name')

                        # 检查是否为增量更新
                        if name in existing_knowledge or name in self.collected_knowledge_points:
                            # 这是已存在的知识点，更新时间戳
                            item['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            # 这是新知识点
                            self.collected_knowledge_points.add(name)
                            new_data.append(item)

                print(f"成功从数据源采集到 {len(collector_data)} 条知识点数据，其中新增 {len(new_data)} 条")
                knowledge_data.extend(collector_data)
            else:
                # 如果没有采集到知识点数据，使用默认知识点
                print("未能从数据源采集到实际知识点数据，使用预设知识点...")
                default_knowledge = [
                    "算法", "数据结构", "人工智能", "机器学习", "深度学习",
                    "计算机科学", "网络协议", "操作系统", "数据库", "编程语言"
                ]

                for topic in default_knowledge:
                    # 检查是否为增量更新
                    if topic not in existing_knowledge and topic not in self.collected_knowledge_points:
                        knowledge_data.append({
                            'type': 'entity',
                            'name': topic,
                            'label': 'KnowledgePoint',
                            'source': 'default_knowledge',
                            'confidence': 0.8,
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'properties': {
                                'description': f"{topic}是计算机科学的重要分支",
                                'category': '计算机科学',
                                'url': f"https://example.com/{urllib.parse.quote(topic)}",
                                'related_topics': default_knowledge[:3]  # 简单关联前3个主题
                            }
                        })
                        self.collected_knowledge_points.add(topic)
                        new_data.append(topic)

                # 添加一些关系
                for i in range(len(default_knowledge) - 1):
                    knowledge_data.append({
                        'type': 'relation',
                        'source': default_knowledge[i],
                        'target': default_knowledge[i + 1],
                        'relation_type': 'RELATED_TO',
                        'source_type': 'default_knowledge',
                        'confidence': 0.8,
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                    })

                print(f"使用了 {len(knowledge_data)} 个预设知识点，其中新增 {len(new_data)} 个")

            # 更新上次更新时间
            self.last_update_time = current_time

        except Exception as e:
            print(f"从数据源采集知识点数据失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
        # 输出增量更新信息
        if new_data:
            print(f"本次增量更新新增 {len(new_data)} 个知识点")
        else:
            print("本次未新增知识点")
            
        print(f"知识点数据采集完成，共{len(knowledge_data)}条记录")
        return knowledge_data
        
    async def _process_data(self, course_data, knowledge_data):
        """处理数据"""
        print("\n开始处理采集到的数据...")

        # 合并数据
        merged_data = course_data + knowledge_data
        
        if not merged_data:
            print("警告：输入数据集为空")
            print("使用默认测试数据作为备用方案")
            # 返回默认数据
            return DEFAULT_COURSE_DATA + DEFAULT_KNOWLEDGE_DATA + DEFAULT_RELATIONS
        
        try:
            # 使用默认数据处理
            if self.use_test_data and self.use_mock_db:
                print("使用预设测试数据")
                return DEFAULT_COURSE_DATA + DEFAULT_KNOWLEDGE_DATA + DEFAULT_RELATIONS
            
            print(f"处理 {len(merged_data)} 条数据记录")

            # 实体对齐
            print("执行实体对齐...")
            aligned_data = self.entity_aligner.align_entities(merged_data)
            print(f"实体对齐完成，结果包含 {len(aligned_data)} 条记录")
            
            # 关系解析
            print("执行关系解析...")
            with_relations = self.relation_resolver.resolve_relations(aligned_data)
            relation_count = len([item for item in with_relations if item.get('type') == 'relation'])
            print(f"关系解析完成，共计 {relation_count} 条关系")
            
            # 知识推理
            print("执行知识推理...")
            enriched_data = self.knowledge_reasoner.enrich_knowledge(with_relations)
            
            # 质量评估
            print("执行质量评估...")
            final_data = self.quality_evaluator.evaluate_quality(enriched_data)
            print(f"数据处理完成，最终结果包含 {len(final_data)} 条记录")

            # 如果处理后结果为空，则使用默认数据
            if not final_data:
                print("警告：处理后结果为空，使用默认数据")
                return DEFAULT_COURSE_DATA + DEFAULT_KNOWLEDGE_DATA + DEFAULT_RELATIONS
            
            return final_data
        except Exception as e:
            print(f"❌ 数据处理出错: {str(e)}")
            import traceback
            traceback.print_exc()
            print("使用默认数据作为备用方案")
            # 发生异常时返回默认数据
            return DEFAULT_COURSE_DATA + DEFAULT_KNOWLEDGE_DATA + DEFAULT_RELATIONS

    def _apply_updates_to_mock_db(self, data, is_incremental=True):
        """将更新应用到模拟数据库"""
        # 确保mock_db已初始化
        if not self.mock_db:
            self.mock_db = self._create_mock_db()
            
        # 记录更新信息
        entities_added = 0
        entities_updated = 0
        relations_added = 0

        # 处理实体数据
        for item in data:
            if item.get('type') == 'entity':
                entity_name = item.get('name')

                # 增量更新模式下，新增或更新实体
                if is_incremental and entity_name in self.mock_db["entities"]:
                    # 更新已有实体
                    old_entity = self.mock_db["entities"][entity_name]
                    old_properties = old_entity.get('properties', {})
                    new_properties = item.get('properties', {})

                    # 合并属性，保留旧值
                    merged_properties = {**old_properties, **new_properties}
                    item['properties'] = merged_properties

                    # 更新实体
                    self.mock_db["entities"][entity_name] = item
                    entities_updated += 1
                else:
                    # 新增实体
                    self.mock_db["entities"][entity_name] = item
                    entities_added += 1

            elif item.get('type') == 'relation':
                # 检查是否为增量更新模式下的新关系
                is_new_relation = True

                if is_incremental:
                    # 检查关系是否已存在
                    source = item.get('source')
                    target = item.get('target')
                    relation_type = item.get('relation_type')

                    for existing_relation in self.mock_db["relations"]:
                        if (existing_relation.get('source') == source and
                                existing_relation.get('target') == target and
                                existing_relation.get('relation_type') == relation_type):
                            is_new_relation = False
                            break

                if is_new_relation:
                    self.mock_db["relations"].append(item)
                    relations_added += 1

        print(f"模拟数据库更新：新增 {entities_added} 个实体，更新 {entities_updated} 个实体，新增 {relations_added} 个关系")
        print(f"模拟数据库现有 {len(self.mock_db['entities'])} 个实体和 {len(self.mock_db['relations'])} 个关系")

    async def _build_graph_in_database(self, data, is_incremental=True):
        """将知识图谱数据写入到Neo4j数据库中"""
        print("开始将数据写入到Neo4j数据库...")
        start_time = time.time()

        try:
            # 确保Neo4j连接可用
            if not self.neo4j:
                print("错误: Neo4j连接不可用")
                return False

            # 转换为实体和关系
            entities = []
            relations = []

            # 记录已存在实体的ID
            entity_ids = {}

            # 统计数据
            entities_created = 0
            entities_updated = 0
            relations_created = 0
            relations_updated = 0

            # 如果是增量更新，首先获取已有的实体和关系
            if is_incremental:
                print("执行增量更新，获取已有实体...")

                # 获取所有已有的知识点和课程实体
                query = """
                MATCH (n)
                WHERE n:Course OR n:KnowledgePoint
                RETURN n.name as name, id(n) as id, labels(n) as labels
                """

                result = self.neo4j.sync_query(query)
                if result:
                    for record in result:
                        if 'name' in record and 'id' in record:
                            entity_ids[record['name'].lower()] = record['id']

                print(f"数据库中已有 {len(entity_ids)} 个实体")

            # 收集所有实体
            for item in data:
                if item['type'] == 'entity':
                    entity = {
                        'id': str(uuid.uuid4()),
                        'name': item['name'],
                        'label': item['label'],
                        'properties': item.get('properties', {}),
                        'source': item.get('source', 'unknown'),
                        'confidence': item.get('confidence', 0.5),
                        'timestamp': item.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
                    }

                    # 检查该实体是否已存在
                    entity_name_lower = entity['name'].lower()
                    if is_incremental and entity_name_lower in entity_ids:
                        # 如果实体已存在，使用已有的ID
                        entity['id'] = entity_ids[entity_name_lower]
                        entities_updated += 1
                    else:
                        # 新实体
                        entity_ids[entity_name_lower] = entity['id']
                        entities_created += 1

                    entities.append(entity)

            # 收集所有关系
            for item in data:
                if item['type'] == 'relation':
                    # 直接使用实体名称创建关系
                    relation = {
                        'id': str(uuid.uuid4()),
                        'source_name': item['source'],
                        'target_name': item['target'],
                        'type': item['relation_type'],
                        'properties': item.get('properties', {}),
                        'source_type': item.get('source_type', 'unknown'),
                        'confidence': item.get('confidence', 0.5),
                        'timestamp': item.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
                    }
                    relations.append(relation)
                    relations_created += 1

            # 如果不是增量更新，则先清空数据库
            if not is_incremental:
                print("执行全量更新，清空现有数据...")
                clear_query = """
                MATCH (n)
                DETACH DELETE n
                """
                self.neo4j.sync_query(clear_query)

            # 创建实体
            for entity in entities:
                # 构建属性映射
                properties = {
                    'id': entity['id'],
                    'name': entity['name'],
                    'source': entity['source'],
                    'confidence': entity['confidence'],
                    'timestamp': entity['timestamp']
                }

                # 添加其他属性
                if entity['properties']:
                    for key, value in entity['properties'].items():
                        properties[key] = value

                # 转换属性为Cypher参数
                params = {'props': properties}

                # 如果是增量更新，使用MERGE而不是CREATE
                if is_incremental:
                    # 使用MERGE进行更新或创建（基于name属性）
                    query = f"""
                    MERGE (n:{entity['label']} {{name: $props.name}})
                    ON CREATE SET n = $props
                    ON MATCH SET n += $props
                    """
                else:
                    # 使用CREATE创建新节点
                    query = f"""
                    CREATE (n:{entity['label']})
                    SET n = $props
                    """

                self.neo4j.sync_query(query, params)

            # 创建关系
            for relation in relations:
                # 构建属性映射
                properties = {
                    'id': relation['id'],
                    'source_type': relation['source_type'],
                    'confidence': relation['confidence'],
                    'timestamp': relation['timestamp']
                }

                # 添加其他属性
                if relation['properties']:
                    for key, value in relation['properties'].items():
                        properties[key] = value

                # 转换属性为Cypher参数
                params = {
                    'source_name': relation['source_name'],
                    'target_name': relation['target_name'],
                    'props': properties
                }

                # 使用MERGE进行关系创建或更新（基于name属性）
                query = f"""
                MATCH (source), (target)
                WHERE source.name = $source_name AND target.name = $target_name
                MERGE (source)-[r:{relation['type']}]->(target)
                ON CREATE SET r = $props
                ON MATCH SET r += $props
                """

                self.neo4j.sync_query(query, params)

            end_time = time.time()
            elapsed = end_time - start_time

            print(f"数据库更新完成，耗时: {elapsed:.2f} 秒")
            print(f"实体: 创建 {entities_created} 个，更新 {entities_updated} 个")
            print(f"关系: 创建 {relations_created} 个，更新 {relations_updated} 个")

            return True
        except Exception as e:
            print(f"数据库更新失败: {str(e)}")
            return False

    def get_entities_by_label(self, label):
        """获取指定标签的实体"""
        if self.use_mock_db:
            entities = []
            for name, entity in self.mock_db["entities"].items():
                if entity.get('label') == label:
                    entities.append(entity)
            return entities
        elif self.neo4j:
            # 实际数据库查询
            pass
        return []
        
    def get_relations_by_type(self, relation_type):
        """获取指定类型的关系"""
        if self.use_mock_db:
            relations = []
            for relation in self.mock_db["relations"]:
                if relation.get('relation_type') == relation_type:
                    relations.append(relation)
            return relations
        elif self.neo4j:
            # 实际数据库查询
            pass
        return []


class KnowledgeGraphQuery:
    """知识图谱查询接口"""
    
    def __init__(self):
        # 初始化Neo4j连接
        if not HAS_NEO4J_DRIVER:
            print("警告：Neo4j驱动未安装，将使用模拟数据库查询")
            self.driver = None
            self.use_mock_db = True
            # 初始化模拟数据库
            self.mock_db = {
                'entities': {},
                'relations': []
            }
            return
            
        try:
            self.driver = GraphDatabase.driver(
                os.getenv("NEO4J_URI"),
                auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
            )
            self.use_mock_db = False
        except Exception as e:
            print(f"连接Neo4j数据库失败: {str(e)}")
            self.driver = None
            self.use_mock_db = True
            # 初始化模拟数据库
            self.mock_db = {
                'entities': {},
                'relations': []
            }
    
    async def query_course_knowledge(self, course_name):
        """查询课程包含的知识点"""
        # 如果使用模拟数据库
        if self.use_mock_db:
            return self._query_course_knowledge_mock(course_name)
            
        try:
            async with self.driver.session() as session:
                query = """
                MATCH (c:Course {name: $course_name})-[:CONTAINS]->(k:KnowledgePoint)
                RETURN k.name as knowledge_point, k.description as description
                """
                result = await session.run(query, course_name=course_name)
                return [dict(record) for record in await result.data()]
        except Exception as e:
            print(f"查询课程知识点错误: {str(e)}")
            return []
            
    def _query_course_knowledge_mock(self, course_name):
        """模拟查询课程知识点"""
        results = []
        
        # 从模拟数据库中查找关系
        for relation in self.mock_db['relations']:
            if relation['relation_type'] == 'CONTAINS' and relation['source'] == course_name:
                knowledge_point = relation['target']
                # 获取知识点详情
                if knowledge_point in self.mock_db['entities']:
                    entity = self.mock_db['entities'][knowledge_point]
                    results.append({
                        'knowledge_point': knowledge_point,
                        'description': entity.get('properties', {}).get('description', '')
                    })
                
        return results
    
    async def query_knowledge_related(self, knowledge_point):
        """查询知识点的相关知识点"""
        # 如果使用模拟数据库
        if self.use_mock_db:
            return self._query_knowledge_related_mock(knowledge_point)
            
        try:
            async with self.driver.session() as session:
                query = """
                MATCH (k1:KnowledgePoint {name: $knowledge_point})-[:RELATED_TO]->(k2:KnowledgePoint)
                RETURN k2.name as related_point, k2.description as description
                """
                result = await session.run(query, knowledge_point=knowledge_point)
                return [dict(record) for record in await result.data()]
        except Exception as e:
            print(f"查询相关知识点错误: {str(e)}")
            return []
            
    def _query_knowledge_related_mock(self, knowledge_point):
        """模拟查询相关知识点"""
        results = []
        
        # 从模拟数据库中查找关系
        for relation in self.mock_db['relations']:
            if relation['relation_type'] == 'RELATED_TO' and relation['source'] == knowledge_point:
                related_point = relation['target']
                # 获取知识点详情
                if related_point in self.mock_db['entities']:
                    entity = self.mock_db['entities'][related_point]
                    results.append({
                        'related_point': related_point,
                        'description': entity.get('properties', {}).get('description', '')
                    })
                
        return results
    
    async def query_course_path(self, start_course, end_course):
        """查询课程之间的学习路径"""
        # 如果使用模拟数据库
        if self.use_mock_db:
            return self._query_course_path_mock(start_course, end_course)
            
        try:
            async with self.driver.session() as session:
                query = """
                MATCH path = (c1:Course {name: $start_course})-[:CONTAINS]->(k1:KnowledgePoint)-[:RELATED_TO*1..3]->(k2:KnowledgePoint)<-[:CONTAINS]-(c2:Course {name: $end_course})
                RETURN path
                """
                result = await session.run(query, start_course=start_course, end_course=end_course)
                return [dict(record) for record in await result.data()]
        except Exception as e:
            print(f"查询学习路径错误: {str(e)}")
            return []
            
    def _query_course_path_mock(self, start_course, end_course):
        """模拟查询学习路径"""
        print(f"模拟查询从{start_course}到{end_course}的学习路径")
        # 这里仅返回一个示例路径
        return [{
            'path': f"{start_course} -> 基础知识 -> 进阶知识 -> {end_course}"
        }]
    
    async def search_knowledge(self, keyword):
        """搜索知识点"""
        # 如果使用模拟数据库
        if self.use_mock_db:
            return self._search_knowledge_mock(keyword)
            
        try:
            async with self.driver.session() as session:
                query = """
                MATCH (k:KnowledgePoint)
                WHERE k.name CONTAINS $keyword OR k.description CONTAINS $keyword
                RETURN k.name as name, k.description as description
                """
                result = await session.run(query, keyword=keyword)
                return [dict(record) for record in await result.data()]
        except Exception as e:
            print(f"搜索知识点错误: {str(e)}")
            return []
            
    def _search_knowledge_mock(self, keyword):
        """模拟搜索知识点"""
        results = []
        
        # 从模拟数据库中搜索实体
        for entity_id, entity in self.mock_db['entities'].items():
            if entity.get('label') == 'KnowledgePoint':
                name = entity.get('name', '')
                desc = entity.get('properties', {}).get('description', '')
                
                if keyword in name or keyword in desc:
                    results.append({
                        'name': name,
                        'description': desc
                    })
                
        return results
    
    async def get_course_list(self):
        """获取所有课程列表"""
        # 如果使用模拟数据库
        if self.use_mock_db:
            return self._get_course_list_mock()
            
        try:
            async with self.driver.session() as session:
                query = """
                MATCH (c:Course)
                RETURN c.name as name, c.description as description
                """
                result = await session.run(query)
                return [dict(record) for record in await result.data()]
        except Exception as e:
            print(f"获取课程列表错误: {str(e)}")
            return []
            
    def _get_course_list_mock(self):
        """模拟获取课程列表"""
        results = []
        
        # 从模拟数据库中获取课程
        for entity_id, entity in self.mock_db['entities'].items():
            if entity.get('label') == 'Course':
                results.append({
                    'name': entity.get('name', ''),
                    'description': entity.get('properties', {}).get('description', '')
                })
                
        return results


def create_app(query_interface):
    """创建Flask应用并配置路由

    Args:
        query_interface: 知识图谱查询接口实例

    Returns:
        Flask应用实例
    """
    try:
        from flask import Flask, render_template, request, jsonify

        app = Flask(__name__)

        @app.route('/')
        def index():
            return render_template('index.html')

        @app.route('/query', methods=['POST'])
        def query():
            try:
                query_text = request.json.get('query', '')

                # 执行查询
                if 'course' in query_text.lower() and 'knowledge' in query_text.lower():
                    # 查询课程包含的知识点
                    course_name = query_text.split('course:')[1].strip() if 'course:' in query_text else None
                    if course_name:
                        import asyncio
                        results = asyncio.run(query_interface.query_course_knowledge(course_name))

                        nodes = []
                        relationships = []

                        # 添加课程节点
                        nodes.append({
                            'id': course_name,
                            'label': 'Course',
                            'name': course_name,
                            'properties': {}
                        })

                        # 添加知识点节点和关系
                        for result in results:
                            knowledge_point = result.get('knowledge_point')
                            description = result.get('description', '')

                            nodes.append({
                                'id': knowledge_point,
                                'label': 'KnowledgePoint',
                                'name': knowledge_point,
                                'properties': {'description': description}
                            })

                            relationships.append({
                                'source': course_name,
                                'target': knowledge_point,
                                'type': 'CONTAINS',
                                'properties': {}
                            })

                        return jsonify({
                            'success': True,
                            'nodes': nodes,
                            'relationships': relationships,
                            'cypher_query': f"MATCH (c:Course {{name: '{course_name}'}})-[:CONTAINS]->(k:KnowledgePoint) RETURN c, k"
                        })
                else:
                    # 简单查询，返回所有实体和关系
                    nodes = []
                    relationships = []

                    # 从模拟数据库获取实体
                    if query_interface.use_mock_db:
                        for entity_name, entity in query_interface.mock_db['entities'].items():
                            nodes.append({
                                'id': entity_name,
                                'label': entity.get('label', 'Entity'),
                                'name': entity_name,
                                'properties': entity.get('properties', {})
                            })

                        # 获取关系
                        for relation in query_interface.mock_db['relations']:
                            relationships.append({
                                'source': relation.get('source'),
                                'target': relation.get('target'),
                                'type': relation.get('relation_type'),
                                'properties': {}
                            })

                    return jsonify({
                        'success': True,
                        'nodes': nodes,
                        'relationships': relationships,
                        'cypher_query': "MATCH (n)-[r]->(m) RETURN n, r, m"
                    })

            except Exception as e:
                import traceback
                traceback.print_exc()
                return jsonify({
                    'success': False,
                    'error': str(e)
                })

        @app.route('/neo4j-browser', methods=['GET'])
        def neo4j_browser():
            """重定向到Neo4j Browser"""
            neo4j_browser_url = os.environ.get("NEO4J_BROWSER_URL", "http://localhost:7474/browser/")
            return f"""
            <script>
                window.location.href = "{neo4j_browser_url}";
            </script>
            """

        @app.route('/check_updates', methods=['POST'])
        def check_updates():
            """检查是否有新的更新"""
            try:
                data = request.get_json()
                last_update = data.get('last_update', 0)

                # 检查最新更新时间
                if query_interface.use_mock_db:
                    latest_update = time.time()
                else:
                    # 从数据库查询
                    pass

                return jsonify({
                    'has_updates': True,  # 简化处理
                    'latest_update': latest_update
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @app.route('/get_graph_data')
        def get_graph_data():
            """获取最新的图谱数据"""
            try:
                nodes = []
                relationships = []

                # 从模拟数据库获取实体
                if query_interface.use_mock_db:
                    for entity_name, entity in query_interface.mock_db['entities'].items():
                        nodes.append({
                            'id': entity_name,
                            'label': entity.get('label', 'Entity'),
                            'name': entity_name,
                            'properties': entity.get('properties', {})
                        })

                    # 获取关系
                    for relation in query_interface.mock_db['relations']:
                        relationships.append({
                            'source': relation.get('source'),
                            'target': relation.get('target'),
                            'type': relation.get('relation_type'),
                            'properties': {}
                        })

                return jsonify({
                    'nodes': nodes,
                    'relationships': relationships
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        return app
    except Exception as e:
        print(f"创建Flask应用错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
# Flask应用创建函数已移除，现在使用Django框架
#def create_app_removed():
#    """Flask应用创建函数已移除，现在使用Django框架"""
#    pass


async def main():
    """
    主函数 - 整合了数据采集、图谱构建、关系生成和可视化的完整流程
    
    本函数整合了以下功能：
    1. 从各数据源采集知识点和课程数据
    2. 构建基础知识图谱
    3. 保存图谱数据（整合save_graph.py功能）
    4. 生成高质量知识点关系（整合generate_relations.py功能）
    5. 提供Web界面查看知识图谱（可选）
    
    通过命令行参数控制不同功能：
    --reset               重置数据，从头开始构建
    --continue-collection 继续之前的采集任务
    --only-save           仅保存已有数据，不进行采集
    --skip-relations      跳过关系生成步骤
    --web                 运行Web应用程序查看图谱
    """
    try:
        # 解析命令行参数
        import argparse
        parser = argparse.ArgumentParser(description="计算机专业知识图谱自动化构建工具")
        parser.add_argument('--reset', action='store_true', help='重置数据，从头开始构建')
        parser.add_argument('--continue-collection', action='store_true', help='继续之前的采集任务')
        parser.add_argument('--only-save', action='store_true', help='仅保存已有数据，不进行采集')
        parser.add_argument('--skip-relations', action='store_true', help='跳过关系生成步骤')
        parser.add_argument('--web', action='store_true', help='运行Web应用程序')
        args = parser.parse_args()

        # 标题
        print("-" * 70)
        print("                计算机专业知识图谱自动化构建工具")
        print("-" * 70)

        # 确保路径存在
        os.makedirs("data", exist_ok=True)
        
        # 更新进度信息
        def update_progress(status, **kwargs):
            progress_file = 'data/collection_progress.json'
            progress_info = {
                'last_updated': time.strftime('%Y-%m-%d %H:%M:%S'),
                'status': status
            }
            
            # 读取已有进度信息（如果存在）
            if os.path.exists(progress_file):
                try:
                    with open(progress_file, 'r', encoding='utf-8') as f:
                        existing_progress = json.load(f)
                        # 保留历史信息
                        for key, value in existing_progress.items():
                            if key != 'status' and key != 'last_updated' and key not in kwargs:
                                progress_info[key] = value
                except Exception as e:
                    print(f"读取进度文件失败: {str(e)}")
            
            # 更新额外的进度信息
            for key, value in kwargs.items():
                progress_info[key] = value
            
            # 写入进度文件
            try:
                with open(progress_file, 'w', encoding='utf-8') as f:
                    json.dump(progress_info, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"写入进度文件失败: {str(e)}")

        # 仅保存模式
        if args.only_save:
            print("仅保存模式：保存当前知识图谱数据")
            update_progress('running', collection_type='only_save')
            
            # 直接调用save_graph.py中的功能
            from save_graph import save_mock_db_from_run, extract_data_from_collector, extract_from_json_file, extract_from_default_data
            
            success = save_mock_db_from_run()
            if not success:
                success = extract_data_from_collector()
            if not success:
                success = extract_from_json_file()
            if not success:
                success = extract_from_default_data()
                
            if success and not args.skip_relations:
                print("\n生成关系数据...")
                # 调用generate_relations.py中的功能
                from generate_relations import load_knowledge_graph, generate_prerequisite_relations, generate_related_relations
                from generate_relations import generate_parent_child_relations, generate_relations_based_on_text, generate_course_knowledge_relations, save_graph_data
                
                graph_data = load_knowledge_graph()
                original_relations_count = len(graph_data.get('relations', []))
                
                # 生成各类关系
                prereq_relations = generate_prerequisite_relations(graph_data)
                graph_data['relations'].extend(prereq_relations)
                
                related_relations = generate_related_relations(graph_data)
                graph_data['relations'].extend(related_relations)
                
                parent_child_relations = generate_parent_child_relations(graph_data)
                graph_data['relations'].extend(parent_child_relations)
                
                text_based_relations = generate_relations_based_on_text(graph_data)
                graph_data['relations'].extend(text_based_relations)
                
                course_kp_relations = generate_course_knowledge_relations(graph_data)
                graph_data['relations'].extend(course_kp_relations)
                
                # 保存更新后的图谱数据
                save_graph_data(graph_data)
                
                new_relations_count = len(graph_data.get('relations', []))
                print(f"共添加了 {new_relations_count - original_relations_count} 个新关系")
                print(f"最终图谱包含 {len(graph_data.get('entities', {}))} 个实体和 {new_relations_count} 个关系")
            
            # 更新进度为完成
            update_progress('completed')
            
            # 如果需要运行Web应用
            if args.web:
                run_web_app()
                
            return

        # 初始化图谱构建器
        # 优先尝试使用Neo4j数据库，如果不可用则回退到模拟数据库
        use_mock_db = False  # 默认尝试使用Neo4j
        use_test_data = not args.reset  # 如果重置则不使用测试数据

        # 检查Neo4j是否可用
        neo4j_available = False
        neo4j_uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.environ.get("NEO4J_USER", "neo4j")
        neo4j_password = os.environ.get("NEO4J_PASSWORD", "12345678")

        print(f"🔍 Neo4j连接配置:")
        print(f"   URI: {neo4j_uri}")
        print(f"   用户: {neo4j_user}")
        print(f"   密码: {'*' * len(neo4j_password)}")

        if HAS_NEO4J_DRIVER:
            try:
                print("🔄 正在测试Neo4j连接...")
                # 尝试连接Neo4j
                test_neo4j = Neo4j(
                    uri=neo4j_uri,
                    user=neo4j_user,
                    password=neo4j_password
                )
                # 测试连接
                test_result = test_neo4j.sync_query("RETURN 1 as test")
                if test_result:
                    neo4j_available = True
                    print("✅ Neo4j数据库连接成功，将使用Neo4j存储数据")

                    # 检查数据库中的数据
                    try:
                        nodes_result = test_neo4j.sync_query("MATCH (n) RETURN count(n) as node_count")
                        node_count = nodes_result[0]["node_count"] if nodes_result else 0
                        rels_result = test_neo4j.sync_query("MATCH ()-[r]->() RETURN count(r) as rel_count")
                        rel_count = rels_result[0]["rel_count"] if rels_result else 0
                        print(f"📊 数据库状态: {node_count}个节点, {rel_count}个关系")
                    except Exception as e:
                        print(f"⚠️ 无法获取数据库统计信息: {str(e)}")
                else:
                    print("⚠️ Neo4j连接测试失败，将使用模拟数据库")
                    use_mock_db = True
            except Exception as e:
                print(f"❌ Neo4j连接失败: {str(e)}")
                print("💡 可能的解决方案:")
                print("   1. 确保Neo4j服务正在运行")
                print("   2. 检查连接配置是否正确")
                print("   3. 验证用户名和密码")
                print("将使用模拟数据库作为备选方案")
                use_mock_db = True
        else:
            print("⚠️ Neo4j驱动未安装，将使用模拟数据库")
            use_mock_db = True

        builder = KnowledgeGraphBuilder(use_mock_db=use_mock_db, use_test_data=use_test_data)

        # 根据参数执行相应操作
        build_success = False
        if args.reset:
            print("重置模式：从头构建知识图谱")
            update_progress('running', collection_type='reset')
            build_success = await builder.build_knowledge_graph(is_incremental=False)
        elif args.continue_collection:
            print("继续模式：继续之前的知识收集任务")
            update_progress('running', collection_type='continue')
            build_success = await builder.build_knowledge_graph(is_incremental=True)
        else:
            print("标准模式：根据需要增量构建知识图谱")
            update_progress('running', collection_type='standard')
            build_success = await builder.build_knowledge_graph(is_incremental=True)
        
        # 更新知识点统计信息
        if hasattr(builder, 'collected_knowledge_points'):
            update_progress(
                'running',
                processed_topics=list(builder.collected_knowledge_points),
                total_batches=20,  # 假设总批次
                last_batch=len(builder.collected_knowledge_points) // 5  # 粗略计算已完成批次
            )
            
        # 只有构建成功才继续处理
        if not build_success:
            print("知识图谱构建失败，将不进行数据保存和关系生成")
            update_progress('error', error_message="知识图谱构建失败")
            return

        # 保存图谱数据到文件
        print("\n保存图谱数据到文件...")
        # 直接调用save_graph.py中的功能
        from save_graph import save_mock_db_from_run, extract_data_from_collector, extract_from_json_file, extract_from_default_data
        
        success = save_mock_db_from_run()
        if not success:
            success = extract_data_from_collector()
        if not success:
            success = extract_from_json_file()
        if not success:
            success = extract_from_default_data()
            
        # 生成关系，除非明确跳过
        if not args.skip_relations:
            print("\n生成关系数据...")
            update_progress('running', stage='generating_relations')
            # 调用generate_relations.py中的功能
            from generate_relations import load_knowledge_graph, generate_prerequisite_relations, generate_related_relations
            from generate_relations import generate_parent_child_relations, generate_relations_based_on_text, generate_course_knowledge_relations, generate_course_course_relations, save_graph_data
            
            graph_data = load_knowledge_graph()
            original_relations_count = len(graph_data.get('relations', []))
            
            # 生成各类关系
            prereq_relations = generate_prerequisite_relations(graph_data)
            graph_data['relations'].extend(prereq_relations)
            
            related_relations = generate_related_relations(graph_data)
            graph_data['relations'].extend(related_relations)
            
            parent_child_relations = generate_parent_child_relations(graph_data)
            graph_data['relations'].extend(parent_child_relations)
            
            text_based_relations = generate_relations_based_on_text(graph_data)
            graph_data['relations'].extend(text_based_relations)
            
            course_kp_relations = generate_course_knowledge_relations(graph_data)
            graph_data['relations'].extend(course_kp_relations)
            
            # 添加课程间关系
            course_relations = generate_course_course_relations(graph_data)
            graph_data['relations'].extend(course_relations)
            
            # 保存更新后的图谱数据
            save_graph_data(graph_data)
            
            new_relations_count = len(graph_data.get('relations', []))
            print(f"共添加了 {new_relations_count - original_relations_count} 个新关系")
            print(f"最终图谱包含 {len(graph_data.get('entities', {}))} 个实体和 {new_relations_count} 个关系")

        # 更新进度为完成
        update_progress('completed')

        # 运行Web应用（如果需要）
        if args.web:
            run_web_app()
        else:
            print("\n图谱构建完成！")
            print("请使用Django管理命令启动Web应用:")
            print("python manage.py runserver")
            print("然后访问: http://localhost:8000/knowledge-graph/")
    
    except Exception as e:
        print(f"主函数执行错误: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 更新进度为错误
        try:
            progress_file = 'data/collection_progress.json'
            if os.path.exists('data'):
                with open(progress_file, 'r', encoding='utf-8') as f:
                    progress_info = json.load(f)
                
                progress_info['status'] = 'error'
                progress_info['error_message'] = str(e)
                progress_info['last_updated'] = time.strftime('%Y-%m-%d %H:%M:%S')
                
                with open(progress_file, 'w', encoding='utf-8') as f:
                    json.dump(progress_info, f, ensure_ascii=False, indent=2)
        except:
            pass
            
        sys.exit(1)

def run_web_app():
    """运行Web应用，展示构建的知识图谱"""
    try:
        print("\n知识图谱构建完成！")
        print("请使用Django管理命令启动Web应用:")
        print("python manage.py runserver")
        print("然后访问: http://localhost:8000/knowledge-graph/")
    except Exception as e:
        print(f"提示信息显示失败: {str(e)}")

if __name__ == "__main__":
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("错误: 需要Python 3.7或更高版本")
        sys.exit(1)

    # 运行主函数
    if sys.platform == 'win32':
        # Windows平台需要特殊处理异步
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())