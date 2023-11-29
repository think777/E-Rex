import networkx as nx
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from networkx.exception import PowerIterationFailedConvergence

from . import DB

import warnings

warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn.utils.validation")

session=DB.getSession()

nodeQueue=[]

neo4j_queries = {
    "find_influencers" : "MATCH (s:Student) OPTIONAL MATCH (s)-[:DIRECT]->(e:Event) OPTIONAL MATCH (s)-[:MEMBER_OF]->(c:Club) WITH s, COUNT(DISTINCT e) AS eventsAttended, COUNT(DISTINCT c) AS clubsJoined RETURN s.StudentId, eventsAttended+clubsJoined as influencerScore ORDER BY influencerScore DESC;",
    "louvainq1": "CALL gds.graph.project('myGraphLouvian', '*', '*');",
    "louvainq2" : "CALL gds.louvain.stream('myGraphLouvian') YIELD nodeId, communityId RETURN DISTINCT communityId, count(communityId) AS number_of_members ORDER BY number_of_members DESC;",
    "community_member_mapper" : "CALL gds.louvain.stream('myGraphLouvian') YIELD nodeId, communityId WITH communityId, COLLECT(DISTINCT nodeId) AS nodeIdsInCommunity RETURN communityId, nodeIdsInCommunity;",
    "louvainq3" : "CALL gds.graph.exists('myGraphLouvian');",
    "all_nodes_in_community" : "CALL gds.louvain.stream('myGraphLouvian') YIELD nodeId, communityId WITH communityId, gds.util.asNode(nodeId) AS node1 RETURN communityId, labels(node1) AS labels, node1 ",
    "edges_query" : " CALL gds.louvain.stream('myGraphLouvian') YIELD nodeId, communityId WITH communityId, gds.util.asNode(nodeId) AS node WITH communityId, collect(node) AS nodes UNWIND nodes AS node1 UNWIND nodes AS node2 MATCH (node1)-[edge]->(node2) RETURN communityId, type(edge) AS relationship, node1, node2  ORDER BY communityId ASC;",
    "all_students" : "MATCH(s:Student) RETURN COLLECT(s.StudentId) as stud_list",
    "all_clubs" : "MATCH(s:Club) RETURN COLLECT(s.ClubId) as club_list",
    "all_events" : "MATCH(s:Event) RETURN COLLECT(s.EventId) as event_list"}

def create_neural_network(input_dim):
    model = Sequential()
    model.add(Dense(64, input_dim=input_dim, activation='relu'))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(1, activation='linear')) 
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

def Reverse(tuples):
    new_tup = tuples[::-1]
    return new_tup

def fetchNode(session, id, type1):
    query1 = f"""MATCH (x:Student {{StudentId: $studentId}}) RETURN x"""
    query2 = f"""MATCH (x:Event {{EventId: $eventId}}) RETURN x"""
    query3 = f"""MATCH (x:Club {{ClubId: $clubId}}) RETURN x"""
    if type1== "Student":
        result = session.run(query1,studentId=id).single()
        return result
    if type1== "Event":
        result = session.run(query2,eventId=id).single()
        return result
    if type1== "Club":
        result = session.run(query3,clubId=id).single()
        return result

def fetchNeighbourhood(x):
    neighbourQueue={"Student":[],"Club":[],"Event":[]}
    query1=f"""MATCH (s:Student {{StudentId: $id}})-[r]-(neighbour) WHERE type(r) <> 'SILK_ROAD' SET r.visited=1 RETURN DISTINCT(neighbour) as neighbour """
    query2=f"""MATCH (s:Event {{EventId: $id}})-[r]-(neighbour) WHERE type(r) <> 'SILK_ROAD' SET r.visited=1 RETURN DISTINCT(neighbour) as neighbour """
    query3=f"""MATCH (s:Club {{ClubId: $id}})-[r]-(neighbour) WHERE type(r) <> 'SILK_ROAD' SET r.visited=1 RETURN DISTINCT(neighbour) as neighbour """
    result = ""
    if "StudentId" in x:
        result = session.run(query1, id=x["StudentId"])
    elif "EventId" in x:
        result = session.run(query2, id=x["EventId"])
    elif "ClubId" in x:
        result = session.run(query3, id=x["ClubId"])
    for record in result:
        nodeQueue.append(record)
        label,=record["neighbour"].labels
        neighbourQueue[label].append(record["neighbour"])
    return neighbourQueue

