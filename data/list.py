import pandas as pd
from neo4j import GraphDatabase,exceptions
import csv
import random
#from backend.app.neo4j.helper import create_relationships_with_clubs,create_relationships_with_events

uri = "bolt://localhost:7687"
username = 'neo4j'
password = 'testtest'

driver=GraphDatabase.driver(uri,auth=(username,password))
session=driver.session()

# Load data from CSV files
students_df = pd.read_csv('Events List - Students.csv')
clubs_df = pd.read_csv('Events List - Clubs(2).csv')

# Split the list of clubs in the Clubs column and add specific club keywords to the student's keywords
students_df['Clubs'] = students_df['Clubs'].str.replace('[', '').str.replace(']', '').str.replace("'", '').str.replace('"','')
students_df['Clubs'] = students_df['Clubs'].str.split(',')


students_club_count = 0

# Iterate through each student
for index, student_row in students_df.iterrows():
    student_id = student_row['StudentID']
    student_clubs = student_row['Clubs']

    # Iterate through each club the student is part of
    for club in student_clubs:

        # Find the club in the clubs DataFrame
        club_info = clubs_df[clubs_df['Club'] == club.strip()]
        
        result = session.run(
            "MATCH (s:Student {StudentID: $student_id})"
            "MATCH (c:Club {ClubID: $club_id})"
            "OPTIONAL MATCH (s)-[:MEMBER_OF]->(c)"
            "WHERE c IS NULL"
            "RETURN s.StudentID AS StudentWithoutClub",
            student_id=student_id,
            club_id=club_info['ClubId']
        )
        
        if result:
            print(student_row['Name']+','+student_row['StudentID'])

        students_club_count += len(student_row['Clubs'])

print(students_club_count)

