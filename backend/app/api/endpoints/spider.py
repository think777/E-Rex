from . import *
from app.neo4j.spider import Spider

router=APIRouter(prefix='/spider',tags=["Spider"])

@router.get('/')
async def spider(id:str=Query(description="ID of student")):
    spider=Spider()
    result=spider.crawl(id)
    if(result is None):
        # Handle the exception and return a 404 response
        raise HTTPException(status_code=404, detail="Invalid student ID")
    return result