from . import *

router=APIRouter(prefix='/spider',tags=["Spider"])

@router.get('/weave')
async def spiderWeave(restart:bool,nodeId:str=Query(description="ID of node")):
    result=spidey.weave('Student',nodeId,restart)
    if(result is None):
        raise HTTPException(status_code=404, detail="Invalid node ID")
    return result

@router.get('/crawl')
async def spiderCrawl(nodeId:str=Query(description="ID of student")):
    result=spidey.crawl(nodeId)
    if(result is None):
        raise HTTPException(status_code=404, detail="Invalid student ID")
    return result