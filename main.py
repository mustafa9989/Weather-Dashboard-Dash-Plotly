# https://www.weatherapi.com/api-explorer.aspx#forecast
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
from dash.dependencies import Input, Output
import dash_daq as daq
import plotly.express as px
import pandas as pd
import datetime
import json
import urllib3
import os
import pytz
import plotly.graph_objs as go
import numpy as np

API_KEY = os.environ['API_KEY']

app = Dash(__name__,
           suppress_callback_exceptions=True,
           external_stylesheets=[dbc.themes.MORPH])  # QUARTZ
server = app.server
app.title = "🌤 Weather"
load_figure_template('MORPH')

header = html.H1(id='header')
header_paragraph = html.P(id='header_paragraph')
cities_list = [
  'Cairo', 'Alexandria', 'Giza', 'Shubra El Kheima', 'Port Said', 'Suez',
  'El Mahalla El Kubra', 'Luxor', 'Mansoura', 'Tanta', 'Asyut', 'Ismailia',
  'Faiyum', 'Zagazig', 'Damietta', 'Aswan', 'Minya', 'Damanhur', 'Beni Suef',
  'Hurghada', 'Qena', 'Sohag', 'Shibin El Kom', 'Banha', 'Arish'
]

tab1_content = html.Div([
  dbc.Row([
    dbc.Row([
      dbc.Col([header, header_paragraph,
               html.Div(id="target")]),
      dbc.Col(
        [dcc.Dropdown(cities_list, cities_list[0], id='cities-dropdown_1')])
    ]),
    dbc.Row([
      dbc.Col([
        dbc.Row([
          dbc.Col(id='card1'),
          dbc.Col(id='card2'),
          dbc.Col(id='card3'),
          dbc.Col(id='card4'),
          dbc.Col(id='card5'),
          dbc.Col(id='card6'),
        ]),
        dbc.Row(id='temp_day'),
        dbc.Row(id='uv_graph'),
        dbc.Row([dbc.Col(id='wind'),
                 dbc.Col(id='humidity')])
      ]),
      dbc.Col([
        dbc.Row(id='today_card'),
        dbc.Row([dbc.Col(id='sunrise_card'), 
        dbc.Col(id='sunset_card')]),
        dbc.Row(id='feelslike'),
      ],
              width=3)
    ]),
    dcc.Interval(id='interval-component1',
                 interval=1 * 1000 * 60 / 2,
                 n_intervals=0),  # every half a minute
    dcc.Interval(id='interval-component2',
                 interval=1 * 1000 * 60 * 60,
                 n_intervals=0)  # every hour
  ])
])

tab2_content = html.Div([
  html.H3('Compare two cities'),
  html.P('Choose two cities from the dropdown menus to start comparing them together'),
  dbc.Row([
    dbc.Col(dcc.Dropdown(cities_list, cities_list[0], id='cities-dropdown_2')),
    dbc.Col(dcc.Dropdown(cities_list, cities_list[1], id='cities-dropdown_3'))
  ]),
  dbc.Row(dbc.Col(id='temp_compare_graph')),
  dbc.Row([
    dbc.Col(id='humidity_compare_graph')
  ]),
  dbc.Row([
    dbc.Col(id='wind_compare_1'),
    dbc.Col(id='wind_compare_2')
  ])
])


def create_graph_card(graph):
  return dbc.Card(
    [dbc.CardBody(graph)],
    className="text-center text-black shadow",
    style={
      'width': 'fit-content',
      'background': 'white',
      'margin-top': '15px',
      'margin-bottom': '10px',
      'border-radius': '30px'
    })


def create_card(img, d, c, avg_t=0):
  my_card = dbc.Card(
    [
      dbc.CardImg(src=img,
                  top=True,
                  style={
                    "height": 80,
                    'width': 80
                  },
                  className='align-self-center'),
      dbc.CardBody([
        html.B(html.H5(d[:3])),  # day name
        # html.H6(c),  # weather condition
        html.H6(f'{avg_t} °C'),  # average temp
      ]),
    ],
    className="text-center text-black shadow",
    style={
      'width': '100%',
      'background': 'white',
      'margin-top': '30px',
      'margin-bottom': '10px',
      'border-radius': '35px'
    })
  return my_card