def influencer_community_map(communityId1, nodesInCommunity):
    influencer_finder = session.run(query_gen1(nodesInCommunity))
    influencer_finder = list(influencer_finder)
    mapper = []
    if(len(influencer_finder) != 0):
        max_activity = influencer_finder[0]["activity"]
        all_influencers =[]
        for k1 in influencer_finder:
            if(k1["activity"] == max_activity):
                all_influencers.append(k1["id"])
            else:
                break
        mapper.append({communityId1: all_influencers})
    else:
        mapper.append({communityId1:[]})
    return mapper[0]
        
def query_gen1(list1):
    formatted_string = f"WITH {list(map(lambda t: str(t), list1))} AS nodeIds MATCH (s: Student) WHERE s.StudentId IN nodeIds OPTIONAL MATCH (s)-[:DIRECT]->(e:Event) OPTIONAL MATCH (s)-[:MEMBER_OF]->(c:Club) WITH s, COUNT(DISTINCT e) AS eventsAttended, COUNT(DISTINCT c) AS clubsJoined RETURN s.StudentId AS id,eventsAttended+clubsJoined AS activity ORDER BY activity DESC ;"
    return formatted_string

def all_edges_per_community():
    edges_community = {}
    edges_per_community = session.run(neo4j_queries["edges_query"])
    for edge in edges_per_community:
        if edge["communityId"] not in edges_community:
            edges_community[edge["communityId"]] = []
        if edge["relationship"] == "HOSTED_BY":
            edges_community[edge["communityId"]].append([edge["node1"]["EventId"], edge["relationship"], edge["node2"]["ClubId"]])
        elif edge["relationship"] == "DIRECT":
            edges_community[edge["communityId"]].append([edge["node1"]["StudentId"], edge["relationship"], edge["node2"]["EventId"]])
        elif edge["relationship"] == "MEMBER_OF":
            edges_community[edge["communityId"]].append([edge["node1"]["StudentId"], edge["relationship"], edge["node2"]["ClubId"]])
    return edges_community

def community_node_mapper():
    nodes_in_community = session.run(neo4j_queries["all_nodes_in_community"])
    community_node_mapping_temp = {}
    for record in nodes_in_community:
        community_id = record["communityId"]
        labels_list = list(record["labels"])
        if(labels_list[0] == "Student"):
            node_properties = record["node1"]["StudentId"]
        elif(labels_list[0] == "Club"):
            node_properties = record["node1"]["ClubId"]
        elif(labels_list[0] == "Event"):
            node_properties = record["node1"]["EventId"]
        if community_id in community_node_mapping_temp:
            community_node_mapping_temp[community_id][0].append(labels_list[0])
            community_node_mapping_temp[community_id][1].append({labels_list[0]:node_properties})
        else:
            community_node_mapping_temp[community_id] = [[labels_list[0]], [{labels_list[0]:node_properties}]]
    community_node_mapping = {}
    for id in community_node_mapping_temp:
        club_count = community_node_mapping_temp[id][0].count("Club")
        event_count = community_node_mapping_temp[id][0].count("Event")
        student_count = community_node_mapping_temp[id][0].count("Student")
        organized_data = {"Club": [], "Student": [], "Event": []}
        for item in community_node_mapping_temp[id][1]:
            item_type, item_name = next(iter(item.items()))
            organized_data[item_type].append(item_name)
        community_node_mapping[id]= {"Clubs":club_count, "Events": event_count, "Student": student_count, "Distribution": organized_data}
    return community_node_mapping

def generate_adj_mat(map, communityId, edges):
    adjacency_clubs = map[communityId]["Distribution"]["Club"]
    adjacency_students = map[communityId]["Distribution"]["Student"]
    adjacency_events = map[communityId]["Distribution"]["Event"]
    all_nodes_adjacency = adjacency_clubs + adjacency_students + adjacency_events
    adjacency_matrix = [[0] * len(all_nodes_adjacency) for _ in range(len(all_nodes_adjacency))]
    for a11 in range(len(adjacency_matrix)):
        for a12 in range(len(adjacency_matrix)):
            if([all_nodes_adjacency[a11],"MEMBER_OF",all_nodes_adjacency[a12] ]in edges[communityId] or [all_nodes_adjacency[a12], "MEMBER_OF",all_nodes_adjacency[a11] ]in edges[communityId]):
                adjacency_matrix[a11][a12] = 1
                adjacency_matrix[a12][a11] = 1
            elif([all_nodes_adjacency[a11],"HOSTED_BY",all_nodes_adjacency[a12] ]in edges[communityId] or [all_nodes_adjacency[a12], "HOSTED_BY",all_nodes_adjacency[a11] ]in edges[communityId]):
                adjacency_matrix[a11][a12] = 2
                adjacency_matrix[a12][a11] = 2
            elif([all_nodes_adjacency[a11],"DIRECT",all_nodes_adjacency[a12] ]in edges[communityId] or [all_nodes_adjacency[a12], "DIRECT",all_nodes_adjacency[a11] ]in edges[communityId]):
                adjacency_matrix[a11][a12] = 3
                adjacency_matrix[a12][a11] = 3
            else:
                pass
    return [adjacency_matrix, all_nodes_adjacency]

