###############################################################################
#                            RUN MAIN                                         #
###############################################################################

# setup
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

import names
import pandas as pd
import numpy as np
import base64
import io


'''
Generate random guests list
:parameter
    :param n: num - number of guests and length of dtf
    :param lst_categories: list - ["family", "friends", "university", ...]
    :param n_rules: num - number of restrictions to apply (ex. if 1 then 2 guests can't be sit together)
:return
    dtf with guests
'''
def random_data(n=100, lst_categories=["family","friends","work","university","tennis"], n_rules=0):
    ## basic list
    lst_dics = []
    for i in range(n):
        name = names.get_full_name()
        category = np.random.choice(lst_categories) if len(lst_categories) > 0 else np.nan
        lst_dics.append({"id":i, "name":name, "category":category, "avoid":np.nan})
    dtf = pd.DataFrame(lst_dics)

    ## add rules
    if n_rules > 0:
        for i in range(n_rules):
            choices = dtf[dtf["avoid"].isna()]["id"]
            ids = np.random.choice(choices, size=2)
            dtf["avoid"].iloc[ids[0]] = int(ids[1]) if int(ids[1]) != ids[0] else int(ids[1])+1

    return dtf


'''
When a file is uploaded it contains "contents", "filename", "date"
:parameter
    :param contents: file
    :param filename: str
:return
    pandas table
'''
def upload_file(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            return pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            return pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print("ERROR:", e)
        return 'There was an error processing this file.'


'''
Write excel
:parameter
    :param dtf: pandas table
:return
    link
'''
def download_file(dtf):
    xlsx_io = io.BytesIO()
    writer = pd.ExcelWriter(xlsx_io)
    dtf.to_excel(writer, index=False)
    writer.save()
    xlsx_io.seek(0)
    media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    data = base64.b64encode(xlsx_io.read()).decode("utf-8")
    link = f'data:{media_type};base64,{data}'
    return link 
    

import numpy as np


class Model():

    def __init__(self, dtf, capacity=10, n_iter=10):
        self.n_tables = int(np.ceil( len(dtf)/capacity ))
        self.dic_tables = {i:capacity for i in range(self.n_tables)}
        self.dtf = dtf
        self.n_iter = n_iter


    @staticmethod
    def evaluate(dtf):
        score = 0
        for t in dtf["table"].unique():
            dtf_t = dtf[dtf["table"]==t]

            ## check penalties
            for i in dtf_t[~dtf_t["avoid"].isna()]["avoid"].values:
                if i in dtf_t["id"].values:
                    score -= 1

            ## check rewards
            seats = dtf_t["id"].values
            for n,i in enumerate(seats):
                cat = dtf_t[dtf_t["id"]==i]["category"].iloc[0]

                next_i = seats[n+1] if n < len(seats)-1 else seats[0]
                next_cat = dtf_t[dtf_t["id"]==next_i]["category"].iloc[0]
                if cat == next_cat:
                    score += 1

                prev_i = seats[n-1] if n > 0 else seats[-1]
                prev_cat = dtf_t[dtf_t["id"]==prev_i]["category"].iloc[0]
                if cat == prev_cat:
                    score += 1

        return score


    def run(self):
        best_dtf = self.dtf.copy()
        best_dtf["table"] = np.random.randint(low=1, high=self.n_tables+1, size=len(self.dtf))
        best_score = self.evaluate(best_dtf)

        for i in range(self.n_iter):
            self.dtf["table"] = np.random.randint(low=1, high=self.n_tables+1, size=len(self.dtf))
            score = self.evaluate(self.dtf)
            best_dtf = self.dtf if score > best_score else best_dtf

        return best_dtf

import plotly.express as px
import numpy as np
import pandas as pd


class Plot():

    def __init__(self, dtf):
       self.dtf = self.prepare_data(dtf)


    @staticmethod
    def prepare_data(dtf):
        ## mark the rules
        dtf["avoid"] = dtf["avoid"].apply(lambda x: dtf[dtf["id"]==x]["name"].iloc[0] if pd.notnull(x) else "none")
        dtf["size"] = dtf["avoid"].apply(lambda x: 1 if x == "none" else 3)

        ## create axis
        dtf_out = pd.DataFrame()
        lst_tables = []
        for t in dtf["table"].unique():
            dtf_t = dtf[dtf["table"]==t]
            n = len(dtf_t)
            theta = np.linspace(0, 2*np.pi, n)
            dtf_t["x"] = 1*np.cos(theta)
            dtf_t["y"] = 1*np.sin(theta)
            dtf_out = dtf_out.append(dtf_t)

        return dtf_out.reset_index(drop=True).sort_values("table")


    def print_title(self, max_capacity, filename=None):
        guests = str(int(len(self.dtf)))
        tables = str(int(len(self.dtf["table"].unique())))
        process = "Random Simulation" if filename is None else "Data from "+filename
        max_capacity = str(int(max_capacity))
        return process+" : "+guests+" guests --> "+tables+ " tables calculated with max "+max_capacity+" people per table"


    def plot(self):
        fig = px.scatter(self.dtf, x="x", y="y", color="category", hover_name="name", facet_col="table", facet_col_wrap=3,
                         hover_data={"x":False, "y":False, "category":True, "avoid":True, "size":False, "table":False},
                         size="size")

        fig.add_shape(type="circle", opacity=0.1, fillcolor="black", col="all", row="all", exclude_empty_subplots=True,
                      x0=self.dtf["x"].min(), y0=self.dtf["y"].min(), x1=self.dtf["x"].max(), y1=self.dtf["y"].max())

        fig.update_layout(plot_bgcolor='white', legend={"bordercolor":"black", "borderwidth":1, "orientation":"h"})
        fig.update_yaxes(visible=False)
        fig.update_xaxes(visible=False)
        return fig

import os

#ENV = "DEV"
ENV = "PROD"


## server
host = "0.0.0.0"
port = int(os.environ.get("PORT", 5000))


## info
app_name = "Wedding Planner"
contacts = "https://www.linkedin.com/in/mauro-di-pietro-56a1366b/"
code = "https://github.com/mdipietro09/App_Wedding"
tutorial = "https://towardsdatascience.com/web-development-with-python-dash-complete-tutorial-6716186e09b3"
fontawesome = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"

about = "Load your guest list or try random simulation"

## fs
#root = os.path.dirname(os.path.dirname(__file__)) + "/"

# App Instance
app = dash.Dash(name=app_name, assets_folder="static", external_stylesheets=[dbc.themes.LUX, fontawesome])
app.title = app_name



########################## Navbar ##########################
# Input
## none


# Output
navbar = dbc.Nav(className="nav nav-pills", children=[
    ## logo/home
    dbc.NavItem(html.Img(src=app.get_asset_url("logo.PNG"), height="40px")),
    ## about
    dbc.NavItem(html.Div([
        dbc.NavLink("About", href="/", id="about-popover", active=False),
        dbc.Popover(id="about", is_open=False, target="about-popover", children=[
            dbc.PopoverHeader("How it works"), dbc.PopoverBody(about)
        ])
    ])),
    ## links
    dbc.DropdownMenu(label="Links", nav=True, children=[
        dbc.DropdownMenuItem([html.I(className="fa fa-linkedin"), "  Contacts"], href=contacts, target="_blank"), 
        dbc.DropdownMenuItem([html.I(className="fa fa-github"), "  Code"], href=code, target="_blank")
    ])
])


# Callbacks
@app.callback(output=[Output(component_id="about", component_property="is_open"), 
                      Output(component_id="about-popover", component_property="active")], 
              inputs=[Input(component_id="about-popover", component_property="n_clicks")], 
              state=[State("about","is_open"), State("about-popover","active")])
def about_popover(n, is_open, active):
    if n:
        return not is_open, active
    return is_open, active



########################## Body ##########################
# Input
inputs = dbc.FormGroup([
    ## hide these 2 inputs if file is uploaded
    html.Div(id='hide-seek', children=[

        dbc.Label("Number of Guests", html_for="n-guests"), 
        dcc.Slider(id="n-guests", min=10, max=100, step=1, value=50, tooltip={'always_visible':False}),

        dbc.Label("Number of Rules", html_for="n-rules"), 
        dcc.Slider(id="n-rules", min=0, max=10, step=1, value=3, tooltip={'always_visible':False})

    ], style={'display':'block'}),

    ## always visible
    dbc.Label("Number of Trials", html_for="n-iter"), 
    dcc.Slider(id="n-iter", min=10, max=1000, step=None, marks={10:"10", 100:"100", 500:"500", 1000:"1000"}, value=0),

    html.Br(),
    dbc.Label("Max Guests per Table", html_for="max-capacity"), 
    dbc.Input(id="max-capacity", placeholder="table capacity", type="number", value="10"),

    ## upload a file
    html.Br(),
    dbc.Label("Or Upload your Excel", html_for="upload-excel"), 
    dcc.Upload(id='upload-excel', children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
               style={'width':'100%', 'height':'60px', 'lineHeight':'60px', 'borderWidth':'1px', 'borderStyle':'dashed',
                      'borderRadius':'5px', 'textAlign':'center', 'margin':'10px'} ),
    html.Div(id='excel-name', style={"marginLeft":"20px"}),

    ## run button
    html.Br(),html.Br(),
    dbc.Col(dbc.Button("run", id="run", color="primary"))
])


# Output
body = dbc.Row([
        ## input
        dbc.Col(md=3, children=[
            inputs, 
            html.Br(),html.Br(),html.Br(),
        ]),
        ## output
        dbc.Col(md=9, children=[
            dbc.Spinner([
                ### title
                html.H6(id="title"),
                ### download
                dbc.Badge(html.A('Download', id='download-excel', download="tables.xlsx", href="", target="_blank"), color="success", pill=True),
                ### plot
                dcc.Graph(id="plot")
            ], color="primary", type="grow"), 
        ])
])


# Callbacks
@app.callback(output=[Output(component_id="hide-seek", component_property="style"),
                      Output(component_id="excel-name", component_property="children")], 
              inputs=[Input(component_id="upload-excel", component_property="filename")])
def upload_event(filename):
    div = "" if filename is None else "Use file "+filename
    return {'display':'block'} if filename is None else {'display':'none'}, div


@app.callback(output=[Output(component_id="title", component_property="children"),
                      Output(component_id="plot", component_property="figure"),
                      Output(component_id='download-excel', component_property='href')],
              inputs=[Input(component_id="run", component_property="n_clicks")],
              state=[State("n-guests","value"), State("n-iter","value"), State("max-capacity","value"), State("n-rules","value"), 
                     State("upload-excel","contents"), State("upload-excel","filename")])
def results(n_clicks, n_guests, n_iter, max_capacity, n_rules, contents, filename):
    if contents is not None:
        dtf = upload_file(contents, filename)
    else:
        dtf = random_data(n=n_guests, n_rules=n_rules)
    dtf = Model(dtf, float(max_capacity), int(n_iter)).run()
    out = Plot(dtf)
    return out.print_title(max_capacity, filename), out.plot(), download_file(dtf.drop("size", axis=1))



########################## App Layout ##########################
app.layout = dbc.Container(fluid=True, children=[
    html.H1(app_name, id="nav-pills"),
    navbar,
    html.Br(),html.Br(),html.Br(),
    body
])



########################## Run ##########################
if __name__ == "__main__":
    debug = True if ENV == "DEV" else False
    app.run_server(debug=debug, host=host, port=port)