# Today's card
def main_card(img, d, c, max_t=0, min_t=0, curr_t=0):
  full_date = datetime.datetime.now(
    pytz.timezone("Africa/Cairo")).strftime('%d %B')
  my_card = dbc.Card(
    [
      dbc.CardImg(src=img,
                  top=True,
                  style={
                    "height": 100,
                    'width': 110
                  },
                  className='align-self-center'),
      dbc.CardBody([
        html.H6(f'Today, {full_date}'),  # day name
        html.B(html.H3(f'{curr_t} °C')),  # current temp
        html.H5(c),  # weather condition
        html.Br(),
        html.H6(f'\n{max_t} °C (max)'),  # max temp
        html.H6(f'{min_t} °C (min)'),  # min temp
      ]),
    ],
    className="text-center text-white shadow",
    style={
      'background': '#378dfc',
      'margin-top': '30px',
      'margin-bottom': '10px',
      'margin-left': '20px',
      'border-radius': '35px'
    })
  return my_card


app.layout = html.Div(children=[
  dbc.Row(dcc.Tabs(id="tabs",
                   value='tab1_current',
                   children=[
                     dcc.Tab(label='Show Current', value='tab1_current'),
                     dcc.Tab(label='Show Comparison', value='tab2_comparison'),
                   ]),
          style={'margin-bottom': '30px'}),
  dbc.Container([tab1_content], id='tabs_content'),
])


@app.callback(Output('tabs_content', 'children'), Input('tabs', 'value'))
def render_content(tab):
  if tab == 'tab1_current':
    return tab1_content
  elif tab == 'tab2_comparison':
    return tab2_content


# just to update the time in the header
@app.callback([Output('header', 'children'),
               Output('target', 'children')], [
                 Input('interval-component1', 'n_intervals'),
                 Input('cities-dropdown_1', 'value')
               ])
def update_clock(value, city):
  currentTime = datetime.datetime.now(pytz.timezone('Africa/Cairo'))
  current_time = currentTime.strftime("%I:%M %p")
  greeting = ''
  if currentTime.hour < 12:
    greeting = '🌄 Good morning!'
  elif currentTime.hour >= 12 and currentTime.hour < 18:
    greeting = '🌇 Good afternoon!'
  else:
    greeting = '🌆 Good evening!'
  return [current_time], html.H3(greeting)


