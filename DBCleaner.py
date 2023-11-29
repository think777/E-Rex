from neo4j import GraphDatabase
import json
import ast

uri = "bolt://localhost:7687"
username = "neo4j"
password = "testtest"

def clean_up_clubs(session):
    query ="""
    MATCH (s:Student)
    RETURN s.Clubs as Clubs,s.StudentID as sid
    """
    result=session.run(query)
    counter=0
    for record in result:
        clubs_list=ast.literal_eval(record["Clubs"])
        query="""
        MATCH (s:Student {StudentID:$sid})-[:MEMBER_OF]-(x)
        RETURN COLLECT(x.Club) as clubs
        """
        result1=session.run(query,sid=record["sid"]).single()
        if len(result1["clubs"])!=len(clubs_list):
            print(result1["clubs"],record["Clubs"])
            counter+=1
    print(counter)

with GraphDatabase.driver(uri, auth=(username, password)) as driver:
    with driver.session() as session:
        clean_up_clubs(session)

