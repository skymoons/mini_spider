#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""迷你定向网页抓取器"""

import re
import threading
import getopt
import ConfigParser
import urllib
import urllib2
import urlparse
import logging
import sys
import socket
import time
import os
import Queue

import bs4
import chardet

reload(sys)
sys.setdefaultencoding('utf8')

class SpiderThread(threading.Thread):
    """网页抓取线程"""
    def __init__(self, url, config, queue, logger, history, lock):
        threading.Thread.__init__(self)
        self.url = url
        self.config = config
        self.lock = lock
        self.history = history
        self.queue = queue
        self.logger = logger
        self.pattern = re.compile(self.config['target_url'])
        self.headers = {'User-Agent':\
                'Mozilla/5.0 (Windows NT 5.2; rv:7.0.1) Gecko/20100101 FireFox/7.0.1'}

    def download(self, url):
        """Download File"""
        self.url = url 
        local_path = self.config['output_directory']
        if not os.path.exists(local_path):
            try:
                os.mkdir(local_path)
            except os.error as err:
                self.logger.error("download to path, mkdir errror: %s" % err)

        try:
            path = os.path.join(local_path, self.url.replace('/', '_').replace(':', '_')
                                .replace('?', '_').replace('\\', '_'))
            self.logger.info("download url: %s" % self.url)
            urllib.urlretrieve(self.url, path, None)
        except Exception as err:
            self.logger.error("download url fail. url: %s" % self.url)
            return False
        return True

    def crawl_content(self):
        """请求URL，并判断返回结果的字符集"""
        try:
            #self.logger.debug(self.url)
            req = urllib2.Request(self.url, headers = self.headers)
            code = urllib2.urlopen(req).getcode()
            if (200 == code or 302 == code):
                content = urllib2.urlopen(req).read()
                charset = chardet.detect(content)
                if charset == 'utf-8' or charset == 'UTF-8':
                    return content
                else:
                    try:
                        content = content.decode('GBK', 'ignore').encode('utf-8')
                        return content
                    except UnicodeDecodeError as err:
                        logger.error("Decode html error %s", err)
                self.logger.debug("%s charset is %s" % (self.url, charset))
        except urllib2.HTTPError as err1:
            #self.logger.debug(self.url)
            self.logger.debug(str(err1))
        except Exception as err2:
            #self.logger.debug(self.url)
            self.logger.debug(str(err2))

    def spider(self):
        """对URL进行抓取，返回页面中包含的URL的列表"""
        content = self.crawl_content()
        if not content:
            self.logger.info(self.url + ' crawl fail')
            return []
        soup = bs4.BeautifulSoup(content, 'html.parser')
        urls = []
        new_links = []
        base_url = self.url.strip('/ ')
        anchors = soup.findAll('a', attrs = {'href': True})
        for a in anchors:
            if not a['href'].startswith('javascript'):
                urls.append(a['href'])
        anchors = soup.findAll('img', attrs = {'src': True})
        for a in anchors:
            urls.append(a['src'])
        for url in urls:
            
            if url.startswith('http') or url.startswith('//'):
                url = urlparse.urlparse(url, scheme='http').geturl()
            else:
                url = urlparse.urljoin(base_url, url)
            #self.logger.info(url)    
            new_links.append(url)
            # if not link.startswith('http'):
            #     try:
            #         url = urlparse.urljoin('http', link.strip('/'))
            #         self.logger.info(url)
            #         time.sleep(5)
                     
            #     except UnicodeDecodeError as msg:
            #         self.logger.error('Url parse error.Message: %s' % msg)
            # else:
            #     new_links.append(link.strip('/'))
        return new_links

    def run(self):
        urls = self.spider()
        self.logger.error(len(urls))
        for url in urls:
            #self.logger.error(url)
            prog = self.pattern
            if prog.match(url):
                self.logger.error(url)
                st = self.download(url)
            #self.logger.info(url)
            if len(self.history) > self.config['thread_count'] * 8:
                if url in self.history:
                    self.logger.debug("Url has been fetched: {url}".format(url=url))
                    #lock.release()
                    return
            lock = self.lock()
            lock.acquire()
            self.history.append(url)
            #self.logger.error(self.history)
            self.queue.put(url, block = False)
            lock.release()


