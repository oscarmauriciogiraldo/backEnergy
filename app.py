from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from matplotlib.ticker import FuncFormatter

app = Flask(__name__)
CORS(app)  # Habilitar CORS para todos los dominios

# Cargar los datos
file_path = "energy.csv"
df = pd.read_csv(file_path)

# Limpiar y preparar los datos
df.fillna(0, inplace=True)
df['Total'] = df.iloc[:, 2:-1].sum(axis=1)  # Calcular el total de energía por año

# Formateador para los ejes Y (en GWh)
def gwh_formatter(x, pos):
    return f'{x/1000:.0f}K' if x >= 1000 else f'{x:.0f}'

gwh_format = FuncFormatter(gwh_formatter)

# Función para crear gráficas en base64
def plot_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    image = base64.b64encode(buf.read()).decode('utf-8')
    return image

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({
        'data': df.to_dict(orient='records'),
        'columns': list(df.columns)
    })

@app.route('/api/energy_trend', methods=['GET'])
def energy_trend():
    # Gráfico de tendencia de todas las energías
    plt.figure(figsize=(12, 6))
    for column in df.columns[2:-2]:  # Excluir 'Units' y 'Total'
        if df[column].sum() > 0:  # Solo mostrar energías con datos
            plt.plot(df['year'], df[column], label=column, marker='o')
    
    plt.title('Evolución de la Producción de Energía por Fuente (1990-2023)')
    plt.xlabel('Año')
    plt.ylabel('Producción (GWh)')
    plt.gca().yaxis.set_major_formatter(gwh_format)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True)
    
    img = plot_to_base64(plt)
    plt.close()
    return jsonify({'image': f'data:image/png;base64,{img}'})

@app.route('/api/energy_composition', methods=['GET'])
def energy_composition():
    year = request.args.get('year', default=2023, type=int)
    
    if year not in df['year'].values:
        return jsonify({'error': 'Año no disponible'}), 404
    
    year_data = df[df['year'] == year].iloc[0]
    sources = df.columns[2:-2]
    values = [year_data[source] for source in sources]
    
    # Filtrar fuentes con valores > 0
    filtered = [(s, v) for s, v in zip(sources, values) if v > 0]
    sources_filtered, values_filtered = zip(*filtered) if filtered else ([], [])
    
    # Gráfico de composición
    plt.figure(figsize=(10, 10))
    if values_filtered:
        plt.pie(values_filtered, labels=sources_filtered, autopct='%1.1f%%', startangle=140)
        plt.title(f'Composición de la Producción de Energía en {year}')
    else:
        plt.text(0.5, 0.5, 'No hay datos disponibles', ha='center', va='center')
        plt.title(f'Datos no disponibles para {year}')
    
    img = plot_to_base64(plt)
    plt.close()
    return jsonify({
        'image': f'data:image/png;base64,{img}',
        'year': year,
        'sources': sources_filtered,
        'values': values_filtered
    })

@app.route('/api/renewable_vs_fossil', methods=['GET'])
def renewable_vs_fossil():
    # Clasificar las fuentes
    fossil = ['Coal', 'Oil', 'Natural gas']
    renewable = ['Biofuels', 'Hydro', 'Solar PV', 'Wind', 'Other sources']
    
    df_fossil = df[fossil].sum(axis=1)
    df_renewable = df[renewable].sum(axis=1)
    df_ratio = (df_renewable / (df_fossil + df_renewable)) * 100
    
    # Gráfico de comparación
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Gráfico de producción absoluta
    ax1.plot(df['year'], df_fossil, label='Fósiles', color='red', marker='o')
    ax1.plot(df['year'], df_renewable, label='Renovables', color='green', marker='o')
    ax1.fill_between(df['year'], df_fossil, alpha=0.2, color='red')
    ax1.fill_between(df['year'], df_renewable, alpha=0.2, color='green')
    ax1.set_title('Comparación de Energías Fósiles vs Renovables (1990-2023)')
    ax1.set_ylabel('Producción (GWh)')
    ax1.yaxis.set_major_formatter(gwh_format)
    ax1.legend()
    ax1.grid(True)
    
    # Gráfico de porcentaje renovable
    ax2.plot(df['year'], df_ratio, label='% Renovable', color='blue', marker='o')
    ax2.set_title('Porcentaje de Energía Renovable')
    ax2.set_xlabel('Año')
    ax2.set_ylabel('Porcentaje (%)')
    ax2.set_ylim(0, 100)
    ax2.grid(True)
    
    plt.tight_layout()
    
    img = plot_to_base64(fig)
    plt.close()
    return jsonify({'image': f'data:image/png;base64,{img}'})

@app.route('/api/top_sources', methods=['GET'])
def top_sources():
    n = request.args.get('n', default=5, type=int)
    # Calcular la media de cada fuente
    avg_production = df.iloc[:, 2:-2].mean().sort_values(ascending=False)
    top_sources = avg_production.head(n)
    
    # Gráfico de barras
    plt.figure(figsize=(10, 6))
    bars = plt.bar(top_sources.index, top_sources.values, color='skyblue')
    
    plt.title(f'Top {n} Fuentes de Energía (Promedio 1990-2023)')
    plt.ylabel('Producción Promedio (GWh)')
    plt.gca().yaxis.set_major_formatter(gwh_format)
    
    # Añadir valores en las barras
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                 f'{height/1000:.1f}K' if height >= 1000 else f'{height:.0f}',
                 ha='center', va='bottom')
    
    img = plot_to_base64(plt)
    plt.close()
    return jsonify({
        'image': f'data:image/png;base64,{img}',
        'top_sources': top_sources.to_dict()
    })

@app.route('/api/growth_comparison', methods=['GET'])
def growth_comparison():
    # Calcular crecimiento porcentual
    first_year = df.iloc[0]
    last_year = df.iloc[-1]
    
    growth = {}
    for source in df.columns[2:-2]:
        if first_year[source] > 0:  # Solo fuentes con datos iniciales
            growth[source] = ((last_year[source] - first_year[source]) / first_year[source]) * 100
    
    growth_series = pd.Series(growth).sort_values()
    
    # Gráfico de crecimiento
    plt.figure(figsize=(10, 6))
    colors = ['red' if x < 0 else 'green' for x in growth_series.values]
    bars = plt.barh(growth_series.index, growth_series.values, color=colors)
    
    plt.title('Crecimiento Porcentual de la Producción por Fuente (1990 vs 2023)')
    plt.xlabel('Crecimiento Porcentual (%)')
    plt.grid(axis='x')
    
    # Añadir valores en las barras
    for bar in bars:
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height()/2,
                 f'{width:.1f}%',
                 ha='left' if width > 0 else 'right', va='center')
    
    img = plot_to_base64(plt)
    plt.close()
    return jsonify({
        'image': f'data:image/png;base64,{img}',
        'growth_data': growth_series.to_dict()
    })

@app.route('/api/years_available', methods=['GET'])
def years_available():
    return jsonify({
        'years': sorted(df['year'].unique().tolist()),
        'min_year': int(df['year'].min()),
        'max_year': int(df['year'].max())
    })

if __name__ == '__main__':
    app.run(debug=True)