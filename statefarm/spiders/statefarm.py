import re
import scrapy

from urlparse import urljoin
from lxml import html


class StateFarmItem(scrapy.Item):
    Name = scrapy.Field()
    Address = scrapy.Field()
    City = scrapy.Field()
    Phone_number = scrapy.Field()


class StateFarmAgentSpider(scrapy.Spider):

    name = 'statefarm'

    allowed_domains = ["statefarm.com"]

    start_urls = ['https://www.statefarm.com/agent/us']

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/41.0.2228.0 Safari/537.36', }

    def __init__(self, *args, **kwargs):
        super(StateFarmAgentSpider, self).__init__(site_name=self.allowed_domains[0], *args, **kwargs)
        self.current_page = 0

    def start_requests(self):
        yield scrapy.Request(url=self.start_urls[0], callback=self.parse_by_state, headers=self.headers)

    def parse_by_state(self, response):
        state_links = response.xpath('//ul/li/div[@class="sfx-text "]/a/@href').extract()
        for link in state_links:
            yield scrapy.Request(url=urljoin(response.url, link), callback=self.parse_by_city)

    def parse_by_city(self, response):
        agent_links = response.xpath('//ul/li/div[@class="sfx-text "]/a/@href').extract()
        for link in agent_links:
            yield scrapy.Request(url=urljoin(response.url, link), callback=self.parse_agent)

    def parse_agent(self, response):
        agent_info = StateFarmItem()
        agent_lists = response.xpath('//div[contains(@class, "agentDetailsAddress")]').extract()
        if len(agent_lists) > 0:
            for agent in agent_lists:
                name = self._clean_text(html.fromstring(agent)
                                        .xpath('//span[contains(@class, "agentListAgentName")]/h4/text()')[0])
                details = html.fromstring(agent)\
                    .xpath('//div[@class="hidden-phone"]//span[contains(@class, "sfx-text")]/text()')
                address = details[0]
                phone_number = details[-1]
                city = response.url.split('/')[-1].capitalize()

                agent_info['Name'] = name
                agent_info['Address'] = address
                agent_info['City'] = city
                agent_info['Phone_number'] = phone_number

                return agent_info

    @staticmethod
    def _clean_text(text):
        text = text.replace("\n", " ").replace("\t", " ").replace("\r", " ")
        text = re.sub("&nbsp;", " ", text).strip()

        return re.sub(r'\s+', ' ', text)
