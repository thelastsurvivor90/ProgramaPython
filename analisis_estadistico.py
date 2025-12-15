"""
Sistema Integral de Análisis Estadístico con Generación Automática de Reportes LaTeX
Autor: Sistema de Análisis Estadístico
Descripción: Aplicación que lee CSV, genera tablas de frecuencias, gráficas estadísticas 
            y produce un documento LaTeX/PDF completo.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pylatex import Document, Section, Subsection, Table, Tabular, Figure, NoEscape, Package
from pylatex.utils import bold
import os
import sys
from pathlib import Path
import seaborn as sns

class AnalizadorEstadistico:
    """Clase principal para análisis estadístico y generación de reportes"""
    
    def __init__(self, ruta_csv, carpeta_salida="output"):
        """
        Inicializa el analizador estadístico
        
        Args:
            ruta_csv (str): Ruta al archivo CSV de entrada
            carpeta_salida (str): Carpeta donde se guardarán los resultados
        """
        self.ruta_csv = ruta_csv
        self.carpeta_salida = Path(carpeta_salida)
        self.carpeta_salida.mkdir(exist_ok=True)
        
        # Crear subcarpetas
        self.carpeta_imagenes = self.carpeta_salida / "imagenes"
        self.carpeta_imagenes.mkdir(exist_ok=True)
        
        self.df = None
        self.columna_numerica = None
        self.tabla_frecuencias = None
        
        # Configurar estilo de gráficas
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")
    
    def cargar_datos(self):
        """Carga el archivo CSV y valida los datos"""
        try:
            self.df = pd.read_csv(self.ruta_csv)
            print(f"✓ Datos cargados exitosamente: {len(self.df)} registros")
            print(f"  Columnas disponibles: {list(self.df.columns)}")
            
            # Seleccionar la primera columna numérica
            columnas_numericas = self.df.select_dtypes(include=[np.number]).columns
            if len(columnas_numericas) == 0:
                raise ValueError("No se encontraron columnas numéricas en el CSV")
            
            self.columna_numerica = columnas_numericas[0]
            print(f"  Analizando columna: '{self.columna_numerica}'")
            return True
            
        except Exception as e:
            print(f"✗ Error al cargar datos: {e}")
            return False
    
    def calcular_tabla_frecuencias(self, num_clases=None):
        """
        Genera la tabla de frecuencias completa
        
        Args:
            num_clases (int): Número de clases (opcional, se calcula automáticamente)
        """
        datos = self.df[self.columna_numerica].dropna()
        n = len(datos)
        
        # Calcular número de clases usando la regla de Sturges
        if num_clases is None:
            num_clases = int(np.ceil(1 + 3.322 * np.log10(n)))
        
        # Calcular intervalos
        min_val = datos.min()
        max_val = datos.max()
        rango = max_val - min_val
        amplitud = rango / num_clases
        
        # Crear intervalos
        intervalos = []
        limites_inferiores = []
        limites_superiores = []
        
        for i in range(num_clases):
            li = min_val + i * amplitud
            ls = min_val + (i + 1) * amplitud
            limites_inferiores.append(li)
            limites_superiores.append(ls)
            intervalos.append(f"[{li:.2f}, {ls:.2f})")
        
        # Calcular frecuencias
        frecuencias = []
        for i in range(num_clases):
            if i == num_clases - 1:
                freq = ((datos >= limites_inferiores[i]) & (datos <= limites_superiores[i])).sum()
            else:
                freq = ((datos >= limites_inferiores[i]) & (datos < limites_superiores[i])).sum()
            frecuencias.append(freq)
        
        # Crear tabla de frecuencias
        self.tabla_frecuencias = pd.DataFrame({
            'Intervalo': intervalos,
            'Límite Inferior': limites_inferiores,
            'Límite Superior': limites_superiores,
            'Marca de Clase': [(li + ls) / 2 for li, ls in zip(limites_inferiores, limites_superiores)],
            'Frecuencia Absoluta (fi)': frecuencias,
            'Frecuencia Relativa (hi)': [f / n for f in frecuencias],
            'Frecuencia Porcentual (%)': [f / n * 100 for f in frecuencias],
            'Frecuencia Acumulada (Fi)': np.cumsum(frecuencias),
            'Frecuencia Rel. Acumulada (Hi)': np.cumsum([f / n for f in frecuencias])
        })
        
        # Guardar tabla en CSV
        ruta_tabla = self.carpeta_salida / "tabla_frecuencias.csv"
        self.tabla_frecuencias.to_csv(ruta_tabla, index=False, float_format='%.4f')
        print(f"✓ Tabla de frecuencias generada: {ruta_tabla}")
        
        return self.tabla_frecuencias
    
    def generar_histograma(self):
        """Genera histograma de frecuencias"""
        plt.figure(figsize=(10, 6))
        
        # Crear histograma
        plt.bar(range(len(self.tabla_frecuencias)), 
                self.tabla_frecuencias['Frecuencia Absoluta (fi)'],
                width=0.8, edgecolor='black', alpha=0.7)
        
        plt.xlabel('Intervalos de Clase', fontsize=12, fontweight='bold')
        plt.ylabel('Frecuencia Absoluta', fontsize=12, fontweight='bold')
        plt.title(f'Histograma de Frecuencias - {self.columna_numerica}', 
                  fontsize=14, fontweight='bold')
        plt.xticks(range(len(self.tabla_frecuencias)), 
                   [f"C{i+1}" for i in range(len(self.tabla_frecuencias))], 
                   rotation=45)
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        ruta = self.carpeta_imagenes / "histograma.png"
        plt.savefig(ruta, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Histograma generado: {ruta}")
        return ruta
    
    def generar_poligono_frecuencias(self):
        """Genera polígono de frecuencias"""
        plt.figure(figsize=(10, 6))
        
        marcas = self.tabla_frecuencias['Marca de Clase']
        frecuencias = self.tabla_frecuencias['Frecuencia Absoluta (fi)']
        
        plt.plot(marcas, frecuencias, marker='o', linewidth=2, 
                markersize=8, color='#2E86AB', markerfacecolor='#A23B72')
        plt.fill_between(marcas, frecuencias, alpha=0.3, color='#2E86AB')
        
        plt.xlabel('Marca de Clase', fontsize=12, fontweight='bold')
        plt.ylabel('Frecuencia Absoluta', fontsize=12, fontweight='bold')
        plt.title(f'Polígono de Frecuencias - {self.columna_numerica}', 
                  fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        ruta = self.carpeta_imagenes / "poligono_frecuencias.png"
        plt.savefig(ruta, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Polígono de frecuencias generado: {ruta}")
        return ruta
    
    def generar_ojiva(self):
        """Genera ojiva (polígono de frecuencias acumuladas)"""
        plt.figure(figsize=(10, 6))
        
        limites_superiores = self.tabla_frecuencias['Límite Superior']
        frecuencias_acum = self.tabla_frecuencias['Frecuencia Acumulada (Fi)']
        
        # Agregar punto inicial (0, 0)
        x_vals = [self.tabla_frecuencias['Límite Inferior'].iloc[0]] + list(limites_superiores)
        y_vals = [0] + list(frecuencias_acum)
        
        plt.plot(x_vals, y_vals, marker='o', linewidth=2, 
                markersize=8, color='#F18F01', markerfacecolor='#C73E1D')
        plt.fill_between(x_vals, y_vals, alpha=0.3, color='#F18F01')
        
        plt.xlabel('Límite Superior de Clase', fontsize=12, fontweight='bold')
        plt.ylabel('Frecuencia Acumulada', fontsize=12, fontweight='bold')
        plt.title(f'Ojiva (Frecuencias Acumuladas) - {self.columna_numerica}', 
                  fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        ruta = self.carpeta_imagenes / "ojiva.png"
        plt.savefig(ruta, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Ojiva generada: {ruta}")
        return ruta
    
    def generar_grafico_torta(self):
        """Genera gráfico de torta (pastel)"""
        plt.figure(figsize=(10, 8))
        
        # Usar los 5 intervalos más frecuentes para mejor visualización
        top_intervals = self.tabla_frecuencias.nlargest(5, 'Frecuencia Absoluta (fi)')
        otros = self.tabla_frecuencias['Frecuencia Absoluta (fi)'].sum() - top_intervals['Frecuencia Absoluta (fi)'].sum()
        
        if otros > 0:
            labels = list(top_intervals['Intervalo']) + ['Otros']
            sizes = list(top_intervals['Frecuencia Absoluta (fi)']) + [otros]
        else:
            labels = list(self.tabla_frecuencias['Intervalo'])
            sizes = list(self.tabla_frecuencias['Frecuencia Absoluta (fi)'])
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(sizes)))
        explode = [0.05] * len(sizes)
        
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                colors=colors, explode=explode, shadow=True)
        plt.title(f'Distribución Porcentual - {self.columna_numerica}', 
                  fontsize=14, fontweight='bold', pad=20)
        plt.axis('equal')
        plt.tight_layout()
        
        ruta = self.carpeta_imagenes / "grafico_torta.png"
        plt.savefig(ruta, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Gráfico de torta generado: {ruta}")
        return ruta
    
    def generar_grafico_barras(self):
        """Genera gráfico de barras"""
        plt.figure(figsize=(12, 6))
        
        x_pos = np.arange(len(self.tabla_frecuencias))
        frecuencias = self.tabla_frecuencias['Frecuencia Absoluta (fi)']
        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(frecuencias)))
        
        bars = plt.bar(x_pos, frecuencias, color=colors, edgecolor='black', linewidth=1.5)
        
        # Agregar valores sobre las barras
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom', fontweight='bold')
        
        plt.xlabel('Intervalos', fontsize=12, fontweight='bold')
        plt.ylabel('Frecuencia Absoluta', fontsize=12, fontweight='bold')
        plt.title(f'Gráfico de Barras - {self.columna_numerica}', 
                  fontsize=14, fontweight='bold')
        plt.xticks(x_pos, [f"Clase {i+1}" for i in range(len(self.tabla_frecuencias))], 
                   rotation=45, ha='right')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        ruta = self.carpeta_imagenes / "grafico_barras.png"
        plt.savefig(ruta, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Gráfico de barras generado: {ruta}")
        return ruta
    
    def calcular_estadisticas_descriptivas(self):
        """Calcula estadísticas descriptivas básicas"""
        datos = self.df[self.columna_numerica].dropna()
        
        stats = {
            'Media': datos.mean(),
            'Mediana': datos.median(),
            'Moda': datos.mode().iloc[0] if len(datos.mode()) > 0 else datos.mean(),
            'Desviación Estándar': datos.std(),
            'Varianza': datos.var(),
            'Mínimo': datos.min(),
            'Máximo': datos.max(),
            'Rango': datos.max() - datos.min(),
            'Q1 (Cuartil 1)': datos.quantile(0.25),
            'Q2 (Mediana)': datos.quantile(0.50),
            'Q3 (Cuartil 3)': datos.quantile(0.75),
            'IQR': datos.quantile(0.75) - datos.quantile(0.25)
        }
        
        return stats
    
    def generar_documento_latex(self):
        """Genera el documento LaTeX completo con todos los elementos"""
        
        # Configuración del documento
        geometry_options = {"margin": "2cm", "top": "2.5cm"}
        doc = Document(geometry_options=geometry_options)
        
        # Paquetes adicionales
        doc.packages.append(Package('babel', options=['spanish']))
        doc.packages.append(Package('float'))
        doc.packages.append(Package('graphicx'))
        doc.packages.append(Package('booktabs'))
        doc.packages.append(Package('xcolor', options=['table']))
        doc.packages.append(Package('amsmath'))
        
        # Título
        doc.preamble.append(NoEscape(r'\title{Análisis Estadístico Completo}'))
        doc.preamble.append(NoEscape(r'\author{Sistema de Análisis Estadístico}'))
        doc.preamble.append(NoEscape(r'\date{\today}'))
        doc.append(NoEscape(r'\maketitle'))
        doc.append(NoEscape(r'\tableofcontents'))
        doc.append(NoEscape(r'\newpage'))
        
        # Sección 1: Introducción
        with doc.create(Section('Introducción')):
            doc.append('Este documento presenta un análisis estadístico completo de los datos proporcionados. ')
            doc.append(f'Se analizaron {len(self.df)} registros de la variable ')
            doc.append(bold(f'"{self.columna_numerica}"'))
            doc.append('. El análisis incluye tablas de frecuencias, medidas de tendencia central, ')
            doc.append('medidas de dispersión y representaciones gráficas diversas.')
        
        # Sección 2: Tabla de Frecuencias
        with doc.create(Section('Tabla de Frecuencias')):
            doc.append('A continuación se presenta la tabla de frecuencias completa con intervalos de clase, ')
            doc.append('frecuencias absolutas, relativas, porcentuales y acumuladas.')
            doc.append(NoEscape(r'\vspace{0.5cm}'))
            
            # Crear tabla LaTeX
            with doc.create(Table(position='H')) as table:
                table.add_caption('Distribución de Frecuencias')
                
                # Preparar datos para la tabla (primera parte)
                with doc.create(Tabular('|c|c|c|c|c|')) as tabular:
                    tabular.add_hline()
                    tabular.add_row(['Intervalo', 'Marca', 'Frec. Abs.', 'Frec. Rel.', 'Frec. %'])
                    tabular.add_hline()
                    
                    for _, row in self.tabla_frecuencias.iterrows():
                        tabular.add_row([
                            row['Intervalo'],
                            f"{row['Marca de Clase']:.2f}",
                            int(row['Frecuencia Absoluta (fi)']),
                            f"{row['Frecuencia Relativa (hi)']:.4f}",
                            f"{row['Frecuencia Porcentual (%)']:.2f}"
                        ])
                    tabular.add_hline()
            
            doc.append(NoEscape(r'\vspace{0.3cm}'))
            
            # Segunda tabla con frecuencias acumuladas
            with doc.create(Table(position='H')) as table:
                table.add_caption('Frecuencias Acumuladas')
                
                with doc.create(Tabular('|c|c|c|')) as tabular:
                    tabular.add_hline()
                    tabular.add_row(['Intervalo', 'Frec. Acum.', 'Frec. Rel. Acum.'])
                    tabular.add_hline()
                    
                    for _, row in self.tabla_frecuencias.iterrows():
                        tabular.add_row([
                            row['Intervalo'],
                            int(row['Frecuencia Acumulada (Fi)']),
                            f"{row['Frecuencia Rel. Acumulada (Hi)']:.4f}"
                        ])
                    tabular.add_hline()
        
        # Sección 3: Estadísticas Descriptivas
        with doc.create(Section('Estadísticas Descriptivas')):
            stats = self.calcular_estadisticas_descriptivas()
            
            doc.append('Las medidas de tendencia central y dispersión se presentan a continuación:')
            doc.append(NoEscape(r'\vspace{0.5cm}'))
            
            with doc.create(Subsection('Medidas de Tendencia Central')):
                doc.append(NoEscape(r'\begin{itemize}'))
                doc.append(NoEscape(f"\\item Media aritmética: $\\bar{{x}} = {stats['Media']:.4f}$"))
                doc.append(NoEscape(f"\\item Mediana: $Me = {stats['Mediana']:.4f}$"))
                doc.append(NoEscape(f"\\item Moda: $Mo = {stats['Moda']:.4f}$"))
                doc.append(NoEscape(r'\end{itemize}'))
            
            with doc.create(Subsection('Medidas de Dispersión')):
                doc.append(NoEscape(r'\begin{itemize}'))
                doc.append(NoEscape(f"\\item Desviación estándar: $s = {stats['Desviación Estándar']:.4f}$"))
                doc.append(NoEscape(f"\\item Varianza: $s^2 = {stats['Varianza']:.4f}$"))
                doc.append(NoEscape(f"\\item Rango: $R = {stats['Rango']:.4f}$"))
                doc.append(NoEscape(f"\\item Rango intercuartílico: $IQR = {stats['IQR']:.4f}$"))
                doc.append(NoEscape(r'\end{itemize}'))
            
            with doc.create(Subsection('Valores Extremos y Cuartiles')):
                doc.append(NoEscape(r'\begin{itemize}'))
                doc.append(NoEscape(f"\\item Valor mínimo: ${stats['Mínimo']:.4f}$"))
                doc.append(NoEscape(f"\\item Primer cuartil (Q1): ${stats['Q1 (Cuartil 1)']:.4f}$"))
                doc.append(NoEscape(f"\\item Segundo cuartil (Q2/Mediana): ${stats['Q2 (Mediana)']:.4f}$"))
                doc.append(NoEscape(f"\\item Tercer cuartil (Q3): ${stats['Q3 (Cuartil 3)']:.4f}$"))
                doc.append(NoEscape(f"\\item Valor máximo: ${stats['Máximo']:.4f}$"))
                doc.append(NoEscape(r'\end{itemize}'))
        
        # Sección 4: Representaciones Gráficas
        with doc.create(Section('Representaciones Gráficas')):
            
            # Histograma
            with doc.create(Subsection('Histograma de Frecuencias')):
                doc.append('El histograma muestra la distribución de frecuencias absolutas por intervalos de clase.')
                with doc.create(Figure(position='H')) as fig:
                    fig.add_image(str(self.carpeta_imagenes / "histograma.png"), width='0.8\\textwidth')
                    fig.add_caption('Histograma de frecuencias')
            
            # Polígono de Frecuencias
            with doc.create(Subsection('Polígono de Frecuencias')):
                doc.append('El polígono de frecuencias conecta las marcas de clase con sus respectivas frecuencias.')
                with doc.create(Figure(position='H')) as fig:
                    fig.add_image(str(self.carpeta_imagenes / "poligono_frecuencias.png"), width='0.8\\textwidth')
                    fig.add_caption('Polígono de frecuencias')
            
            # Ojiva
            with doc.create(Subsection('Ojiva (Frecuencias Acumuladas)')):
                doc.append('La ojiva representa gráficamente las frecuencias acumuladas.')
                with doc.create(Figure(position='H')) as fig:
                    fig.add_image(str(self.carpeta_imagenes / "ojiva.png"), width='0.8\\textwidth')
                    fig.add_caption('Ojiva - Frecuencias acumuladas')
            
            # Gráfico de Torta
            with doc.create(Subsection('Gráfico de Torta')):
                doc.append('El gráfico de torta muestra la distribución porcentual de los datos.')
                with doc.create(Figure(position='H')) as fig:
                    fig.add_image(str(self.carpeta_imagenes / "grafico_torta.png"), width='0.8\\textwidth')
                    fig.add_caption('Distribución porcentual')
            
            # Gráfico de Barras
            with doc.create(Subsection('Gráfico de Barras')):
                doc.append('El gráfico de barras presenta las frecuencias absolutas de forma visual.')
                with doc.create(Figure(position='H')) as fig:
                    fig.add_image(str(self.carpeta_imagenes / "grafico_barras.png"), width='0.85\\textwidth')
                    fig.add_caption('Gráfico de barras')
        
        # Sección 5: Conclusiones
        with doc.create(Section('Conclusiones')):
            doc.append(f'El análisis estadístico de la variable "{self.columna_numerica}" revela las siguientes características:')
            doc.append(NoEscape(r'\begin{enumerate}'))
            doc.append(NoEscape(f"\\item La distribución tiene una media de {stats['Media']:.2f} y una desviación estándar de {stats['Desviación Estándar']:.2f}."))
            doc.append(NoEscape(f"\\item Los valores oscilan entre {stats['Mínimo']:.2f} y {stats['Máximo']:.2f}, con un rango de {stats['Rango']:.2f}."))
            doc.append(NoEscape(f"\\item El coeficiente de variación es {(stats['Desviación Estándar']/stats['Media']*100):.2f}\\%, lo que indica {'baja' if (stats['Desviación Estándar']/stats['Media']*100) < 20 else 'moderada' if (stats['Desviación Estándar']/stats['Media']*100) < 40 else 'alta'} dispersión relativa."))
            doc.append(NoEscape(r'\end{enumerate}'))
        
        # Generar archivos
        nombre_base = 'reporte_estadistico'
        ruta_tex = self.carpeta_salida / nombre_base
        
        try:
            doc.generate_tex(str(ruta_tex))
            print(f"✓ Documento LaTeX generado: {ruta_tex}.tex")
            
            # Compilar a PDF
            doc.generate_pdf(str(ruta_tex), clean_tex=False, compiler='pdflatex')
            print(f"✓ Documento PDF generado: {ruta_tex}.pdf")
            
            return f"{ruta_tex}.pdf"
        except Exception as e:
            print(f"✗ Error al generar PDF: {e}")
            print("  Archivo .tex generado correctamente, pero la compilación falló.")
            print("  Puedes compilar manualmente el archivo .tex con un compilador LaTeX.")
            return f"{ruta_tex}.tex"
    
    def ejecutar_analisis_completo(self):
        """Ejecuta el análisis completo: carga, procesa, gráfica y documenta"""
        print("\n" + "="*70)
        print("SISTEMA DE ANÁLISIS ESTADÍSTICO Y GENERACIÓN DE REPORTES")
        print("="*70 + "\n")
        
        # 1. Cargar datos
        print("[1/7] Cargando datos...")
        if not self.cargar_datos():
            return False
        
        # 2. Calcular tabla de frecuencias
        print("\n[2/7] Calculando tabla de frecuencias...")
        self.calcular_tabla_frecuencias()
        
        # 3-7. Generar gráficas
        print("\n[3/7] Generando histograma...")
        self.generar_histograma()
        
        print("\n[4/7] Generando polígono de frecuencias...")
        self.generar_poligono_frecuencias()
        
        print("\n[5/7] Generando ojiva...")
        self.generar_ojiva()
        
        print("\n[6/7] Generando gráfico de torta...")
        self.generar_grafico_torta()
        
        print("\n[7/7] Generando gráfico de barras...")
        self.generar_grafico_barras()
        
        # 8. Generar documento LaTeX y PDF
        print("\n[FINAL] Generando documento LaTeX y PDF...")
        ruta_documento = self.generar_documento_latex()
        
        print("\n" + "="*70)
        print("ANÁLISIS COMPLETADO EXITOSAMENTE")
        print("="*70)
        print(f"\nResultados guardados en: {self.carpeta_salida.absolute()}")
        print(f"  • Tabla de frecuencias: tabla_frecuencias.csv")
        print(f"  • Gráficas: carpeta 'imagenes/'")
        print(f"  • Documento final: {Path(ruta_documento).name}")
        print("\n" + "="*70 + "\n")
        
        return True


def main():
    """Función principal de ejecución"""
    
    print("\n" + "="*70)
    print("BIENVENIDO AL SISTEMA DE ANÁLISIS ESTADÍSTICO")
    print("="*70 + "\n")
    
    # Solicitar archivo CSV
    if len(sys.argv) > 1:
        ruta_csv = sys.argv[1]
    else:
        print("Ingrese la ruta del archivo CSV a analizar:")
        print("(Ejemplo: datos.csv o ruta/completa/datos.csv)")
        ruta_csv = input("\nRuta del archivo: ").strip()
    
    # Validar que el archivo existe
    if not os.path.exists(ruta_csv):
        print(f"\n✗ Error: El archivo '{ruta_csv}' no existe.")
        print("  Asegúrese de que la ruta sea correcta.\n")
        return
    
    # Crear analizador y ejecutar
    analizador = AnalizadorEstadistico(ruta_csv)
    analizador.ejecutar_analisis_completo()


if __name__ == "__main__":
    main()
