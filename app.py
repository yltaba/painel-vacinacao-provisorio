import json
from pathlib import Path
import pandas as pd
from babel.numbers import format_decimal

from dash import Dash, dcc, html, Input, Output, State, no_update, dash_table, ctx
import dash_bootstrap_components as dbc
import plotly.express as px

from src.utils import get_options_dropdown


# data
DATA_PATH = Path().resolve() / "data"
SHP_FOLDER = Path().resolve() / "data" / "shapefiles"

n_vacinas_escola = pd.read_csv(DATA_PATH / "n_vacinas_escola.csv", sep=";")
n_vacinas_escola = n_vacinas_escola.query(
    "data_vacinacao_ano >= 2015"
)  # há apenas poucas vacinas antes disso, parece sujeira

n_alunos = pd.read_csv(DATA_PATH / "n_alunos.csv", sep=";")

anos = sorted(n_vacinas_escola["data_vacinacao_ano"].unique())
ano_min, ano_max = min(anos), max(anos)

imagem_cabecalho = html.Img(
    src="/assets/Marca-Osasco-Digital-COLOR-ALTA-02.svg",
    style={
        "width": "350px",
        "height": "auto",
        "display": "block",
        "margin": "10px 20px",  # Remove a margem lateral, mantém só topo e base
        "padding-left": "0",  # Garante que não há padding à esquerda
    },
)

# app
app = Dash(external_stylesheets=[dbc.themes.SANDSTONE])
app.title = "Painel de Vacinação"

app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    imagem_cabecalho,
                    width=12,
                    # className="d-flex justify-content-center",
                ),
            ],
        ),
        dbc.Row(
            [
                # COLUNA 1: Filtros e alerta
                dbc.Col(
                    [
                        html.Div(
                            [
                                dbc.Button(
                                    "Limpar filtros",
                                    id="btn-limpar-filtros",
                                    color="secondary",
                                    outline=True,
                                    style={"marginBottom": "1rem", "width": "100%"},
                                ),
                                html.Br(),
                                html.Strong("Selecione o ano:"),
                                dcc.Dropdown(
                                    id="dropdown-ano",
                                    options=[
                                        {"label": str(ano), "value": ano}
                                        for ano in anos
                                    ],
                                    value=ano_max,
                                    clearable=False,
                                    style={"width": "100%"},
                                ),
                                html.Br(),
                                html.Strong("Selecione a modalidade escolar:"),
                                dcc.Dropdown(
                                    id="dropdown-modalidade",
                                    options=[{"label": "Todas", "value": "Todas"}]
                                    + get_options_dropdown(
                                        n_vacinas_escola, "modalidade"
                                    ),
                                    value="Todas",
                                    clearable=False,
                                ),
                                html.Br(),
                                html.Strong("Selecione o tipo de unidade escolar:"),
                                dcc.Dropdown(
                                    id="dropdown-tp-unidade",
                                    options=[{"label": "Todas", "value": "Todas"}]
                                    + get_options_dropdown(
                                        n_vacinas_escola, "tipo_unidade"
                                    ),
                                    value="Todas",
                                    clearable=False,
                                ),
                                html.Br(),
                                html.Strong("Selecione a escola:"),
                                dcc.Dropdown(
                                    id="select-escola-mapa",
                                    value="Todas",
                                    searchable=True,
                                ),
                                html.Br(),
                                html.Strong("Selecione a vacina:"),
                                dcc.Dropdown(
                                    id="dropdown-vacina-mapa",
                                    options=[{"label": "Todas", "value": "Todas"}]
                                    + get_options_dropdown(n_vacinas_escola, "vacina"),
                                    value="Todas",
                                ),
                                html.Br(),
                            ]
                        ),
                    ],
                    width=3,
                    style={
                        "height": "100vh",
                        "padding": "2rem 1rem",
                    },
                ),
                # COLUNA 2: Mapa
                dbc.Col(
                    [dcc.Graph(id="mapa-vacinacao", style={"width": "100%"})],
                    width=7,
                    style={"padding": "2rem 1rem"},
                ),
                # COLUNA 3: Cards descritivos
                dbc.Col(
                    [
                        html.Div(
                            id="info-escola-selecionada", style={"marginTop": "2rem"}
                        ),
                    ],
                    width=2,
                ),
            ],
            style={"height": "100vh"},
        ),
    ],
    fluid=True,
)


