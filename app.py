from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import io
import base64
from matplotlib.ticker import FuncFormatter

matplotlib.use("agg")

app = Flask(__name__)
CORS(app)


# *Cargar y leer datos
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
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')



@app.route('/api/renewable_vs_fossil', methods=['GET'])
def renewable_vs_fossil():
    # Clasificar las fuentes
    fossil = ['Coal', 'Oil', 'Natural gas']
    renewable = ['Biofuels', 'Hydro', 'Solar PV', 'Wind', 'Other sources']
    
    df_fossil = df[fossil].sum(axis=1)
    df_renewable = df[renewable].sum(axis=1)
    
    # Gráfico de comparación
    plt.figure(figsize=(12, 6))
    plt.plot(df['year'], df_fossil, label='Fósiles', color='red', marker='o')
    plt.plot(df['year'], df_renewable, label='Renovables', color='green', marker='o')
    plt.fill_between(df['year'], df_fossil, alpha=0.2, color='red')
    plt.fill_between(df['year'], df_renewable, alpha=0.2, color='green')
    
    plt.title('Comparación de Energías Fósiles vs Renovables (1990-2023)')
    plt.xlabel('Año')
    plt.ylabel('Producción (GWh)')
    plt.gca().yaxis.set_major_formatter(gwh_format)
    plt.legend()
    plt.grid(True)
    
    img = plot_to_base64(plt)
    plt.close()
    return jsonify({'image': f'data:image/png;base64,{img}'})

if __name__ == '__main__':
    app.run(debug = True)