class Spider(object):
    """网页抓取控制器"""
    def __init__(self):
        self.logger = self.init_logger()

    def init_logger(self):
        """初始化日志对象"""
        logger = logging.getLogger('mini_spider')
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler('mini_spider.log')
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        format = '%(asctime)s - %(threadName)s - %(levelname)s - %(lineno)d - %(message)s'
        formatter = logging.Formatter(format)
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)
        return logger

    def version(self):
        """打印版本信息"""
        print 'mini spider version 1.0'

    def usage(self):
        """打印程序介绍"""
        print 'This is a mini spider'

    def check_config(self, data):
        """校验配置文件格式
         Args:
            data: 配置文件数据
         Returns:
            返回格式化后的配置文件数据
         Raises:
            ValueError: an exception of configParser
        """
        data_keys = data.keys()
        need_keys = ['url_list_file', 'output_directory', 'max_depth', 'crawl_interval',\
                'crawl_timeout', 'target_url', 'thread_count']
        if set(data_keys) >= set(need_keys):
            try:
                data['max_depth'] = (int)(data['max_depth'])
                data['crawl_interval'] = (float)(data['crawl_interval'])
                data['crawl_timeout'] = (float)(data['crawl_timeout'])
                data['thread_count'] = (int)(data['thread_count'])
            except ValueError as err:
                self.logger.error(str(err))
                return
            return data
        else:
            self.logger.warn('config keys is:' + str(data_keys))

    def read_config(self, filename):
        """读取配置文件
         Args:
            conf_file: 配置文件名称
         Returns:
            返回配置文件数据
         Raises:
            ValueError: an exception of configParser
        """
        cf = ConfigParser.ConfigParser()
        cf.read(filename)
        data = {}
        try:
            spider = cf.items('spider')
        except Exception as err:
            self.logger.error(str(err))
        for (key, value) in spider:
            data[key] = value
        return data

    def main(self):
        """主程序"""
        try:
            opts, args = getopt.getopt(sys.argv[1:], 'hc:v', ['help', 'config='])
        except getopt.GetoptError as err:
            self.logger.error(str(err))
            usage()
            sys.exit(2)
        filename = None
        config = None
        for option, name in opts:
            if option == '-v':
                version()
            elif option in ('-h', '--help'):
                usage()
                sys.exit()
            elif option in ('-c', '--config'):
                filename = name
                self.logger.debug('config filename: ' + filename)
                data = self.read_config(filename)
                config = self.check_config(data)
            else:
                assert False, 'unhandled option'
        if not config:
            self.logger.info('read config fail')
            sys.exit()
        try:
            f = open(config['url_list_file'], 'r')
        except IOError as err:
            self.logger.error(str(err))

        socket.setdefaulttimeout(config['crawl_timeout'])
        lines = f.readlines()
        links = set(lines)
        new_links = set()
        lock = threading.Lock
        history =[]
        for i in xrange(config['max_depth'] + 1):
            output = Queue.Queue(maxsize = 0)
            for link in links:
                st = SpiderThread(link, config, output, self.logger, history, lock)
                while True:
                    if threading.activeCount() < config['thread_count']:
                        break
                st.start()
                self.logger.debug('active thread count:' + str(threading.activeCount()))
                time.sleep(config['crawl_interval'])
            while True:
                if threading.activeCount() < 2:
                    break
            while not output.empty():
                out = output.get(block = False)
                if out:
                    new_links.add(out)
            links = new_links
            new_links = set()
            self.logger.info('depth:' + str(i))

if __name__ == '__main__':
    spider = Spider()
    spider.main()
