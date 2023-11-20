'''
This module has all similarity functions
'''
from . import *
from app.neo4j.helper import compareStudents, compareEvents, studentEventSim, studentClubSim, eventClubSim

session=db.getSession()

router=APIRouter(prefix='/simFunc',tags=["similarityFuncs"])

#For each similarity function, include immediate and multi-hop neighbours

@router.get('/studentStudent')
async def studentStudent(id1:str=Query(description="ID of student A"),id2:str=Query(description="ID of student B")):
    result=compareStudents(session,id1,id2,False)
    if(result is None):
        # Handle the exception and return a 404 response
        raise HTTPException(status_code=404, detail="Invalid student IDs")
    return result

@router.get('/eventEvent')
async def eventEvent(id1:str=Query(description="ID of event A"),id2:str=Query(descirption="ID of event B")):
    result=compareEvents(session,id1,id2,False)
    if(result is None):
        # Handle the exception and return a 404 response
        raise HTTPException(status_code=404, detail="Invalid event IDs")
    return result

@router.get('/studentEvent')
async def studentEvent(sid:str=Query(description="ID of student"),eid:str=Query(descirption="ID of event")):
    result=studentEventSim(session,sid,eid)
    if(result is None):
        # Handle the exception and return a 404 response
        raise HTTPException(status_code=404, detail="Invalid IDs")
    return result

@router.get('/studentClub')
async def studentClub(sid:str=Query(description="ID of student"),cid:str=Query(descirption="ID of club")):
    result=studentClubSim(session,sid,cid)
    if(result is None):
        # Handle the exception and return a 404 response
        raise HTTPException(status_code=404, detail="Invalid IDs")
    return result

@router.get('/eventClub')
async def eventClub(eid:str=Query(description="ID of event"),cid:str=Query(descirption="ID of club")):
    result=eventClubSim(session,eid,cid)
    if(result is None):
        # Handle the exception and return a 404 response
        raise HTTPException(status_code=404, detail="Invalid IDs")
    return result