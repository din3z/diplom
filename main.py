from flask import Flask, render_template, request, jsonify
import pandas as pd
import plotly.graph_objs as go
import threading
import time
import json
app = Flask(__name__)

def read_csv_data():
    # Чтение данных из CSV-файла
    df = pd.read_csv(r'C:\Users\SKHalitova\Desktop\KuberParser\out_cpu.csv')
    df.columns = ['name', 'ds', 'y']
    df['ds'] = pd.to_datetime(df['ds']).dt.strftime('%Y-%m-%d %H:%M:%S')
    data_sorted = df.sort_values(by='ds')

    # Идентификация уникальных метрик в первом столбце
    metrics = data_sorted['name'].unique()

    # Создание словаря для хранения данных графиков
    data_dict = {}

    # Создание отдельного графика для каждой метрики
    for metric in metrics:
        if metric != "redis-planeta-access-replicas-2":
            continue
        metric_data = data_sorted[data_sorted['name'] == metric]
        trace = go.Scatter(
            x=metric_data['ds'],
            y=metric_data['y']
        )
        # fig = go.Figure()
        # fig.add_trace(trace)
        data_dict[metric] = [trace]

    return data_dict


data_dict = read_csv_data()


def update_data():
    global data_dict
    while True:
        new_data = read_csv_data()
        data_dict = new_data
        time.sleep(15)

@app.route('/update_graph/<metric>')
def update_graph(metric):
    global data_dict
    if metric in data_dict:
        return jsonify(data=data_dict[metric][0]['y'], layout={})
    else:
        return jsonify(data=[], layout={})



@app.route('/')
def index():
    graphJSON = {}

    # Обновление данных графиков из словаря
    for metric, data in data_dict.items():
        layout = go.Layout(
            title=metric,
            xaxis=dict(title='Время'),
            yaxis=dict(title='Значение')
        )

        graph = go.Figure(data=data, layout=layout)
        graphJSON[metric] = graph.to_json()

    return render_template('index.html', graphJSON=graphJSON)

@app.route('/update_chart', methods=['POST'])
def update_chart():
    metric = request.form['metric']

    # Обновление данных графика для указанной метрики
    df = pd.read_csv(r'C:\Users\SKHalitova\Desktop\KuberParser\out_mem.csv')

    df.columns = ['name', 'ds', 'y']
    df['ds'] = pd.to_datetime(df['ds']).dt.strftime('%Y-%m-%d %H:%M:%S')
    df = df.sort_values(by='ds')


    metric_data = df[df['name'] == metric]
    trace = go.Scatter(
        x=metric_data['ds'],
        y=metric_data['y'],
        mode='lines+markers',
        name=metric
    )
    graph = go.Figure(data=[trace])
    graphJSON = graph.to_json()

    return json.dumps(graphJSON)





if __name__ == '__main__':
    data_update_thread = threading.Thread(target=update_data)
    data_update_thread.daemon = True
    data_update_thread.start()

    app.run(debug=True)