def extract_features(df, G, node_ids, communityId):
    features = pd.DataFrame()
    label_encoder = LabelEncoder()
    influencers = influencer_community_map(communityId,node_ids)
    hub_scores_source, authority_scores_source = nx.hits(G)
    hub_scores_target, authority_scores_target = nx.hits(G)
    df['source_encoded'] = label_encoder.fit_transform(df['source'])
    df['target_encoded'] = label_encoder.transform(df['target'])
    features['source_degree'] = df['source_encoded'].map(dict(G.degree()))
    features['target_degree'] = df['target_encoded'].map(dict(G.degree()))
    features['preferential_attachment'] = [i[2] for i in nx.preferential_attachment(G, zip(df['source'], df['target']))]
    try:
        features['katz_centrality_source'] = [nx.katz_centrality(G, alpha=0.1)[source] for source in df['source']]
        features['katz_centrality_target'] = [nx.katz_centrality(G, alpha=0.1)[target] for target in df['target']]
    except PowerIterationFailedConvergence:
        features['katz_centrality_source'] = 0
        features['katz_centrality_target'] = 0
    features['eigenvector_centrality_source'] = [nx.eigenvector_centrality(G, max_iter=3000)[source] for source in df['source']]
    features['eigenvector_centrality_target'] = [nx.eigenvector_centrality(G, max_iter=3000)[target] for target in df['target']]
    features['pagerank_source'] = [nx.pagerank(G)[source] for source in df['source']]
    features['pagerank_target'] = [nx.pagerank(G)[target] for target in df['target']]
    features['hub_score_source'] = [hub_scores_source[source] for source in df['source']]
    features['hub_score_target'] = [hub_scores_target[target] for target in df['target']]
    features['authority_score_source'] = [authority_scores_source[source] for source in df['source']]
    features['authority_score_target'] = [authority_scores_target[target] for target in df['target']]
    features['influencer_score'] = [10 if str(node_ids[node]) in list(influencers.values())[0] else 0 for node in df['source']]
    features['influencer_score'] += [10 if str(node_ids[node]) in list(influencers.values())[0] else 0 for node in df['target']]
    return features

def create_neural_network(input_dim):
    model = Sequential()
    model.add(Dense(64, input_dim=input_dim, activation='relu'))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(1, activation='linear')) 
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

def query_gen2(source_node_id,target_node_id,predicted_weight):
    query1 = (
    f"MATCH (source:Student {{StudentId: '{source_node_id}'}}), "
    f"(target:Club {{ClubId: '{target_node_id}'}}) "
    "MERGE (source)-[r:MEMBER_OF]->(target) "
    f"SET r.weight = {predicted_weight}"
    ) 
    query2 = (
    f"MATCH (source:Student {{StudentId: '{source_node_id}'}}), "
    f"(target:Event {{EventId: '{target_node_id}'}}) "
    "MERGE (source)-[r:DIRECT]->(target) "
    f"SET r.weight = {predicted_weight}"
    ) 
    query3 = (
    f"MATCH (source:Event {{EventId: '{source_node_id}'}}), "
    f"(target:Club {{ClubId: '{target_node_id}'}}) "
    "MERGE (source)-[r:HOSTED_BY]->(target) "
    f"SET r.weight = {predicted_weight}"
    )  
    all_students = session.run(neo4j_queries["all_students"]).single()
    all_clubs = session.run(neo4j_queries["all_clubs"]).single() 
    all_events = session.run(neo4j_queries["all_events"]).single()
    if((source_node_id in all_students["stud_list"] and target_node_id in all_clubs["club_list"]) or (target_node_id in all_students["stud_list"] and source_node_id in all_clubs["club_list"])):
        session.run(query1)
    elif((source_node_id in all_students["stud_list"] and target_node_id in all_events["event_list"]) or (target_node_id in all_students["stud_list"] and source_node_id in all_events["event_list"])):
        session.run(query2)
    elif((source_node_id in all_clubs["club_list"] and target_node_id in all_events["event_list"]) or (target_node_id in all_clubs["club_list"] and source_node_id in all_events["event_list"])):
        session.run(query3)
    else:
        print("Invalid")
    
