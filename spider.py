# -*- coding: utf-8 -*-

import urlparse
import urllib
import requests
from lxml import html
import os
import uuid
import requests
import grequests


class SpiderPdf(object):

    def __init__(self, url, limit_num=10):
        parsed_uri = urlparse.urlparse(url)
        self.dom_url = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        self.path = parsed_uri[2]
        self.main_url = url
        self.limit_num = limit_num
        self.download_urls = []
        self.session = requests.Session()

    def _get_dom_url_html(self, url, timeout=False):
        '''
        Download html of main url
        '''
        if not timeout:
            resp = self.session.get(url)
        else:
            try:
                resp = self.session.get(url, timeout=2)
            except requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError:
                return ''
        return resp.content

    def _get_next_page(self, res_html):
        return res_html.xpath(u'//a[text()="下一页"]/@href')

    def _get_download_url(self, urls):
        pdf_urls = []
        for url in urls:
            url_html = self._get_dom_url_html(url, timeout=True)
            if not url_html:
                continue
            res_html = html.fromstring(url_html)
            pdf_url = res_html.xpath(u'//div[@class="maindown_w4"]/a[@class="maindown4"]/@href')
            title = res_html.xpath(u'//head/title/text()')
            if pdf_url and title:

                pdf_urls.append({'url': urlparse.urljoin(self.dom_url, pdf_url[0]),
                                'title': title[0].replace(' ', '')})
        return pdf_urls

    def get_urls_by_html(self):
        '''
        Parse html for get pdf urls
        '''
        url_html = self._get_dom_url_html(self.main_url)
        while True:

            if len(self.download_urls) > self.limit_num:
                break

            res_html = html.fromstring(url_html)
            urls = res_html.xpath('//dl[@class="mid_dl"]/dt[@class="dt_a"]/a/@href')
            if not urls:
                break
            else:
                pdf_urls = self._get_download_url(urls)
                self.download_urls.extend(pdf_urls)
                nextpg_url = self._get_next_page(res_html)
                if not nextpg_url or len(self.download_urls) > self.limit_num:
                    break
                url_html = self._get_dom_url_html(urlparse.urljoin(self.dom_url,
                                                                self.path + nextpg_url[0]))

        return self.download_urls[:self.limit_num]


class AsyncRecvPDF(object):
    def __init__(self, recv_pdf=[]):
        self.recvpdf_urls = recv_pdf
        print self.recvpdf_urls
        if not os.path.exists('./download_pdf'):
            os.mkdir('./download_pdf')

    def run_download(self):
        import pdb; pdb.set_trace()
        aync_list = [grequests.get(item['url'],
                    hooks={'response': [hook_factory(title=item['title'])]})
                    for item in self.recvpdf_urls]
        return grequests.map(aync_list)


def hook_factory(*f_args, **f_kwargs):
    def do_something(response, *args, **kwargs):
        import pdb; pdb.set_trace()
        dir_file = './download_pdf/'
        filename = dir_file + f_kwargs['title'] + str(uuid.uuid1())[:4] + '.pdf'
        with open(filename, 'wb') as f:
            f.write(response.content)
        return None
    return do_something


def main():
    import sys
    num = None
    if '-find' not in sys.argv:
        print 'Please input url'
        exit(1)
    else:
        try:
            keyword = sys.argv[sys.argv.index('-find')+1].decode('utf8').encode('gbk')
        except UnicodeDecodeError:
            keyword = sys.argv[sys.argv.index('-find')+1].encode('gbk')

    if '-number' in sys.argv:
        try:
            num = int(sys.argv[sys.argv.index('-number')+1])
        except Exception:
            print 'Please input correct number'
            exit(1)
    data = {'keyword': keyword,
            'category': 0,
            'day': 't',
            'page': 1}
    url = "xxxxxxxxxx" + urllib.urlencode(data)
    if num:
        spider = SpiderPdf(url, num)
    else:
        spider = SpiderPdf(url)

    recv_pdf = spider.get_urls_by_html()

    print recv_pdf

    recvpdf_obj = AsyncRecvPDF(recv_pdf)
    recvpdf_obj.run_download()


if __name__ == '__main__':
    main()