def formatar_label(label):
    preposicoes = {
        "em", "de", "da", "do", "dos", "das", "a", "e", "para", "por", "com", "sem", "sob", "sobre", "às", "ao", "aos", "as", "no", "na", "nos", "nas"
    }
    palavras = label.lower().split()
    resultado = []
    for i, palavra in enumerate(palavras):
        if i == 0 or palavra not in preposicoes:
            resultado.append(palavra.capitalize())
        else:
            resultado.append(palavra)
    return " ".join(resultado)


# CALLBACKS
# callback para mostrar informações da escola selecionada em um alerta
@app.callback(
    Output("info-escola-selecionada", "children"),
    [
        Input("select-escola-mapa", "value"),
        Input("dropdown-tp-unidade", "value"),
        Input("dropdown-modalidade", "value"),
        Input("dropdown-ano", "value"),
        Input("dropdown-vacina-mapa", "value"),
    ],
)
def mostrar_info_escola(
    escola: str,
    tipo_unidade: str,
    modalidade: str,
    ano_selecionado: int,
    vacina: str,
):
    # Filtro para mostrar todos os dados quando dropdown esvaziado (clear value)
    if escola is None:
        escola = "Todas"
    if tipo_unidade is None:
        tipo_unidade = "Todas"
    if vacina is None:
        vacina = "Todas"
    if modalidade is None:
        modalidade = "Todas"

    if escola == "Todas":
        df_escola = n_vacinas_escola
        df_alunos = n_alunos
    else:
        df_escola = n_vacinas_escola[n_vacinas_escola["nome_unidade"] == escola]
        df_alunos = n_alunos[n_alunos["nome_unidade"] == escola]

    if tipo_unidade != "Todas":
        df_escola = df_escola[df_escola["tipo_unidade"] == tipo_unidade]
        df_alunos = df_alunos[df_alunos["tipo_unidade"] == tipo_unidade]

    if vacina != "Todas":
        df_escola = df_escola[df_escola["vacina"] == vacina]

    if modalidade != "Todas":
        df_escola = df_escola[df_escola["modalidade"] == modalidade]

    n_vacinas = format_decimal(
        df_escola[df_escola["data_vacinacao_ano"] == ano_selecionado][
            "n_vacinas"
        ].sum(),
        locale="pt_BR",
    )

    ind_card_n_alunos = format_decimal(
        df_alunos["ra"].nunique(),
        locale="pt_BR",
    )

    media_idade = format_decimal(df_escola["idade"].mean().round(1), locale="pt_BR")

    cards = [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    "Total de alunos",
                                    style={
                                        "height": "3rem",
                                        "display": "flex",
                                        "alignItems": "center",
                                        "justifyContent": "center",
                                        "background-color": "#e3f2fd",
                                        "fontWeight": "bold",
                                    },
                                ),
                                dbc.CardBody(
                                    [
                                        html.P(
                                            ind_card_n_alunos,
                                            style={"fontSize": "1.5rem"},
                                        )
                                    ],
                                ),
                            ],
                            style={
                                "width": "200px",
                                "height": "120px",
                                "marginBottom": "1rem",
                                "textAlign": "center",
                            },
                        ),
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    "Vacinas aplicadas",
                                    style={
                                        "height": "3rem",
                                        "display": "flex",
                                        "alignItems": "center",
                                        "justifyContent": "center",
                                        "background-color": "#e3f2fd",
                                        "fontWeight": "bold",
                                    },
                                ),
                                dbc.CardBody(
                                    [html.P(n_vacinas, style={"fontSize": "1.5rem"})],
                                ),
                            ],
                            style={
                                "marginRight": "0.5rem",
                                "width": "200px",
                                "height": "120px",
                                "marginBottom": "1rem",
                                "textAlign": "center",
                            },
                        ),
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    "Média de idade",
                                    style={
                                        "height": "3rem",
                                        "display": "flex",
                                        "alignItems": "center",
                                        "justifyContent": "center",
                                        "background-color": "#e3f2fd",
                                        "fontWeight": "bold",
                                    },
                                ),
                                dbc.CardBody(
                                    [html.P(media_idade, style={"fontSize": "1.5rem"})]
                                ),
                            ],
                            style={
                                "marginRight": "0.5rem",
                                "width": "200px",
                                "height": "120px",
                                "marginBottom": "1rem",
                                "textAlign": "center",
                            },
                        ),
                    ],
                    width=12,
                ),
            ]
        ),
    ]
    # RETORNOS
    return html.Div(cards)


