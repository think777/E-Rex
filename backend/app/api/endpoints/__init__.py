from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.neo4j import DB as db
from app.neo4j.spider import Spider

spidey=Spider()

#Specify what all needs to be included for from . import *
__all__=['db','spidey','BaseModel','APIRouter','HTTPException','Query']