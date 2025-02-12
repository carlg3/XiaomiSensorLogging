import sqlite3
import pandas as pd

from dash import Dash, dcc, Output, Input, html
import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

## Database management
DBNAME_1 = 'temp_1.db'
DBNAME_2 = 'temp_2.db'

def get_battery(DBNAME):
	con = sqlite3.connect(DBNAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
	query = '''select battery_percent from reading order by timestamp desc limit 1;'''
	df = pd.read_sql_query(query, con)
	return df.battery_percent

def get_data(DBNAME, sm_range):
    con  = sqlite3.connect(DBNAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cur = con.cursor()
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
                FROM reading
                WHERE timestamp >= DATE('now')
                ORDER BY timestamp;'''
    df = pd.read_sql_query(query, con, params=[sm_range, sm_range, sm_range, sm_range])
    return df

def get_last_update(DBNAME):
    con  = sqlite3.connect(DBNAME,
                          detect_types=sqlite3.PARSE_DECLTYPES |
                            sqlite3.PARSE_COLNAMES)

    cur = con.cursor()

    query = '''SELECT MAX(timestamp) as max_timestamp FROM reading;'''
    df = pd.read_sql_query(query, con)
    return df.max_timestamp[0]

'''
    def get_statistics(DBNAME, l1=None, l2=None, fields=['temperature', 'humidity']):
        con  = sqlite3.connect(DBNAME,
                            detect_types=sqlite3.PARSE_DECLTYPES |
                                sqlite3.PARSE_COLNAMES)

        cur = con.cursor()

        query = '' 'SELECT\n'' '
        stat = ['avg', 'max', 'min']
        for f in fields:
            for s in stat:
                query += f'' 'round({s}({f}),1) as {s}_{f}'' '
                if stat.index(s) != len(stat) - 1:
                    query += ',\n'
            if fields.index(f) != len(fields) - 1:
                query += ',\n'
        
        query += '' '\nFROM reading' ''
        params = []
        if (l1 is not None and l2 is not None):
            query += '\nWHERE (timestamp BETWEEN ? AND ?);' 
            params = [l1, l2]
        else:
            query += ';'
        df = pd.read_sql_query(query, con, params=params)
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
''' 

def create_info_table():
    carlg_stats = [get_last_update(DBNAME_1), get_battery(DBNAME_1)]
    marti_stats = [get_last_update(DBNAME_2), get_battery(DBNAME_2)]
    
    tab = go.Figure(
        data=[
            go.Table(
                columnwidth=[80, 80],
                header=dict(values=['', '<b>LastUpdate</b>', '<b>Battery%</b>'],
        #                    fill_color='paleturquoise',
                            align='center'),
                cells=dict(values=[
                                ['<b>carlg</b>', '<b>marti</b>'],
                                [carlg_stats[0], marti_stats[0]],
                                [carlg_stats[1], marti_stats[1]]
                                ],
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
df_1 = get_data(DBNAME_1, 25)
df_2 = get_data(DBNAME_2, 25)

# CARLG thermometer
fig1.add_trace(
    go.Scatter(x=df_1.timestamp, y=df_1.wtemperature, name="T_carlg", line=dict(color='firebrick')),
    secondary_y=True,)
fig1.add_trace(
    go.Scatter(x=df_1.timestamp, y=df_1.whumidity, name="H_carlg", line=dict(color='royalblue')),
    secondary_y=False,)

# marti thermometer
fig1.add_trace(
    go.Scatter(x=df_2.timestamp, y=df_2.wtemperature, name="T_marti", line=dict(color='darkgreen')),
    secondary_y=True,)
fig1.add_trace(
    go.Scatter(x=df_2.timestamp, y=df_2.whumidity, name="H_marti", line=dict(color='dodgerblue')),
    secondary_y=False,)

# Set y-axes titles
fig1.update_yaxes(title_text="<b>Temperature</b> (°C)", secondary_y=True)
fig1.update_yaxes(title_text="<b>Humidity</b> (%)", secondary_y=False)
fig1.update_layout(
        uirevision=True,
        xaxis=dict(
            rangeslider=dict(
                visible=True
            ),
            type="date"
        ),
        margin=dict(l=20, r=20, t=20, b=20)
    )

mygraph1.figure = fig1
#################################

# df = get_statistics()

## Page elements
tab = go.Figure()
tab_graph = dcc.Graph(figure=tab,
    style={
        'margin': '0',
        'padding':'0',
        'height': '12em',
    }
)

'''
slid = dcc.Slider(
    0, 100, value=10, marks=None, vertical=True,
    tooltip={"placement": "left", "always_visible": False}
    )
'''

'''
,
dbc.Row([
    dbc.Col([html.H3('carlg', style=dict(color='firebrick')), html.P('...', id='last_update_p_1'), html.P('...', id='last_battery_1')], width=5)
    ]),
dbc.Row([
    dbc.Col([html.H3('marti', style=dict(color='darkgreen')), html.P('...', id='last_update_p_2'), html.P('...', id='last_battery_2')], width=5)
    ])
'''

header = html.Div(
        dbc.Card(
            dbc.CardBody([
                dbc.Row([
                    # dbc.Col([slid], width=1),
                    dbc.Col([mygraph1], width=11)
                    ]),
                dbc.Row(
                    dbc.Col([tab_graph], width=10, style={'padding-left':'15%', 'padding-right':'15%', 'justify-content':'center'})
                )
            ])
        ),
        style={
        } # 'background-color': 'rgba(0,0,122,0.2)',
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
    return create_info_table()

@app.callback(
        Output(mygraph1, component_property='figure'),
        [
        #Input(slid, component_property='value'),
        Input(interval, component_property='n_intervals')]
)
def update_smoothing (n_intervals, val = 25):
    df_1 = get_data(DBNAME_1, val)
    df_2 = get_data(DBNAME_2, val)

    fig1.update_traces(x=df_1.timestamp, y=df_1.wtemperature, selector=dict(name="T_carlg"))
    fig1.update_traces(x=df_1.timestamp, y=df_1.whumidity, selector=dict(name="H_carlg"))
    
    fig1.update_traces(x=df_2.timestamp, y=df_2.wtemperature, selector=dict(name="T_marti"))
    fig1.update_traces(x=df_2.timestamp, y=df_2.whumidity, selector=dict(name="H_marti"))

    return fig1

if __name__ == '__main__':
    app.run(
        host='192.168.1.60',
        port=8080,
        debug=True,
        dev_tools_hot_reload=True
    )