@app.callback(
    Output("select-escola-mapa", "value"),
    [
        Input("mapa-vacinacao", "clickData"),
        Input("btn-limpar-filtros", "n_clicks"),
    ],
    prevent_initial_call=True,
)
def selecionar_ou_limpar_escola(clickData, n_clicks):
    trigger = ctx.triggered_id
    if trigger == "mapa-vacinacao":
        if clickData and "points" in clickData and len(clickData["points"]) > 0:
            point = clickData["points"][0]
            nome = point.get("hovertext") or (
                point.get("customdata")[0] if point.get("customdata") else None
            )
            return nome
        return no_update
    elif trigger == "btn-limpar-filtros":
        return "Todas"
    return no_update


@app.callback(
    [
        Output("dropdown-ano", "value"),
        Output("dropdown-modalidade", "value"),
        Output("dropdown-tp-unidade", "value"),
        Output("dropdown-vacina-mapa", "value"),
    ],
    Input("btn-limpar-filtros", "n_clicks"),
    prevent_initial_call=True,
)
def limpar_outros_filtros(n_clicks):
    return ano_max, "Todas", "Todas", "Todas"


@app.callback(
    Output("select-escola-mapa", "options"),
    [
        Input("dropdown-ano", "value"),
        Input("dropdown-tp-unidade", "value"),
        Input("dropdown-modalidade", "value"),
        Input("dropdown-vacina-mapa", "value"),
    ],
)
def update_escola_options(ano, tipo_unidade, modalidade, vacina):
    df = n_vacinas_escola.copy()
    if ano is not None:
        df = df[df["data_vacinacao_ano"] == ano]
    if tipo_unidade is not None and tipo_unidade != "Todas":
        df = df[df["tipo_unidade"] == tipo_unidade]
    if modalidade is not None and modalidade != "Todas":
        df = df[df["modalidade"] == modalidade]
    if vacina is not None and vacina != "Todas":
        df = df[df["vacina"] == vacina]

    escolas = sorted(df["nome_unidade"].dropna().unique())
    options = [{"label": "Todas", "value": "Todas"}] + [
        {"label": formatar_label(e), "value": e} for e in escolas
    ]
    return options


@app.callback(
    Output("dropdown-vacina-mapa", "options"),
    # Output("dropdown-vacina-mapa", "value"),
    [
        Input("dropdown-ano", "value"),
        Input("dropdown-tp-unidade", "value"),
        Input("select-escola-mapa", "value"),
        Input("dropdown-modalidade", "value"),
    ],
    # State("dropdown-vacina-mapa", "value"),
)
def update_vacina_options(ano, tipo_unidade, escola, modalidade):
    df = n_vacinas_escola.copy()
    if ano is not None:
        df = df[df["data_vacinacao_ano"] == ano]
    if tipo_unidade is not None and tipo_unidade != "Todas":
        df = df[df["tipo_unidade"] == tipo_unidade]
    if escola is not None and escola != "Todas":
        df = df[df["nome_unidade"] == escola]
    if modalidade is not None and modalidade != "Todas":
        df = df[df["modalidade"] == modalidade]

    vacinas = sorted(df["vacina"].unique())
    options = [{"label": "Todas", "value": "Todas"}] + [
        {"label": formatar_label(v), "value": v} for v in vacinas
    ]

    return options


@app.callback(
    Output("dropdown-modalidade", "options"),
    # Output("dropdown-modalidade", "value"),
    [
        Input("dropdown-ano", "value"),
        Input("dropdown-tp-unidade", "value"),
        Input("select-escola-mapa", "value"),
        Input("dropdown-vacina-mapa", "value"),
    ],
    # State("dropdown-modalidade", "value"),
)
def update_modalidade_options(ano, tipo_unidade, escola, vacina):
    df = n_vacinas_escola.copy()
    if ano is not None:
        df = df[df["data_vacinacao_ano"] == ano]
    if tipo_unidade is not None and tipo_unidade != "Todas":
        df = df[df["tipo_unidade"] == tipo_unidade]
    if escola is not None and escola != "Todas":
        df = df[df["nome_unidade"] == escola]
    if vacina is not None and vacina != "Todas":
        df = df[df["vacina"] == vacina]

    modalidades = sorted(df["modalidade"].dropna().unique())
    options = [{"label": "Todas", "value": "Todas"}] + [
        {"label": formatar_label(m), "value": m} for m in modalidades
    ]

    return options


