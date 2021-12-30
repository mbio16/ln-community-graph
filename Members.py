import requests
import json
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_cytoscape as cyto
from dash.dependencies import Input, Output
import plotly.express as px
class Members:
    
    def __init__(self, community_id: str) -> None:
        self.community_id = community_id
        self.GRAPHQUERY = payload="{\"query\":\"{getCommunity(id: \\\"" +self.community_id+ "\\\") {\\ndetails {\\nname\\npubId\\n}\\nmember_count\\nmember_list\\n}\\n}\",\"variables\":{}}"
        self.USER_AGENT = "BTC"
        
        self.community_name:str = None
        self.num_members:int = None
        self.members:list = None
        
        self.capacity = list()
        self.nodes_info = list()
        self.result = list()
        self._get_data()
        
    def _get_data(self) -> None:
        r = requests.post(
            url="https://api.amboss.space/graphql",
            data=self.GRAPHQUERY,
            headers={"Content-Type":"application/json", "Host" : "api.amboss.space", "User-Agent": self.USER_AGENT}
            )
        
        res_data = r.json()
        self.community_name = res_data["data"]["getCommunity"]["details"]["name"]
        self.num_members = res_data["data"]["getCommunity"]["member_count"]
        self.members = res_data["data"]["getCommunity"]["member_list"]
        self._get_channels()
    
    def _get_channels(self)->None:
        for i in self.members:
            query = "{\"query\":\"{\\n  getNode(\\n    pubkey: \\\""+i+"\\\"\\n  ) {\\n    graph_info {\\nnode {\\n        alias\\n        color\\n      }\\n      channels {\\n          total_capacity\\n          list {\\n          block_age\\n          short_channel_id\\n          capacity\\n          node1_pub\\n          node2_pub\\n          }       \\n        }\\n      }\\n   }\\n}\",\"variables\":{}}"
            r = requests.post(
            url="https://api.amboss.space/graphql",
            data=query,
            headers={"Content-Type":"application/json", "Host" : "api.amboss.space", "User-Agent": self.USER_AGENT}
            )
            res = r.json()
            channels= res["data"]["getNode"]["graph_info"]["channels"]["list"]
            self.nodes_info.append(res["data"]["getNode"]["graph_info"]["node"])
            self.capacity.append(int(res["data"]["getNode"]["graph_info"]["channels"]["total_capacity"]))
            self._channels_in_community(channels,i)
            
    def _channels_in_community(self,channels:list,node:str)->None:
        for item in channels:
            if item["node1_pub"] not in self.members:
                continue
            if item["node2_pub"] not in self.members:
                continue
            if(item["node1_pub"] == node) or (item["node2_pub"] == node) and (item["short_channel_id"] not in self.result):
                self.result.append(
                    item
                )
                
                
    def __str__(self) -> str:
        return "name: " + self.community_name + "\nnum_members: " + str(self.num_members) + "\nnodes: " +str(self.members)
    
    def print_nodes_info(self):
        print(json.dumps(self.nodes_info,indent=3))
        
    def print_community_channels(self,save_to_file=False)->None:
        print(json.dumps(self.result,indent=3))
        if(save_to_file):
            with open("./data.json","w") as file:
                file.write(json.dumps(self.result,indent=3))
    def _get_data_for_graph(self,capacity_limit_highlight:int)->list:
        result_list = list()
        for i,node in enumerate(self.members):
            name = self.nodes_info[i]["alias"]
            result_list.append({
                "data":{
                    "id":node,
                    "label":name,
                    },
                "classes":node
                }
            )
        for chan in self.result:
            result_list.append({
                "data":
                    {"source": chan["node1_pub"],
                     "target": chan["node2_pub"]
                     },
                    "classes":  "top" if int(chan["capacity"]) >= capacity_limit_highlight else "not-top"
                    }
                )
        return result_list
              
    def _get_stylesheet(self)->list:
        res = list()
        for i,node in enumerate(self.nodes_info):
            res.append(
                {
                    "selector": "." + self.members[i],
                    "style":{
                        "background-color": node["color"]
                    }
                }
            )
        res.append( {
                "selector": "node",
                "style": {
                    "label": "data(label)",   
                }
            })
        res.append(
                {
                    "selector": ".top",
                    "style":{
                        'background-color': 'red',
                        'line-color': 'red'
                    }
                }
            )
        return res
    


    def create_graph(self,capacity_limit_highlight:int)->None: 
        app = dash.Dash(__name__)
        app.layout = html.Div([
            html.P(self.community_name),
            cyto.Cytoscape(
                id='cytoscape',
                elements=self._get_data_for_graph(capacity_limit_highlight),
                responsive=True,
                style={'width': '100%', 'height': '90vh'},
                stylesheet= self._get_stylesheet(),
                layout={
                    'name': 'cose',
                    'idealEdgeLength': 150,
                    'nodeOverlap': 20,
                    'refresh': 20,
                    'fit': True,
                    'padding': 30,
                    'randomize': False,
                    'componentSpacing': 100,
                    'nodeRepulsion': 400000,
                    'edgeElasticity': 200,
                    'nestingFactor': 5,
                    'gravity': 80,
                    'numIter': 1000,
                    'initialTemp': 200,
                    'coolingFactor': 0.95,
                    'minTemp': 1.0
            },
            )
        ])

        app.run_server(debug=True)