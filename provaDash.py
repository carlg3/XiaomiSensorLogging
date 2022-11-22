from dash import Dash, dcc, Output, Input, html
import dash_bootstrap_components as dbc
import plotly.express as px
import sqlite3
import pandas as pd

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

DBNAME = 't_h_readings.db'
con  = sqlite3.connect(DBNAME,
                      detect_types=sqlite3.PARSE_DECLTYPES |
                        sqlite3.PARSE_COLNAMES)

cur = con.cursor()
query = '''SELECT
                timestamp as "timestamp [timestamp]",
                temperature,
                avg(temperature) OVER
                    (ORDER BY timestamp ROWS BETWEEN 10 PRECEDING AND 10 FOLLOWING)
                    as wtemperature,
                humidity,
                avg(humidity) OVER
                    (ORDER BY timestamp ROWS BETWEEN 10 PRECEDING AND 10 FOLLOWING)
                    as whumidity
            FROM reading ORDER BY timestamp;'''
df = pd.read_sql_query(query, con)

mygraph = dcc.Graph(figure={})

dropdown = dcc.Dropdown(options=['wtemperature', 'whumidity'],
        value='wtemperature',
        clearable=False)
temp_button = dbc.Button("Temperature")
humi_button = dbc.Button("Humidity")

radio = dbc.RadioItems(
            id="radios",
            className="btn-group",
            inputClassName="btn-check",
            labelClassName="btn btn-outline-primary",
            labelCheckedClassName="active",
            options=[
                {"label": "Temperature", "value": 'wtemperature'},
                {"label": "Humidity", "value": 'whumidity'}
            ],
            value='wtemperature',
        )
button_group = html.Div(
    [
        radio,
        html.Div(id='output'),
    ],
    className='radio-group',
)

app.layout = dbc.Container([mygraph, button_group])

@app.callback(
        Output(mygraph, component_property='figure'),

        Input(radio, component_property='value')
)
def update_title (user_input):
    fig = px.line(data_frame=df, x="timestamp", y=user_input)
    return fig



if __name__ == '__main__':
    app.run(
        host='192.168.178.58',
        port=8080,
        debug=True,
        dev_tools_hot_reload=True
    )