@app.callback([
  Output('header_paragraph', 'children'),
  Output('temp_day', 'children'),
  Output('wind', 'children'),
  Output('humidity', 'children'),
  Output('feelslike', 'children'),
  Output('today_card', 'children'),
  Output('card1', 'children'),
  Output('card2', 'children'),
  Output('card3', 'children'),
  Output('card4', 'children'),
  Output('card5', 'children'),
  Output('card6', 'children'),
  Output('sunrise_card', 'children'),
  Output('sunset_card', 'children'),
  Output('uv_graph', 'children')
], [
  Input('interval-component2', 'n_intervals'),
  Input('cities-dropdown_1', 'value')
])
def update_graphs(value, city):
  full_date = datetime.datetime.now(
    pytz.timezone("Africa/Cairo")).strftime('%A, %d %B, %Y')

  http = urllib3.PoolManager()
  url = 'http://ipinfo.io/json'
  response = http.request('GET', url)
  # data = json.loads(response.data.decode('utf-8'))
  # IP = data['ip']
  # org = data['org']
  # city = 'Cairo'  # data['city']
  # country = data['country']
  # region = data['region']

  url = f'http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={city}&days=8&aqi=no&alerts=no'

  response = http.request('GET', url)
  current_data_day = json.loads(response.data.decode('utf-8'))

  hours = current_data_day['forecast']['forecastday'][0]['hour']
  temp_c = np.array([hour['temp_c'] for hour in hours])
  current_wind = current_data_day['current']['wind_kph']
  feels_like = current_data_day['current']['feelslike_c']
  humidity = current_data_day['current']['humidity']
  x = np.arange(0, 24)

  df = pd.DataFrame()
  df['Hours'] = x
  df['Temperature'] = temp_c

  wind_gauge = create_graph_card(
    daq.Gauge(label="Wind",
              value=current_wind,
              min=0,
              max=50,
              showCurrentValue=True,
              units='Km/h'))

  feelslike_graph = create_graph_card(
    daq.Thermometer(value=feels_like,
                    min=0,
                    max=70,
                    label='feels like',
                    labelPosition='top',
                    showCurrentValue=True,
                    units="°C",
                    style={
                      'margin-top': '30px',
                    }))

  humidity_graph = create_graph_card(
    daq.Gauge(value=humidity,
              label='Humidity',
              max=100,
              min=0,
              color={
                "gradient": True,
                "ranges": {
                  "#fffdc2": [0, 21],
                  "#d7f0a2": [21, 119],
                  "#fffdc1": [119, 140]
                }
              },
              showCurrentValue=True,
              units='%'))

  # uv graph
  uv_indexes = np.array([hour['uv'] for hour in hours])
  hours_str = np.array([hour['time'][11:] for hour in hours])
  fig_11 = px.line(x=hours_str,
                   y=uv_indexes,
                   line_shape='spline',
                   title='UV index over the day',
                   labels={
                     'x': 'time',
                     'y': 'uv-index'
                   })
  fig_11.add_trace(
    go.Scatter(x=['00:00', '23:00'],
               y=[6, 6],
               mode="lines",
               name="max accepted uv",
               fillcolor="red"))

  fig_11.update_layout(xaxis=dict(tickmode="array",
                                  tickvals=hours_str[::2],
                                  ticktext=hours_str[::2],
                                  tickangle=40))
  uv_graph = create_graph_card(dcc.Graph(figure=fig_11))

  days = []
  conds = []
  icons = []
  avg_temp = []

  for i in range(7):
    print(i)
    try:
      d = current_data_day['forecast']['forecastday'][i]['date']
      d = pd.Timestamp(d)
      days.append(d.day_name())
      avg_temp.append(
        current_data_day['forecast']['forecastday'][i]['day']['avgtemp_c'])
      icons.append(current_data_day['forecast']['forecastday'][i]['day']
                   ['condition']['icon'])
      conds.append(current_data_day['forecast']['forecastday'][i]['day']
                   ['condition']['text'])
    except Exception as e:
      print(f"Error processing data for index {i}: {e}")

  # sunset & sunrise for today
  sunrise = current_data_day['forecast']['forecastday'][0]['astro']['sunrise']
  sunset = current_data_day['forecast']['forecastday'][0]['astro']['sunset']

  sunrise_card = dbc.Card(
    [
      dbc.CardBody([html.B(html.H6("🌅 Sunrise")),
                    html.H6(sunrise)]),
    ],
    className="text-center text-white shadow",
    style={
      'width': '152px',
      'background': '#E49393',
      'margin-top': '30px',
      'margin-bottom': '10px',
      'border-radius': '35px'
    })

  sunset_card = dbc.Card(
    [
      dbc.CardBody([html.B(html.H6("🌇 Sunset")),
                    html.H6(sunset)]),
    ],
    className="text-center text-white shadow",
    style={
      'width': '150px',
      'background': '#408E91',
      'margin-top': '30px',
      'margin-bottom': '10px',
      'border-radius': '35px'
    })

  max_temp_0 = current_data_day['forecast']['forecastday'][0]['day'][
    'maxtemp_c']
  min_temp_0 = current_data_day['forecast']['forecastday'][0]['day'][
    'mintemp_c']
  curr_temp_0 = current_data_day['current']['temp_c']
  today = current_data_day['current']['last_updated'][:10]

  card_0 = main_card(icons[0], today, conds[0], max_temp_0, min_temp_0,
                     curr_temp_0)
  card_1 = create_card(icons[1], days[1], conds[1], avg_temp[1])
  card_2 = create_card(icons[2], days[2], conds[2], avg_temp[2])
  card_3 = create_card(icons[3], days[3], conds[3], avg_temp[3])
  card_4 = create_card(icons[4], days[4], conds[4], avg_temp[4])
  card_5 = create_card(icons[5], days[5], conds[5], avg_temp[5])
  card_6 = create_card(icons[6], days[6], conds[6], avg_temp[6])

  fig = px.line(df,
                x=hours_str,
                y="Temperature",
                line_shape='spline',
                title='Temperature over the day',
                labels={'x': 'Time'})

  fig.update_layout(xaxis=dict(tickmode="array",
                               tickvals=hours_str[::2],
                               ticktext=hours_str[::2],
                               tickangle=40))

  fig.update_layout({
    'plot_bgcolor': 'rgba(0,0,0,0)',
    'paper_bgcolor': 'rgba(0,0,0,0)',
  })

  graph1 = create_graph_card(dcc.Graph(figure=fig))

  return full_date, graph1, wind_gauge, humidity_graph, feelslike_graph, card_0, card_1, card_2, card_3, card_4, card_5, card_6, sunrise_card, sunset_card, uv_graph
  # request.remote_addr
  # f'{current_data_day["current"]["temp_c"]} °C'


