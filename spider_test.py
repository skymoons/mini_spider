#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""迷你定向网页抓取器测试程序"""

import unittest
from mini_spider import SpiderThread
from mini_spider import Spider

class TestSpiderThreadUrlError(unittest.TestCase):
    """网页抓取线程测试类"""
    def setUp(self):
        """初始化日志对象"""
        self.logger = MiniSpider().init_logger()

    def tearDown(self):
        """结束不做处理"""
        pass

    def test_crawl_content(self):
        """选择可抓取的URL和格式错误的URL进行测试"""
        config = {'target_url': '.*\\.(gif|png|jpg|bmp)$', 'thread_count': '8', 'output_directory':\
                './output', 'crawl_timeout': '1', 'crawl_interval': '1', 'url_list_file': './urls',\
                'max_depth': '1'}
        url1 = 'http://pycm.baidu.com:8081'
        test_obj1 = SpiderThread(url1, config, None, self.logger)
        url2 = 'aaa'
        test_obj2 = SpiderThread(url2, config, None, self.logger)
        self.assertNotEqual(test_obj1.crawl_content(), None)
        self.assertEqual(test_obj2.crawl_content(), None)


class TestMiniSpiderParamError(unittest.TestCase):
    """网页抓取控制器测试类"""
    def setUp(self):
        """初始化网页抓取对象"""
        self.test_obj = MiniSpider()

    def tearDown(self):
        """结束不做处理"""
        pass

    def test_check_config(self):
        """选择格式正确以及缺少参数和参数格式错误的异常情况进行测试"""
        config1 = {'target_url': '.*\\.(gif|png|jpg|bmp)$', 'thread_count': '8', 'output_directory':\
                './output', 'crawl_timeout': '1', 'crawl_interval': '1', 'url_list_file': './urls',\
                'max_depth': '1'}
        config2 = {'target_url': '.*\\.(gif|png|jpg|bmp)$', 'thread_count': '8', 'output_directory':\
                './output', 'crawl_timeout': '1', 'crawl_interval': '1', 'url_list_file': './urls'}
        config3 = {'target_url': '.*\\.(gif|png|jpg|bmp)$', 'thread_count': '8', 'output_directory':\
                './output', 'crawl_timeout': '1', 'crawl_interval': '1', 'url_list_file': './urls',\
                'max_depth': 'a'}
        expect = {'target_url': '.*\\.(gif|png|jpg|bmp)$', 'thread_count': 8, 'output_directory':\
                './output', 'crawl_timeout': 1, 'crawl_interval': 1, 'url_list_file': './urls',\
                'max_depth': 1}
        self.assertEqual(self.test_obj.check_config(config1), expect)
        self.assertEqual(self.test_obj.check_config(config2), None)
        self.assertEqual(self.test_obj.check_config(config3), None)

    def test_read_config(self):
        """读取配置文件，并与预先设计好的字典进行对比"""
        filename1 = 'spider.conf'
        expect = {'target_url': '.*\\.(gif|png|jpg|bmp)$', 'thread_count': '8', 'output_directory':\
                './output', 'crawl_timeout': '1', 'crawl_interval': '1', 'url_list_file': './urls',\
                'max_depth': '1'}
        self.assertEqual(self.test_obj.read_config(filename1), expect)

if __name__ == '__main__':
    unittest.main()
