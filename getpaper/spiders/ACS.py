import time
from bs4 import BeautifulSoup
from getpaper.spiders._spider import _Spider
from getpaper.config import HEADER
from typing import Dict
import asyncio

from getpaper.utils import AsyncFunc, getSession


class Spider(_Spider):
    base_url = 'https://pubs.acs.org/action/doSearch'

    def parseData(self, keyword: str,
                  start_year: str,
                  end_year: str,
                  author: str,
                  journal: str,
                  sorting: str) -> Dict:
        data = {"AllField": keyword}
        return data

    @AsyncFunc
    async def getTotalPaperNum(self):
        """
        获取查找文献的总数
        """
        async with getSession() as session:
            html = await self.getHtml(session, self.data)
        bs = BeautifulSoup(html, 'lxml')
        total_num = bs.find("span", attrs = {'class': 'result__count'}).string  # type:ignore
        return total_num.replace(",", "")  # type:ignore

    @AsyncFunc
    async def getAllpapers(self, num: int):
        return super().getAllpapers(num)


if __name__ == '__main__':
    pass