@app.callback(
    Output("dropdown-tp-unidade", "options"),
    # Output("dropdown-tp-unidade", "value"),
    [
        Input("dropdown-ano", "value"),
        Input("dropdown-modalidade", "value"),
        Input("select-escola-mapa", "value"),
        Input("dropdown-vacina-mapa", "value"),
    ],
    # State("dropdown-tp-unidade", "value"),
)
def update_tipo_unidade_options(ano, modalidade, escola, vacina):
    df = n_vacinas_escola.copy()
    if ano is not None:
        df = df[df["data_vacinacao_ano"] == ano]
    if modalidade is not None and modalidade != "Todas":
        df = df[df["modalidade"] == modalidade]
    if escola is not None and escola != "Todas":
        df = df[df["nome_unidade"] == escola]
    if vacina is not None and vacina != "Todas":
        df = df[df["vacina"] == vacina]

    tipos = sorted(df["tipo_unidade"].dropna().unique())
    options = [{"label": "Todas", "value": "Todas"}] + [
        {"label": t, "value": t} for t in tipos
    ]

    return options


# callback para selecionar o tipo de unidade escolar
@app.callback(
    Output("mapa-vacinacao", "figure"),
    [
        Input("dropdown-tp-unidade", "value"),
        Input("dropdown-modalidade", "value"),
        Input("dropdown-ano", "value"),
        Input("dropdown-vacina-mapa", "value"),
        Input("select-escola-mapa", "value"),
    ],
)
def update_map(tipo_unidade, modalidade, ano_selecionado, vacina, escola):

    with open(SHP_FOLDER / "osasco.geojson", "r", encoding="utf-8") as f:
        osasco_geojson = json.load(f)

    # Filtro para mostrar todos os dados quando dropdown esvaziado (clear value)
    if tipo_unidade is None:
        tipo_unidade = "Todas"
    if vacina is None:
        vacina = "Todas"
    if escola is None:
        escola = "Todas"
    if modalidade is None:
        modalidade = "Todas"

    # Filtrar por ano
    df = n_vacinas_escola[n_vacinas_escola["data_vacinacao_ano"] == ano_selecionado]

    # Filtrar por tipo de unidade
    if tipo_unidade != "Todas":
        df = df[df["tipo_unidade"] == tipo_unidade]

    # Filtrar por vacina
    if vacina != "Todas":
        df = df[df["vacina"] == vacina]

    # Filtrar por escola
    if escola != "Todas":
        df = df[df["nome_unidade"] == escola]

    # Filtrar por modalidade
    if modalidade != "Todas":
        df = df[df["modalidade"] == modalidade]

    df_escola = df.groupby(["latitude", "longitude", "nome_unidade"], as_index=False)[
        "n_vacinas"
    ].sum()

    # Definir zoom da escola selecionada
    if escola != "Todas" and not df_escola.empty:
        lat = df_escola.iloc[0]["latitude"]
        lon = df_escola.iloc[0]["longitude"]
        center = dict(lat=lat, lon=lon)
        zoom = 13
    else:
        center = dict(lat=-23.5324, lon=-46.7916)
        zoom = 11

    mapa_osasco = px.scatter_map(
        df_escola,
        lat="latitude",
        lon="longitude",
        size="n_vacinas",
        hover_data={"nome_unidade": True, "n_vacinas": True, "latitude": False, "longitude": False},
        custom_data=["nome_unidade", "n_vacinas"],
        zoom=zoom,
        center=center,
        height=600,
        labels={"nome_unidade": "Nome da unidade:", "n_vacinas": "Número de vacinas"},
    )
    mapa_osasco.update_layout(
        map=dict(
            style="outdoors",
            center=center,
            zoom=zoom,
            layers=[
                dict(
                    sourcetype="geojson",
                    source=osasco_geojson,
                    type="fill",
                    color="rgba(0,0,255,0.2)",
                ),
                dict(
                    sourcetype="geojson",
                    source=osasco_geojson,
                    type="line",
                    color="blue",
                    line=dict(width=1),
                ),
            ],
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 60},
    )
    return mapa_osasco


if __name__ == "__main__":
    app.run(debug=True)
