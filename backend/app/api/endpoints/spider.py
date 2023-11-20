from . import *
from app.neo4j.spider import Spider

router=APIRouter(prefix='/spider',tags=["Spider"])

spider=Spider()

@router.get('/weave')
async def spiderWeave(id:str=Query(description="ID of student")):
    spider.construct()  #FIXME Remove later
    result=spider.weave('Student',id)
    if(result is None):
        raise HTTPException(status_code=404, detail="Invalid student ID")
    return result

@router.get('/crawl')
async def spiderCrawl(id:str=Query(description="ID of student")):
    print(id)
    result=spider.crawl(id)
    if(result is None):
        raise HTTPException(status_code=404, detail="Invalid student ID")
    return result