def generate_weights(adj_matrix, communityId):
    adjacency_matrix = np.array(adj_matrix[0])
    node_ids = adj_matrix[1]
    G = nx.from_numpy_array(adjacency_matrix)
    all_edges = []  
    edges = list(G.edges())
    for x in edges:
        all_edges.append(x)
        all_edges.append(Reverse(x))
    df = pd.DataFrame(all_edges, columns=['source', 'target'])
    features1 = extract_features(df, G, node_ids, communityId)
    df_concat = pd.concat([df, features1], axis=1)
    df_concat = df_concat.drop(index=[n for n in range(len(df_concat)) if n % 2 != 0])
    df_concat['label'] = [i for i in range(len(df_concat))]
    labels = df_concat['label']
    features = df_concat.drop(columns=['source', 'target', 'label'])
    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)
    model = create_neural_network(input_dim=X_train.shape[1])
    model.fit(X_train, y_train, epochs=100, batch_size=8, verbose=1)
    y_pred = model.predict(features).flatten()
    df_concat['predicted_weights'] = y_pred
    for index, row in df_concat.iterrows():
        query_gen2(node_ids[int(row['source'])],node_ids[int(row['target'])],row['predicted_weights'])
    y_pred = model.predict(X_test).flatten()
    mse = mean_squared_error(y_test, y_pred)
    print(f'Mean Squared Error: {mse}')

def edgeWeightGen(session, studentId):
    query = f"""MATCH (x:Student {{StudentId: $studentId}}) RETURN x"""
    result = session.run(query,studentId=studentId).single()
    graphExists = session.run(neo4j_queries["louvainq3"]).single()
    if(graphExists["exists"]):
        all_communities = session.run(neo4j_queries["louvainq2"])
        community_member_mapping = session.run(neo4j_queries["community_member_mapper"])
        community_member_mapping_list = list(community_member_mapping)
    else:
        subq = session.run(neo4j_queries["louvainq1"])
        all_communities = session.run(neo4j_queries["louvainq2"])
        community_member_mapping = session.run(neo4j_queries["community_member_mapper"])
        community_member_mapping_list = list(community_member_mapping)
    
    map = community_node_mapper()
    edges = all_edges_per_community()
    for record1 in community_member_mapping_list:
        community_id = record1["communityId"]
        nodesInCommunity = record1["nodeIdsInCommunity"]
        if(community_id != 1078):
                adj_matrix = generate_adj_mat(map, community_id, edges)
                generate_weights(adj_matrix,community_id)
        else:
            print(f"No matching community found for communityId: {community_id}")

    return result

def find_edge_weight(session, source_node_id, target_node_id):
    query1 = (f"MATCH (source:Student {{StudentId: '{source_node_id}'}})-[r:MEMBER_OF]-(target:Club {{ClubId: '{target_node_id}'}}) return r.weight as edge_weight") 
    query2 = (f"MATCH (source:Student {{StudentId: '{source_node_id}'}})-[r:DIRECT]-(target:Event {{EventId: '{target_node_id}'}}) return r.weight as edge_weight") 
    query3 = (f"MATCH (source:Event {{EventId: '{source_node_id}'}})-[r:HOSTED_BY]-(target:Club {{ClubId: '{target_node_id}'}}) return r.weight as edge_weight") 
    all_students = session.run(neo4j_queries["all_students"]).single()
    all_clubs = session.run(neo4j_queries["all_clubs"]).single() 
    all_events = session.run(neo4j_queries["all_events"]).single()

    if((source_node_id in all_students["stud_list"] and target_node_id in all_clubs["club_list"]) or (target_node_id in all_students["stud_list"] and source_node_id in all_clubs["club_list"])):
        rec = session.run(query1).single()
        return 1 if rec is None else rec["edge_weight"]
    elif((source_node_id in all_students["stud_list"] and target_node_id in all_events["event_list"]) or (target_node_id in all_students["stud_list"] and source_node_id in all_events["event_list"])):
        rec = session.run(query2).single()
        return 1 if rec is None else rec["edge_weight"]
    elif((source_node_id in all_clubs["club_list"] and target_node_id in all_events["event_list"]) or (target_node_id in all_clubs["club_list"] and source_node_id in all_events["event_list"])):
        rec = session.run(query3).single()
        return 1 if rec is None else rec["edge_weight"]
    else:
        return -1


#to get edge weight given source node id and target node id, run the following:
# x = find_edge_weight(session, "61", "1")
# print(x)

#to start edge generation algo, run the following:
# edgeWeightGen(session, "278")