# second tab callback
@app.callback([
  Output('temp_compare_graph', 'children'),
  Output('humidity_compare_graph', 'children'),
  Output('wind_compare_1', 'children'),
  Output('wind_compare_2', 'children')
], [Input('cities-dropdown_2', 'value'),
    Input('cities-dropdown_3', 'value')])
def update_compare_graphs(city_1, city_2):
  http = urllib3.PoolManager()
  url_1 = f'http://api.weatherapi.com/v1/forecast.json?key=  {API_KEY}&q=  {city_1}&days={7}&aqi=no&alerts=no'
  response_1 = http.request('GET', url_1)
  first_city = json.loads(response_1.data.decode('utf-8'))
  url_2 = f'http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q=  {city_2}&days={7}&aqi=no&alerts=no'
  response_2 = http.request('GET', url_2)
  second_city = json.loads(response_2.data.decode('utf-8'))

  # days
  first_city_days = first_city['forecast']['forecastday']
  second_city_days = second_city['forecast']['forecastday']

  # temperatures every day for the next seven days every three hours
  first_city_temps = np.array(
    [hour['temp_c'] for day in first_city_days for hour in day['hour']][::3])
  second_city_temps = np.array(
    [hour['temp_c'] for day in second_city_days for hour in day['hour']][::3])

  # wind speed every day for the next seven days every three hours
  first_city_wind_speed = np.array(
    [hour['wind_kph'] for day in first_city_days for hour in day['hour']][::3])
  second_city_wind_speed = np.array([
    hour['wind_kph'] for day in second_city_days for hour in day['hour']
  ][::3])

  # humidity every day for the next seven days every three hours
  first_city_humidity = np.array(
    [hour['humidity'] for day in first_city_days for hour in day['hour']][::3])
  second_city_humidity = np.array([
    hour['humidity'] for day in second_city_days for hour in day['hour']
  ][::3])

  # dates every three hours
  date = np.array(
    [hour['time'] for day in first_city_days for hour in day['hour']][::3])

  if city_1 == city_2:
    first_city['location']['name'] += ' 1'
    second_city['location']['name'] += ' 2'

  # creating a dataframe contains information of the two cities
  df_compare = pd.DataFrame()
  df_compare['date'] = date
  df_compare["date"] = pd.to_datetime(df_compare["date"])

  df_compare[f"{first_city['location']['name']}"] = first_city_temps
  df_compare[f"{second_city['location']['name']}"] = second_city_temps

  df_compare[f"wind_speed in {df_compare.columns[1]}"] = first_city_wind_speed
  df_compare[f"wind_speed in {df_compare.columns[2]}"] = second_city_wind_speed

  df_compare[f"humidity in {df_compare.columns[1]}"] = first_city_humidity
  df_compare[f"humidity in {df_compare.columns[2]}"] = second_city_humidity
  color1, color2 = '#7262fc', '#853257'

  # temp graph
  fig_2 = px.area(df_compare,
                  x='date',
                  y=[df_compare.columns[1], df_compare.columns[2]],
                  labels={'value': 'Temperatue'},
                  color_discrete_sequence=[color1, color2],
                  line_shape='spline')
  fig_2.update_layout(
    xaxis=dict(tickmode="array",
               tickvals=df_compare["date"][::8],
               ticktext=df_compare["date"].dt.strftime('%m-%d')[::8],
               tickangle=40))
  fig_2.update_traces(stackgroup=None, fill='tozeroy')
  
  # humidity graph
  fig_4 = px.area(df_compare,
                  'date',
                  y=[df_compare.columns[5], df_compare.columns[6]],
                  labels={'value': 'Humidity'},
                  color_discrete_sequence=[color1, color2],
                  line_shape='spline')
  fig_4.update_layout(
    xaxis=dict(tickmode="array",
               tickvals=df_compare["date"][::8],
               ticktext=df_compare["date"].dt.strftime('%m-%d')[::8],
               tickangle=40))
  fig_4.update_traces(stackgroup=None, fill='tozeroy')

  # wind graph data
  hours = first_city['forecast']['forecastday'][0]['hour']
  hours_2 = second_city['forecast']['forecastday'][0]['hour']

  wind_dir = np.array([hour['wind_dir'] for hour in hours])
  wind_speed = np.array([hour['wind_kph'] for hour in hours])

  wind_dir_2 = np.array([hour['wind_dir'] for hour in hours_2])
  wind_speed_2 = np.array([hour['wind_kph'] for hour in hours_2])

  df_wind = pd.DataFrame()
  df_wind[f'wind direction in {df_compare.columns[1]}'] = wind_dir
  df_wind[f'wind-speed in {df_compare.columns[1]}'] = wind_speed
  df_wind[f'wind direction in {df_compare.columns[2]}'] = wind_dir_2
  df_wind[f'wind-speed in {df_compare.columns[2]}'] = wind_speed_2

  # wind graph 1
  fig_8 = px.bar_polar(df_wind,
                       r=f'{df_wind.columns[1]}',
                       theta=f'{df_wind.columns[0]}',
                       template="plotly_dark",
                       color=f"{df_wind.columns[1]}",
                       color_discrete_sequence=px.colors.sequential.Plasma_r,
                       category_orders={
                         f"{df_wind.columns[0]}": [
                           "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                           "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
                         ]
                       },
                       range_r=(0, 50))

  # wind graph 2
  fig_9 = px.bar_polar(df_wind,
                       r=f'{df_wind.columns[3]}',
                       theta=f'{df_wind.columns[2]}',
                       template="plotly_dark",
                       color=f"{df_wind.columns[3]}",
                       color_discrete_sequence=px.colors.sequential.Plasma_r,
                       category_orders={
                         f"{df_wind.columns[2]}": [
                           "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                           "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
                         ]
                       },
                       range_r=(0, 50))

  graph2 = create_graph_card(
    dcc.Graph(figure=fig_2))  # , className='scorecard__graph'
  graph4 = create_graph_card(dcc.Graph(figure=fig_4))

  graph8 = create_graph_card(dcc.Graph(figure=fig_8))
  graph9 = create_graph_card(dcc.Graph(figure=fig_9))

  return graph2, graph4, graph8, graph9


if __name__ == '__main__':
  app.run_server(host='0.0.0.0', port=80, debug=True)
