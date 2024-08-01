First add directories:
```bash
./logging
./temp
```

Run: `python run.py`

Note that modify the `category` of `run_esg_crawler` in `run.py`:

```py
esg = ESGCrawler(category="report") # ESG报告
esg = ESGCrawler(category="event") # ESG争议事件
esg = ESGCrawler(category="penalty") # ESG环保处罚
```

Parsed data will be downloaded at 

```bash
./data/crawler/esg_crawler/report
./data/crawler/esg_crawler/event
./data/crawler/esg_crawler/penalty
```
