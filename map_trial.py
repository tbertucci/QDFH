import plotly.express as px
import geopandas as gpd
import pandas as pd
from dash import Dash, dcc, html, Output, Input, callback, dash_table
import itertools

cities = pd.read_csv('languageCities.csv', encoding = 'utf-8')

cities_geo = gpd.GeoDataFrame(cities, geometry = gpd.points_from_xy(cities['latitude'], cities['longitude']))

display_data = pd.read_csv('display_data.csv')

# group by treatment, find min and max number, add to treatment var
treatment_range = display_data.groupby('treatment')['number'].agg(['min', 'max']).reset_index()

treatment_dict = {}
for treatment,row in treatment_range.iterrows():
    key = row['treatment']

    if row['min'] == row['max']:
        string =  str(int(row['min'])).zfill(3) + ' ' + key   
        treatment_dict[key] = string

    else:
        string = str(int(row['min'])).zfill(3) + '-' + str(int(row['max'])).zfill(3) + ' ' + key
        treatment_dict[key] = string

display_data['treatment'] = display_data['treatment'].map(treatment_dict)


#filter = display_data[(display_data['treatment'] == 'T-') & (display_data['environment'] == '#_E')]
#print(filter)

display_data['sonority_scaled'] = (display_data['sonority_avg'] - display_data['sonority_avg'].min()) / (display_data['sonority_avg'].max() - display_data['sonority_avg'].min())
display_data['place_scaled'] = (display_data['place_avg'] - display_data['place_avg'].min()) / (display_data['place_avg'].max() - display_data['place_avg'].min())


def blend_colors(r, g, b):
    return f'rgb({int(r * 255)}, {int(g)}, {int(b * 255)})'

display_data['color'] = [blend_colors(r, g, b) for r, g, b in zip(display_data['sonority_scaled'], display_data['voice_avg'], display_data['place_scaled'])]

version_sub = display_data[(display_data['treatment'] == '001-002 B-') & (display_data['environment'] == 'V_V')]
version_sub = version_sub[['language', 'display']]


app = Dash()

app.layout = html.Div(children=[
    html.H1(children='QDFH'),

    html.Div(children='''
        A visual presentation of Latin consonants across the Romance languages
    '''),

    html.Div(children = [
        html.Label('Treatment'),
        dcc.Dropdown(display_data.sort_values(by = 'number')['treatment'].unique().tolist(),
                     value = '001-002 B-',
                     id = 'select_treatment')
        ]),

    html.Div(children = [
        html.Label('Environment'),
        dcc.Dropdown(value = 'V_V', 
                     id = 'select_environment')
    ]),

    html.Div(children = [
             html.Label('Version'),
             dcc.Dropdown(value = 'a',
                          id = 'select_version')
                          ]),

    html.Div([
        html.Div([
            html.Div(id='ipa_table_1', style={'width': '49%', 'display': 'inline-block'}),
            html.Div(id='ipa_table_2', style={'width': '49%', 'display': 'inline-block'}),
        ], style={'width': '40%', 'display': 'inline-block', 'verticalAlign': 'top'}),

        
        dcc.Graph(id='map', style={'width': '60%', 'display': 'inline-block', 'verticalAlign': 'top'})
        ], style={'display': 'flex', 'flexDirection': 'row', 'gap': '20px'})

])

@callback(
    Output('select_environment', 'options'),
    Input('select_treatment', 'value')
)
def update_environments(treatment):
    environ_list = display_data[display_data['treatment'] == treatment]['environment'].unique().tolist()
    return environ_list

@callback(
    Output('select_version', 'options'),
    Input('select_treatment', 'value'),
    Input('select_environment', 'value')
)
def update_versions(treatment, environment):
    versions_list = display_data[(display_data['treatment'] == treatment) & (display_data['environment'] == environment)]['version'].sort_values().unique().tolist()
    return versions_list



@callback(
    Output('map', 'figure'),
    Output('ipa_table_1', 'children'),
    Output('ipa_table_2', 'children'),
    Input('select_treatment', 'value'),
    Input('select_environment', 'value'),
    Input('select_version', 'value'))
def update_map(selected_treatment, selected_environment, selected_version):
    latin_to_rom_sub = display_data[(display_data['treatment'] == selected_treatment) &
                                     (display_data['environment'] == selected_environment)]
    
    grouped = latin_to_rom_sub.groupby('language')

    version_tables = []
    for language, df in grouped:
        if selected_version in df['version'].unique().tolist():
            select_version = selected_version
        else:
            select_version = 'a'
        
        lang_table = df[df['version'] == select_version]
        version_tables.append(lang_table)

    if version_tables:
        version_sub = pd.concat(version_tables, axis=0)
    else:
        version_sub = pd.DataFrame(columns=display_data.columns)


    city_context = pd.merge(cities_geo, version_sub, left_on = 'language_code', right_on = 'language').dropna(subset = 'display')

    fig = px.scatter_geo(city_context,
                    lat=city_context.geometry.x,
                    lon=city_context.geometry.y, 
                    text = 'display',
                    hover_name = 'Language Variety',
                    hover_data=['sonority_avg', 'place_avg'],
                    color = city_context['color'],
                    color_discrete_map = 'identity')

    fig.update_layout(geo = dict(projection_scale = 8,
                                 center = dict(lat = 45.76, lon = 4.84)),
                        margin=dict(t=10,l=10,b=10,r=10)
                        )
    fig.update_traces(textfont = dict(family = 'Arial',
                                    size = 16,
                                    color = 'black'),
                        marker = dict(size = 30,
                                      opacity = 0.4))
    fig.update_geos(showcountries = True)


    #version_sub = city_context.sort_values(['latitude'])
    version_sub = pd.merge(cities_geo, version_sub, left_on = 'language_code', right_on = 'language').sort_values('longitude')
    version_sub = version_sub[['language', 'display']]

    columns = [{'name': i, 'id': i} for i in version_sub.columns]
    version_sub = version_sub.to_dict('records')
    mid = len(version_sub) //2 if len(version_sub) > 16 else len(version_sub)
    col1_data = version_sub[:mid]
    col2_data = version_sub[mid:] if len(version_sub) > 16 else []


    table1 = dash_table.DataTable(data=col1_data, columns=columns, style_table={'overflowX': 'auto'})
    table2 = dash_table.DataTable(data=col2_data, columns=columns, style_table={'overflowX': 'auto'}) if col2_data else None

    return fig, table1, table2


if __name__ == '__main__':
    app.run(debug=True)
