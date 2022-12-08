from dash import Dash, dcc, Output, Input, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
import pandas as pd
from datetime import date
from datetime import timedelta

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

## Database management
DBNAME = 't_h_readings.db'

def get_data(sm_range, date_range=[]):
    con  = sqlite3.connect(DBNAME,
                          detect_types=sqlite3.PARSE_DECLTYPES |
                            sqlite3.PARSE_COLNAMES)

    cur = con.cursor()

    params = [sm_range for i in range(4)]
    query = '''SELECT
                    timestamp as "timestamp [timestamp]",
                    temperature,
                    avg(temperature) OVER
                        (ORDER BY timestamp ROWS BETWEEN ? PRECEDING AND ? FOLLOWING)
                        as wtemperature,
                    humidity,
                    avg(humidity) OVER
                        (ORDER BY timestamp ROWS BETWEEN ? PRECEDING AND ? FOLLOWING)
                        as whumidity
                    FROM reading'''
    if len(date_range) == 2:
        query += '''\nWHERE timestamp BETWEEN ? AND ?'''
        params.append(date_range[0])
        params.append(date_range[1])
    
    query += '\nORDER BY timestamp;'
    # print(query)
    # print(*date_range)
    print(params)
    df = pd.read_sql_query(query, con, params=params)
    return df

def get_last_update():
    con  = sqlite3.connect(DBNAME,
                          detect_types=sqlite3.PARSE_DECLTYPES |
                            sqlite3.PARSE_COLNAMES)

    cur = con.cursor()

    query = '''SELECT MAX(timestamp) as max_timestamp FROM reading;'''
    df = pd.read_sql_query(query, con)
    return df.max_timestamp[0]

get_last_update()
def get_statistics(l1=None, l2=None, fields=['temperature', 'humidity']):
    con  = sqlite3.connect(DBNAME,
                          detect_types=sqlite3.PARSE_DECLTYPES |
                            sqlite3.PARSE_COLNAMES)

    cur = con.cursor()

    query = '''SELECT\n'''
    stat = ['avg', 'max', 'min']
    for f in fields:
        for s in stat:
            query += f'''round({s}({f}),1) as {s}_{f}'''
            if stat.index(s) != len(stat) - 1:
                query += ',\n'
        if fields.index(f) != len(fields) - 1:
            query += ',\n'
    
    query += '''\nFROM reading'''
    params = []
    if (l1 is not None and l2 is not None):
        query += '\nWHERE (timestamp BETWEEN ? AND ?);' 
        params = [l1, l2]
    else:
        query += ';'
    df = pd.read_sql_query(query, con, params=params)
    #print(query)
    return df


## Create table
def create_stats_table(graph_range):
    df = get_statistics(*graph_range)

    tab = go.Figure(
        data=[
            go.Table(
                columnwidth=[80, 80],
                header=dict(values=['', '<b>Temperature</b>', '<b>Humidity</b>'],
        #                    fill_color='paleturquoise',
                            align='center'),
                cells=dict(values=[['<b>Average</b>', '<b>Maximum</b>', '<b>Mimimum</b>', ],
                                [df.avg_temperature, df.max_temperature, df.min_temperature],
                                [df.avg_humidity, df.max_humidity,  df.min_humidity]],
                                #                   fill_color='lavender',
                        align='center')
            )
        ],
        layout = dict(
            margin=dict(l=20, r=20, t=20, b=20)
        )
    )
    return tab

#################################
# Create figure with secondary y-axis

mygraph1 = dcc.Graph(
        figure={},
        config={
            "displaylogo": False,
            'modeBarButtonsToRemove': ['pan2d', 'zoomin', 'zoomout']
        })

fig1 = make_subplots(specs=[[{"secondary_y": True}]])
# Add traces
df = get_data(10)
fig1.add_trace(
        go.Scatter(x=df.timestamp, y=df.wtemperature, name="Temperature", line=dict(color='firebrick')),
    secondary_y=False,
)

fig1.add_trace(
        go.Scatter(x=df.timestamp, y=df.whumidity, name="Humidity", line=dict(color='royalblue')),
    secondary_y=True,
)

# Set y-axes titles
fig1.update_yaxes(title_text="<b>Temperature</b> (°C)", secondary_y=False)
fig1.update_yaxes(title_text="<b>Humidity</b> (%)", secondary_y=True)
fig1.update_layout(
        uirevision=True,
        xaxis=dict(
            rangeslider=dict(
                visible=False
            ),
            type="date"
        ),
        margin=dict(l=20, r=20, t=20, b=20)
    )
mygraph1.figure = fig1
#################################

df = get_statistics()

## Page elements

tab = go.Figure()
tab_graph = dcc.Graph(figure=tab,
    style={
        'margin': '0',
        'padding':'0',
        'height': '12em',
        # 'width' : '50%'
    }
)
slid = dcc.Slider(0, 100, value=10, marks=None, vertical=True,
    tooltip={"placement": "right", "always_visible": False})
header = html.Div(
    dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    slid
                ], width=1),
                dbc.Col([
                    mygraph1
                ], width=11)
            ]),
            dbc.Row([
                dbc.Col([
                    tab_graph
                ], width=4),
                dbc.Col([
                    dbc.CardBody([
                        html.H3('Last Update'),
                        html.P(get_last_update(), id='last_update_p')
                    ])
                ], width=3)
            ])
        ]),
    style={
        # 'background-color': 'rgba(0,0,122,0.2)',
    }

    )
)

interval = dcc.Interval(
    interval=60*1000,
    n_intervals=0
)

app.layout = dbc.Container([header, interval])
## Misc


## Callbacks

@app.callback(
        Output(tab_graph, component_property='figure'),
        [Input(mygraph1, component_property='relayoutData'),
        Input(interval, component_property='n_intervals')]
)
def update_table(rlData, n_intervals):
    graph_range = []
    try:
        graph_range = rlData['xaxis.range']
    except (KeyError, TypeError):
        graph_range = []

    tab = create_stats_table(graph_range)
    return tab


@app.callback(
        Output(mygraph1, component_property='figure'),
        [Input(slid, component_property='value'),
        Input(interval, component_property='n_intervals')]
)
def update_smoothing (val, n_intervals):
    today = date.today()
    # Yesterday date
    yesterday = today - timedelta(days = 1)
    tomorrow = today + timedelta(days = 1)
    today = today.strftime('%Y-%m-%d %H:%M:%S.%f')
    yesterday = yesterday.strftime('%Y-%m-%d %H:%M:%S.%f')
    tomorrow = tomorrow.strftime('%Y-%m-%d %H:%M:%S.%f')
    print(today)
    print(yesterday)
    print()
    df = get_data(val, [yesterday, tomorrow])
    fig1.update_traces(x=df.timestamp, y=df.whumidity, selector=dict(name="Humidity"))
    fig1.update_traces(x=df.timestamp, y=df.wtemperature, selector=dict(name="Temperature"))
    return fig1

@app.callback(
        Output('last_update_p', component_property='children'),
        Input(interval, component_property='n_intervals')
)
def periodic_update(n_intervals):
    #Plotly.relayoutData(mygraph1, {'xaxis.range[1]':None})
    # mygraph1.layout = go.Layout(xaxis_range=[None, '2022-11-28 18:28:07.434392'])
    return get_last_update()



if __name__ == '__main__':
    app.run(
        host='192.168.178.58',
        port=8080,
        debug=True,
        dev_tools_hot_reload=True
    )
