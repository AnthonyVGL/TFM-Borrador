# -*- coding: utf-8 -*-
"""14MBID_TFM_Anthony_Valerio_Gomez_Lizana.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1xWqpZ7eCsGnLg08AgmYdv60cufGGY2jk

# <center>T-068 Control de Calidad Agroalimentario: Análisis Predictivo en Uvas a Diferentes Puntos de Madurez

**Nombre y apellidos:** Anthony Valerio Gomez Lizana

**Usuario VIU:** anthonyvalerio.gomez (anthonyvalerio.gomez@student.universidadviu.com)

---
# Comprensión de Datos
---

Importamos las bibliotecas a utilizar
"""

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.model_selection import cross_val_score
from scipy.cluster import hierarchy
from scipy.signal import savgol_filter
from scipy import stats

"""Se sube los archivos csv al local de google colab, donde los datos del espectrómetro y calidad se guarda con los nombres matriz_x y matriz_y respectivamente."""

# Lee los archivos CSV
matriz_x = pd.read_csv('/content/MatrizX_Uva.csv')  # Datos del espectrómetro
matriz_y = pd.read_csv('/content/MatrizY_Uva.csv', delimiter=';')  # Valores de Brix y pH

"""Se muestra el contenido del archivo matriz_y"""

# Imprimir la cantidad de filas y columnas
print(f"Cantidad de filas y columnas en matriz_y: {matriz_y.shape[0]} filas, {matriz_y.shape[1]} columnas")

# Mostrar las primeras filas del DataFrame
matriz_y.head()

"""Se modifica el nombre de la primera columna para un manejo adecuado"""

matriz_y = matriz_y.rename(columns={"º Brix": "Brix"})
print(matriz_y.shape)
matriz_y.head()

"""Se muestra el archivo matriz_x"""

# Imprimir la cantidad de filas y columnas
print(f"Cantidad de filas y columnas en matriz_x: {matriz_x.shape[0]} filas, {matriz_x.shape[1]} columnas")

# Mostrar las primeras 15 filas del DataFrame
matriz_x.head(15)

"""El dataset matriz_x necesita darle forma para una estructura adecuada, para ello se eliminará las filas con información innecesaria y se adaptará de la siguiente forma"""

# Elimina las primeras 6 filas
matriz_x = matriz_x.drop(matriz_x.index[:6])

# Se llena los valores de la primera fila con los de la segunda donde sean NaN
matriz_x.iloc[0] = matriz_x.iloc[0].combine_first(matriz_x.iloc[1])

# Se elimina la fila con indice 1
matriz_x = matriz_x.drop(matriz_x.index[1])
matriz_x = matriz_x.drop(matriz_x.index[1])

# Elimina la primera columna
matriz_x = matriz_x.drop(matriz_x.columns[0], axis=1)

# Elimina la última columna
matriz_x = matriz_x.drop(matriz_x.columns[-1], axis=1)

# Restablece la fila 7 (índice 0) como los títulos de las columnas
matriz_x.columns = matriz_x.iloc[0]

# Resetea los índices para evitar saltos en la numeración
matriz_x = matriz_x.reset_index(drop=True)

# Elimina la fila duplicada en el indice 0
matriz_x = matriz_x.drop(matriz_x.index[0])

# Verifica el resultado
matriz_x.head()

"""Teniendo la estructura adecuada observamos que entre las variables esta el analysis date, esta variable se modificará el formato para obtener dos columnas extras una de fecha y otra que contabilizará el número de días según la columna Sample teniendo como referencia siempre la primera Fecha a contabilizar y las demás del mismo Sample se contarán los días."""

# Función para agregar el 0 faltante al año
def corregir_fecha(fecha):
    if fecha.startswith('021'):
        fecha = '2021' + fecha[3:]
    return fecha

# Aplicar la corrección a la columna 'analysis date'
matriz_x['analysis date corregido'] = matriz_x['analysis date'].apply(corregir_fecha)

# Convertir la columna corregida a datetime
matriz_x['analysis date corregido'] = pd.to_datetime(matriz_x['analysis date corregido'], format='%Y-%m-%dT%H-%M-%S')

# Convertir al formato deseado dd/mm/yyyy
matriz_x['Fecha'] = matriz_x['analysis date corregido'].dt.strftime('%d/%m/%Y')

# Eliminar la columna 'analysis date corregido'
matriz_x = matriz_x.drop(columns=["analysis date corregido"])

# Eliminar las columnas no necesarias
matriz_x = matriz_x.drop(columns=["sample name", "Time Index", "Replicate"])

# Mover la columna 'Fecha' al lado de 'analysis date'
matriz_x.insert(2, "Fecha", matriz_x.pop("Fecha"))

# Asegurarnos de que la columna 'Fecha' está en formato datetime
matriz_x['Fecha'] = pd.to_datetime(matriz_x['Fecha'], format='%d/%m/%Y')

# Calcular la columna 'Días' tomando la primera fecha de cada muestra como referencia
matriz_x['Días'] = matriz_x.groupby('Sample')['Fecha'].transform(lambda x: (x - x.min()).dt.days)

# Insertar la columna "Días" en la posición 3
matriz_x.insert(3, "Días", matriz_x.pop("Días"))

# Renombrar la columna "type of fermentation" a "Tipo de uva"
matriz_x.rename(columns={"type of fermentation": "Tipo de uva"}, inplace=True)

# Mostrar las primeras filas para verificar
matriz_x.head()

"""Ahora se elimina las columnas que no aportarán valor como el analysis date, Fecha y Subfile Index"""

# Eliminar las columnas 'analysis date', 'Subfile Index', 'Fecha' y 'Sampling time'
matriz_x = matriz_x.drop(columns=['analysis date', 'Subfile Index', 'Fecha', 'Sampling time'])

# Reiniciar el índice
matriz_x.reset_index(drop=True, inplace=True)

# Verificar que las columnas se hayan eliminado correctamente
matriz_x.head()

"""Ahora el dataset matriz_x contiene las variables y una estructura adecuadas para el análisis, además de estar compuesta por las siguientes variables
*   Full name = Codificación al unir Sample, Samplin time, Replicate y analysis date
*   Días = La cantidad de días de cada Sample considerando la primera fecha como 0.
*   Sample = Es la muestra tomada del tipo de uva siendo la primera o segunda muestra con dichas características.
*   Tipo de uva = Tipo de uva con las siguientes nomenclaturas:

  M = Variedad, A=Arriba, M=Medio y B=Bajo.

  La primera letra M es de variedad Moscatel de Alejandría.

  La segunda letra indica la posición de la Viña en donde se tiene la medida de la uva sea A, M o B.

  La tercera letra indica la posición de racismo de uva dentro de la planta sea A, M o B.

A partir de la columna Sample se muestra los distintos números de onda (cm-1)

Identificación de valores nulos o faltantes de cada matriz
"""

# Para matriz_x
nulos_x = matriz_x.isnull().sum()
print("Valores nulos en matriz_x:")
print(nulos_x[nulos_x > 0])

# Para matriz_y
if isinstance(matriz_y, pd.DataFrame):
    nulos_y = matriz_y.isnull().sum()
    print("Valores nulos en matriz_y:")
    print(nulos_y[nulos_y > 0])

"""Se observa en el resultado es 0 en cada matriz por lo que los datasets tienen completa su información

Ahora identificaremos los outliers de la matriz_y
"""

# Configurar el estilo de los gráficos
sns.set(style="whitegrid")

# Crear una figura con dos gráficos de boxplot (uno para cada variable)
fig, ax = plt.subplots(1, 2, figsize=(12, 6))

# Graficar boxplot para la columna 'Brix'
sns.boxplot(data=matriz_y['Brix'], ax=ax[0])
ax[0].set_title('Boxplot de Brix')
ax[0].set_ylabel('Valor de Brix')

# Graficar boxplot para la columna 'pH'
sns.boxplot(data=matriz_y['pH'], ax=ax[1])
ax[1].set_title('Boxplot de pH')
ax[1].set_ylabel('Valor de pH')

# Mostrar los gráficos
plt.tight_layout()
plt.show()

# Identificar y mostrar los valores de outliers en cada columna
def identificar_outliers(df, columna):
    Q1 = df[columna].quantile(0.25)  # Primer cuartil
    Q3 = df[columna].quantile(0.75)  # Tercer cuartil
    IQR = Q3 - Q1  # Rango intercuartílico

    # Limites para identificar outliers
    limite_inferior = Q1 - 1.5 * IQR
    limite_superior = Q3 + 1.5 * IQR

    # Filtrar outliers
    outliers = df[(df[columna] < limite_inferior) | (df[columna] > limite_superior)]
    return outliers[columna]

def identificar_outliers_index(df, columna):
    Q1 = df[columna].quantile(0.25)  # Primer cuartil
    Q3 = df[columna].quantile(0.75)  # Tercer cuartil
    IQR = Q3 - Q1  # Rango intercuartílico

    # Limites para identificar outliers
    limite_inferior = Q1 - 1.5 * IQR
    limite_superior = Q3 + 1.5 * IQR

    # Filtrar outliers
    outliers_indices = df[(df[columna] < limite_inferior) | (df[columna] > limite_superior)].index
    return outliers_indices

# Identificar y mostrar outliers
outliers_brix = identificar_outliers(matriz_y, 'Brix')
outliers_ph = identificar_outliers(matriz_y, 'pH')

# Identificar los indices de los outliers en Brix y pH
indices_outliers_brix = identificar_outliers_index(matriz_y, 'Brix')
indices_outliers_ph = identificar_outliers_index(matriz_y, 'pH')

print("Outliers en la columna Brix:", outliers_brix)

print("\nOutliers en la columna pH:", outliers_ph)

"""Se visualizar que existe 1 caso de outliers en la gráfica de boxplot para la columnas Brix y pH, siendo los valores 12.9 en la posición 9 y 2.87 en la posición 0 respectivamente.

Los resultados de los outliers se encuentran dentro de los valores establecidos en los indicadores de Brix y pH, por lo que se conservarán para que puedan aportar información útil al modelo.

Ahora se grafica las muestras en todos los espectros para analizar la matriz_x
"""

espectros = matriz_x.iloc[:, 7:]  # Todas las filas y columnas a partir de la 7
numeros_onda = matriz_x.columns[7:]  # Los nombres de las columnas de números de onda

# Graficamos los espectros de todas las filas
plt.figure(figsize=(12, 8))

# Iteramos sobre todas las filas
for i in range(espectros.shape[0]):
    plt.plot(numeros_onda, espectros.iloc[i, :], label=f'Fila {i+1}')  # Graficamos cada fila

# Configuramos el gráfico
plt.title('Espectros de todas las filas de matriz_x')
plt.xlabel('Números de onda (cm-1)')
plt.ylabel('Intensidad')
plt.grid(True)
plt.tight_layout()
plt.show()

"""Se observa que los valores no se encuentran tan distantes entre sí, lo que da indicios a que no exista valores de outliers en la matriz_x, la diferencia más notoría se centra entre los números de onda entre (900, 1500) y (3200, 3400), se realizará el gráfico en ese rango para visualizar mejor el comportamiento de los datos."""

# Filtramos los números de onda en los rangos deseados
rango_espectros_1 = (numeros_onda >= 900) & (numeros_onda <= 1500)
rango_espectros_2 = (numeros_onda >= 3200) & (numeros_onda <= 3400)

# Espectros filtrados para cada rango
espectros_filtrados_1 = espectros.loc[:, rango_espectros_1]
espectros_filtrados_2 = espectros.loc[:, rango_espectros_2]

numeros_onda_filtrados_1 = numeros_onda[rango_espectros_1]  # Números de onda filtrados para el primer rango
numeros_onda_filtrados_2 = numeros_onda[rango_espectros_2]  # Números de onda filtrados para el segundo rango

# Graficamos los espectros de todas las filas en el primer rango
plt.figure(figsize=(12, 6))
for i in range(espectros_filtrados_1.shape[0]):
    plt.plot(numeros_onda_filtrados_1, espectros_filtrados_1.iloc[i, :], label=f'Fila {i+1}')  # Graficamos cada fila
plt.title('Espectros de todas las filas de matriz_x (900-1500 cm-1)')
plt.xlabel('Números de onda (cm-1)')
plt.ylabel('Intensidad')
plt.grid(True)
plt.tight_layout()
plt.show()

# Graficamos los espectros de todas las filas en el segundo rango
plt.figure(figsize=(12, 6))
for i in range(espectros_filtrados_2.shape[0]):
    plt.plot(numeros_onda_filtrados_2, espectros_filtrados_2.iloc[i, :], label=f'Fila {i+1}')  # Graficamos cada fila
plt.title('Espectros de todas las filas de matriz_x (3200-3400 cm-1)')
plt.xlabel('Números de onda (cm-1)')
plt.ylabel('Intensidad')
plt.grid(True)
plt.tight_layout()
plt.show()

"""Todas las muestran siguen el mismo patrón, casi ni parece cruzarse entre sí, es un indicio de que en estos niveles de números de onda captan mayor la variabilidad de las muestras entre sí.

----
# Selección de Variables
----

Se tiene como finalidad realizar los modelos con los datos de la espectroscopia, pero para un mayor nivel de entrenamiento se realizará las siguiente prueba para considerar nuevas variables de los datos.

Ahora se graficará un mapa de calor considerando solo las variables de Horas y tipo de uva en relación al Brix y pH, para identificar si guardan algún tipo de relación y poder implementarlas al modelo de Machine Learning
"""

# Preparar los datos a partir de 'matriz_x' (Días, Tipo de uva)
X_datos = matriz_x[['Días', 'Tipo de uva']].copy()

# Extraer los caracteres específicos de 'Tipo de uva'
X_datos['Viña'] = X_datos['Tipo de uva'].str[-2]  # Segundo carácter desde el final (representa Viña)
X_datos['Racimo'] = X_datos['Tipo de uva'].str[-1]  # Último carácter (representa Racimo)

# Convertir las categorías de 'Viña' y 'Racimo'' en variables dummy
X_datos = pd.get_dummies(X_datos, columns=['Viña', 'Racimo'], drop_first=False)

# Eliminar las columnas originales no numéricas 'Tipo de uva'
X_datos = X_datos.drop(columns=['Tipo de uva'])

# Agregar las variables objetivo (Brix y pH) desde 'matriz_y'
X_datos['Brix'] = matriz_y['Brix']
X_datos['pH'] = matriz_y['pH']

# Calcular la matriz de correlación
correlacion = X_datos.corr()

# Visualizar el mapa de calor
plt.figure(figsize=(10, 8))
sns.heatmap(correlacion, annot=True, cmap='coolwarm', fmt='.2f', linewidths=0.5)
plt.title('Mapa de calor de correlaciones entre Días,Tipo de uva, Brix y pH')
plt.show()

"""Resultados del mapa de calor demuestran los siguiente:

Para el Brix la variable más significativa es Días siguiendo de Viña_B (Posición de la Viña Baja) y Viña_A (Posición de la viña Alta).

Para el pH la variable más significativa es Días, siguiendo de Racimo_B (Posición del racimo Bajo) y Racimo_A (Posición del racimo Alto).

Existe una relación significativa entre las variables a predecir entre sí el Brix y el pH siendo estos valores de Matriz_y.

Por lo tanto, se concluye que las nuevas variables de entrada a sumar de la espectroscopía serán los Días y Tipo de uva para el entrenamiento de los modelos.

---
# Entrenamiento
---

Se plantea usar todos los datos posibles que tengan algún tipo de relación con los valores a predecir Brix y pH.

Para el tratamiento de preparar los datos se usarán todas las variables de espectros y se considerará las variables Días y Tipo de uva.
"""

# Preparar los datos
X_completo = pd.concat([espectros, matriz_x[['Días', 'Tipo de uva']]], axis=1)

# Extraer los caracteres específicos de 'Tipo de uva' para crear 'Viña' y 'Racimo'
X_completo['Viña'] = X_completo['Tipo de uva'].str[-2]  # Segundo carácter desde el final (representa Viña)
X_completo['Racimo'] = X_completo['Tipo de uva'].str[-1]  # Último carácter (representa Racimo)

# Codificación de variables categóricas ('Viña' y 'Racimo')
X_completo = pd.get_dummies(X_completo, columns=['Viña', 'Racimo'], drop_first=False)

# Eliminar las columnas originales no numéricas 'Tipo de uva'
X_completo = X_completo.drop(columns=['Tipo de uva'])

# Normalizar solo la columna 'Días'
scaler = StandardScaler()

# Normalizamos solo la columna 'Días'
X_completo[['Días']] = scaler.fit_transform(X_completo[['Días']])
X_completo.columns = X_completo.columns.astype(str)

# Mostrar las primeras filas para verificar
X_completo.head()

"""Al aplicar pd.get_dummies() para convertir la columna Tipo de uva en variables dummy, la columna original se convierte en varias columnas binarias, cada una representando la posición según la viña y del racimo, siendo A=Alto, B=Bajo y M=Medio.

Se realiza la separación de los datos para el entrenamiento y el test en un 70% y 30% ya que es el que mejor resultados da.
"""

# Separar en conjunto de entrenamiento para Brix
y_brix = matriz_y.iloc[:, 0].values  # Seleccionar solo la columna de Brix
y_ph = matriz_y.iloc[:, 1].values  # Seleccionar solo la columna de pH

# Usar train_test_split para dividir los datos aleatoriamente
X_train, X_test, y_train, y_test = train_test_split(X_completo, y_brix, test_size=0.3, random_state=42)
# Usar train_test_split para dividir los datos de Brix y pH
X_train_ph, X_test_ph, y_train_ph, y_test_ph = train_test_split(X_completo, y_ph, test_size=0.3, random_state=42)

"""----
#Modelado para Brix
----

En esta sección de Predicción Brix se ha decidido entrenar distintos modelos de Machine Learning para poder seleccionar el que da mejores resultados con nuestros datos en la predicción del Brix.

**Regresión Lineal**
"""

# Inicializar el modelo para Brix
lin_reg = LinearRegression()

# Ajustar el modelo para Brix
lin_reg.fit(X_train, y_train)

# Realizar predicciones para Brix
y_pred_lin = lin_reg.predict(X_test)

# Evaluar el modelo para Brix
mse_lin = mean_squared_error(y_test, y_pred_lin)
r2_lin = r2_score(y_test, y_pred_lin)

print("Regresión Lineal para Brix")
print(f"Mean Squared Error: {mse_lin}")
print(f"R-squared: {r2_lin}\n")

"""**Árbol de Decisión**"""

# Inicializar el modelo
tree_reg = DecisionTreeRegressor()

# Ajustar el modelo
tree_reg.fit(X_train, y_train)

# Realizar predicciones
y_pred_tree = tree_reg.predict(X_test)

# Evaluar el modelo
mse_tree = mean_squared_error(y_test, y_pred_tree)
r2_tree = r2_score(y_test, y_pred_tree)

print("Árbol de Decisión")
print(f"Mean Squared Error: {mse_tree}")
print(f"R-squared: {r2_tree}\n")

"""**Random Forest**"""

# Inicializar el modelo
rf_reg = RandomForestRegressor()

# Ajustar el modelo
rf_reg.fit(X_train, y_train)

# Realizar predicciones
y_pred_rf = rf_reg.predict(X_test)

# Evaluar el modelo
mse_rf = mean_squared_error(y_test, y_pred_rf)
r2_rf = r2_score(y_test, y_pred_rf)

print("Random Forest")
print(f"Mean Squared Error: {mse_rf}")
print(f"R-squared: {r2_rf}\n")

"""**Comparación Modelos Brix**"""

resultados = pd.DataFrame({
    'Modelo': ['Regresión Lineal', 'Árbol de Decisión', 'Random Forest'],
    'MSE': [mse_lin, mse_tree, mse_rf],
    'R-squared': [r2_lin, r2_tree, r2_rf]
})

print(resultados)

"""----
#Modelado para pH
----

**Regresión Lineal**
"""

# Inicializar el modelo de regresión lineal
lin_reg_brix_ph = LinearRegression()

# Ajustar el modelo usando los datos de entrenamiento
lin_reg_brix_ph.fit(X_train_ph, y_train_ph)

# Realizar predicciones para el conjunto de prueba
y_pred_ph = lin_reg_brix_ph.predict(X_test_ph)

# Evaluar el modelo para predecir pH
mse_ph_lin = mean_squared_error(y_test_ph, y_pred_ph)
r2_ph_lin = r2_score(y_test_ph, y_pred_ph)

print("Modelo de Regresión Lineal:")
print(f"Mean Squared Error: {mse_ph_lin}")
print(f"R-squared: {r2_ph_lin}\n")

"""**Árbol de Decisión**"""

# Inicializar el modelo de Árbol de Decisión
tree_reg_brix_ph = DecisionTreeRegressor(random_state=42)

# Ajustar el modelo usando los datos de entrenamiento (Brix como entrada, pH como salida)
tree_reg_brix_ph.fit(X_train_ph, y_train_ph)

# Realizar predicciones para el conjunto de prueba
y_pred_ph_tree = tree_reg_brix_ph.predict(X_test_ph)

# Evaluar el modelo para predecir pH
mse_ph_tree = mean_squared_error(y_test_ph, y_pred_ph_tree)
r2_ph_tree = r2_score(y_test_ph, y_pred_ph_tree)

print("Árbol de Decisión:")
print(f"Mean Squared Error: {mse_ph_tree}")
print(f"R-squared: {r2_ph_tree}\n")

"""**Random Forest**"""

# Inicializar el modelo de Random Forest
rf_reg_brix_ph = RandomForestRegressor(n_estimators=100, random_state=42)

# Ajustar el modelo usando los datos de entrenamiento
rf_reg_brix_ph.fit(X_train_ph, y_train_ph)

# Realizar predicciones para el conjunto de prueba
y_pred_ph_rf = rf_reg_brix_ph.predict(X_test_ph)

# Evaluar el modelo para predecir pH
mse_ph_rf = mean_squared_error(y_test_ph, y_pred_ph_rf)
r2_ph_rf = r2_score(y_test_ph, y_pred_ph_rf)

print("Random Forest:")
print(f"Mean Squared Error: {mse_ph_rf}")
print(f"R-squared: {r2_ph_rf}\n")

"""**Comparación Modelos pH**"""

resultados = pd.DataFrame({
    'Modelo': ['Regresión Lineal', 'Árbol de Decisión', 'Random Forest'],
    'MSE': [mse_ph_lin, mse_ph_tree, mse_ph_rf],
    'R-squared': [r2_ph_lin, r2_ph_tree, r2_ph_rf]
})

print(resultados)

"""----
#Modelado para pH con variable de entrada Brix
----

En esta sección de Predicción pH se ha decidido entrenar distintos modelos de Machine Learning para poder seleccionar el que da mejores resultados con nuestros datos en la predicción del pH, considerando que el valor de entrada a entrenar es el Brix de la matriz_y debido a que es el de mayor relación tiene.
"""

# Reshape necesario para sklearn, dado que brix es una variable de una dimensión
y_brix = y_brix.reshape(-1, 1)

# Usar train_test_split para dividir los datos de Brix y pH
X_train_brix, X_test_brix, y_train_ph, y_test_ph = train_test_split(y_brix, y_ph, test_size=0.3, random_state=42)

# Verificar las dimensiones de los conjuntos
print(f"Conjunto de entrenamiento: {X_train_brix.shape}, {y_train_ph.shape}")
print(f"Conjunto de prueba: {X_test_brix.shape}, {y_test_ph.shape}")

"""**Regresión Lineal**"""

# Inicializar el modelo de regresión lineal
lin_reg_brix_ph = LinearRegression()

# Ajustar el modelo usando los datos de entrenamiento (Brix como entrada, pH como salida)
lin_reg_brix_ph.fit(X_train_brix, y_train_ph)

# Realizar predicciones para el conjunto de prueba
y_pred_ph = lin_reg_brix_ph.predict(X_test_brix)

# Evaluar el modelo para predecir pH
mse_ph_lin = mean_squared_error(y_test_ph, y_pred_ph)
r2_ph_lin = r2_score(y_test_ph, y_pred_ph)

print("Modelo de Regresión Lineal: Predicción de pH a partir de Brix")
print(f"Mean Squared Error: {mse_ph_lin}")
print(f"R-squared: {r2_ph_lin}\n")

"""**Árbol de Decisión**"""

# Inicializar el modelo de Árbol de Decisión
tree_reg_brix_ph = DecisionTreeRegressor(random_state=42)

# Ajustar el modelo usando los datos de entrenamiento (Brix como entrada, pH como salida)
tree_reg_brix_ph.fit(X_train_brix, y_train_ph)

# Realizar predicciones para el conjunto de prueba
y_pred_ph_tree = tree_reg_brix_ph.predict(X_test_brix)

# Evaluar el modelo para predecir pH
mse_ph_tree = mean_squared_error(y_test_ph, y_pred_ph_tree)
r2_ph_tree = r2_score(y_test_ph, y_pred_ph_tree)

print("Árbol de Decisión: Predicción de pH a partir de Brix")
print(f"Mean Squared Error: {mse_ph_tree}")
print(f"R-squared: {r2_ph_tree}\n")

"""**Random Forest**"""

# Inicializar el modelo de Random Forest
rf_reg_brix_ph = RandomForestRegressor(n_estimators=100, random_state=42)

# Ajustar el modelo usando los datos de entrenamiento (Brix como entrada, pH como salida)
rf_reg_brix_ph.fit(X_train_brix, y_train_ph)

# Realizar predicciones para el conjunto de prueba
y_pred_ph_rf = rf_reg_brix_ph.predict(X_test_brix)

# Evaluar el modelo para predecir pH
mse_ph_rf = mean_squared_error(y_test_ph, y_pred_ph_rf)
r2_ph_rf = r2_score(y_test_ph, y_pred_ph_rf)

print("Random Forest: Predicción de pH a partir de Brix")
print(f"Mean Squared Error: {mse_ph_rf}")
print(f"R-squared: {r2_ph_rf}\n")

"""**Comparación Modelos pH**"""

resultados = pd.DataFrame({
    'Modelo': ['Regresión Lineal', 'Árbol de Decisión', 'Random Forest'],
    'MSE': [mse_ph_lin, mse_ph_tree, mse_ph_rf],
    'R-squared': [r2_ph_lin, r2_ph_tree, r2_ph_rf]
})

print(resultados)

"""---
# Prepraración de Datos PCA
---

Se realiza los pasos para realizar un PCA

**Suavizado**
"""

# Suavizar los datos espectrales
window_length = 9  # Impar
polyorder = 2      # Grado del polinomio para el suavizado
espectros_suavizados = savgol_filter(espectros, window_length=window_length, polyorder=polyorder, axis=1)

# Convertir a DataFrame para facilitar la manipulación
espectros_suavizados_df = pd.DataFrame(espectros_suavizados, columns=numeros_onda)

fila_a_graficar = 0

plt.figure(figsize=(12, 6))

# Graficar el espectro original filtrado
plt.plot(numeros_onda_filtrados_1, espectros_filtrados_1.iloc[fila_a_graficar, :],
         label='Original', color='red', alpha=0.5)

# Graficar el espectro suavizado y filtrado
plt.plot(numeros_onda_filtrados_1, espectros_suavizados_df.loc[fila_a_graficar, rango_espectros_1],
         label='Suavizado', linewidth=2, color='blue')

# Configuraciones del gráfico
plt.title(f'Comparación de Espectro Original y Suavizado - Fila {fila_a_graficar + 1}')
plt.xlabel('Números de onda (cm-1)')
plt.ylabel('Intensidad')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

"""**Normalización**"""

# Asegúrate de que solo contenga los datos de espectros
datos_a_normalizar = espectros_suavizados_df.values  # Convertir a un array de numpy

# Crear el objeto StandardScaler
scaler = StandardScaler()

# Ajustar y transformar los datos
datos_normalizados = scaler.fit_transform(datos_a_normalizar)

# Convertir los datos normalizados de nuevo a un DataFrame
espectros_normalizados_df = pd.DataFrame(datos_normalizados, columns=espectros_suavizados_df.columns)

# Seleccionar un espectro de ejemplo
indice_espectro = 1

# Graficar el espectro original y el normalizado
plt.figure(figsize=(10, 6))

# Graficar el espectro original
plt.plot(espectros_suavizados_df.iloc[indice_espectro], label='Original', alpha=0.7)

# Graficar el espectro normalizado
plt.plot(espectros_normalizados_df.iloc[indice_espectro], label='Normalizado', alpha=0.7)

# Añadir título y etiquetas
plt.title(f'Comparación de Espectros - Índice {indice_espectro}')
plt.xlabel('Número de Onda (cm⁻¹)')
plt.ylabel('Intensidad')
plt.legend()
plt.grid()

# Mostrar la gráfica
plt.show()

"""**Análisis de Componentes Principales (PCA)**"""

# Concatenar ambos rangos
espectros_combinados = pd.concat([espectros_filtrados_1, espectros_filtrados_2], axis=1)

# Realizar PCA con 2 componentes
pca = PCA(n_components=2)
componentes_principales = pca.fit_transform(espectros_combinados)

# Crear un DataFrame con los resultados del PCA
df_pca = pd.DataFrame(data=componentes_principales, columns=['Componente 1', 'Componente 2'])
df_pca['Días'] = matriz_x['Días']  # Asumiendo que tienes una columna 'Días' en matriz_x

# Graficar los resultados del PCA sin etiqueta de Días
plt.figure(figsize=(10, 8))
sns.scatterplot(data=df_pca, x='Componente 1', y='Componente 2', s=100, legend=None)
plt.title('PCA de Espectros Filtrados (900-1500 cm-1 y 3200-3400 cm-1)')
plt.xlabel('Componente 1')
plt.ylabel('Componente 2')
plt.grid(True)
plt.tight_layout()
plt.show()

# Varianza explicada por cada componente
varianza_explicada = pca.explained_variance_ratio_
varianza_explicada_acumulada = np.cumsum(varianza_explicada)

# Crear un DataFrame para mostrar la varianza explicada
df_varianza = pd.DataFrame({
    'Componente': ['Componente 1', 'Componente 2'],
    'Varianza Explicada (%)': varianza_explicada * 100,
    'Suma Acumulativa (%)': varianza_explicada_acumulada * 100
})

print("Varianza explicada por cada componente y su suma acumulativa:")
print(df_varianza)

# Concatenar ambos rangos
espectros_combinados = pd.concat([espectros], axis=1)

# Realizar PCA con 2 componentes
pca = PCA(n_components=2)
componentes_principales = pca.fit_transform(espectros_combinados)

# Crear un DataFrame con los resultados del PCA
df_pca = pd.DataFrame(data=componentes_principales, columns=['Componente 1', 'Componente 2'])
df_pca['Días'] = matriz_x['Días']  # Asumiendo que tienes una columna 'Días' en matriz_x

# Graficar los resultados del PCA sin etiqueta de Días
plt.figure(figsize=(10, 8))
sns.scatterplot(data=df_pca, x='Componente 1', y='Componente 2', s=100, legend=None)
plt.title('PCA de Espectros Totales')
plt.xlabel('Componente 1')
plt.ylabel('Componente 2')
plt.grid(True)
plt.tight_layout()
plt.show()

# Varianza explicada por cada componente
varianza_explicada = pca.explained_variance_ratio_
varianza_explicada_acumulada = np.cumsum(varianza_explicada)

# Crear un DataFrame para mostrar la varianza explicada
df_varianza = pd.DataFrame({
    'Componente': ['Componente 1', 'Componente 2'],
    'Varianza Explicada (%)': varianza_explicada * 100,
    'Suma Acumulativa (%)': varianza_explicada_acumulada * 100
})

print("Varianza explicada por cada componente y su suma acumulativa:")
print(df_varianza)

"""---
# Entrenamiento con PCA
---

Se plantea usar todos los datos posibles que tengan algún tipo de relación con los valores a predecir Brix y pH.

Para el entrenamiento de preparar los datos se usarán todas las variables de espectros y se considerará las variables Días y Tipo de uva.
"""

# Crear un DataFrame con los componentes principales
df_componentes_principales = pd.DataFrame(componentes_principales, columns=['Componente 1', 'Componente 2'])

# Asegurarse de que matriz_x tenga un índice correcto
matriz_x.reset_index(drop=True, inplace=True)  # Reiniciar el índice si es necesario

# Agregar las columnas 'Días' y 'Tipo de uva' a los componentes principales
df_componentes_principales['Días'] = matriz_x['Días'].reset_index(drop=True)  # Asegurarse de que las longitudes coincidan
df_componentes_principales['Tipo de uva'] = matriz_x['Tipo de uva'].reset_index(drop=True)  # Asegurarse de que las longitudes coincidan

# Separar 'Tipo de uva' en dos nuevas columnas 'Racimo' y 'Viña'
df_componentes_principales['Viña'] = df_componentes_principales['Tipo de uva'].str[1]  # Segundo carácter
df_componentes_principales['Racimo'] = df_componentes_principales['Tipo de uva'].str[2]  # Tercer carácter

# Eliminar la columna 'Tipo de uva'
df_componentes_principales.drop(columns=['Tipo de uva'], inplace=True)

# Codificación de variables categóricas ('Viña' y 'Racimo')
df_componentes_principales = pd.get_dummies(df_componentes_principales, columns=['Viña', 'Racimo'], drop_first=False)

# Normalizar la columna 'Días'
scaler = StandardScaler()
df_componentes_principales[['Días']] = scaler.fit_transform(df_componentes_principales[['Días']])

# Mostrar el DataFrame resultante
print(df_componentes_principales.head())

"""Al aplicar pd.get_dummies() para convertir la columna Tipo de uva en variables dummy, la columna original se convierte en varias columnas binarias, cada una representando la posición según la viña y del racimo, siendo A=Alto, B=Bajo y M=Medio.

Se realiza la separación de los datos para el entrenamiento y el test en un 70% y 30% ya que es el que mejor resultados da.
"""

# Separar en conjunto de entrenamiento para Brix
y_brix = matriz_y.iloc[:, 0].values  # Seleccionar solo la columna de Brix
y_ph = matriz_y.iloc[:, 1].values  # Seleccionar solo la columna de pH

# Usar el DataFrame con los componentes principales (df_componentes_principales)
X_train_brix, X_test_brix, y_train_brix, y_test_brix = train_test_split(df_componentes_principales, y_brix, test_size=0.3, random_state=42)
X_train_ph, X_test_ph, y_train_ph, y_test_ph = train_test_split(df_componentes_principales, y_ph, test_size=0.3, random_state=42)

"""----
#Modelado para Brix con PCA
----

En esta sección de Predicción Brix se ha decidido entrenar distintos modelos de Machine Learning para poder seleccionar el que da mejores resultados con nuestros datos en la predicción del Brix.

**Regresión Lineal**
"""

# Inicializar el modelo para Brix
lin_reg = LinearRegression()

# Ajustar el modelo para Brix
lin_reg.fit(X_train_brix, y_train_brix)

# Realizar predicciones para Brix
y_pred_lin = lin_reg.predict(X_test_brix)

# Evaluar el modelo para Brix
mse_lin = mean_squared_error(y_test_brix, y_pred_lin)
r2_lin = r2_score(y_test_brix, y_pred_lin)

print("Regresión Lineal para Brix")
print(f"Mean Squared Error: {mse_lin}")
print(f"R-squared: {r2_lin}\n")

"""**Árbol de Decisión**"""

# Inicializar el modelo
tree_reg = DecisionTreeRegressor()

# Ajustar el modelo
tree_reg.fit(X_train_brix, y_train_brix)

# Realizar predicciones
y_pred_tree = tree_reg.predict(X_test_brix)

# Evaluar el modelo
mse_tree = mean_squared_error(y_test_brix, y_pred_tree)
r2_tree = r2_score(y_test_brix, y_pred_tree)

print("Árbol de Decisión")
print(f"Mean Squared Error: {mse_tree}")
print(f"R-squared: {r2_tree}\n")

"""**Random Forest**"""

# Inicializar el modelo
rf_reg = RandomForestRegressor()

# Ajustar el modelo
rf_reg.fit(X_train_brix, y_train_brix)

# Realizar predicciones
y_pred_rf = rf_reg.predict(X_test_brix)

# Evaluar el modelo
mse_rf = mean_squared_error(y_test_brix, y_pred_rf)
r2_rf = r2_score(y_test_brix, y_pred_rf)

print("Random Forest")
print(f"Mean Squared Error: {mse_rf}")
print(f"R-squared: {r2_rf}\n")

"""**Comparación Modelos Brix**"""

resultados = pd.DataFrame({
    'Modelo': ['Regresión Lineal', 'Árbol de Decisión', 'Random Forest'],
    'MSE': [mse_lin, mse_tree, mse_rf],
    'R-squared': [r2_lin, r2_tree, r2_rf]
})

print(resultados)

"""----
#Modelado para pH con PCA
----

**Regresión Lineal**
"""

# Inicializar el modelo de regresión lineal
lin_reg_brix_ph = LinearRegression()

# Ajustar el modelo usando los datos de entrenamiento
lin_reg_brix_ph.fit(X_train_ph, y_train_ph)

# Realizar predicciones para el conjunto de prueba
y_pred_ph = lin_reg_brix_ph.predict(X_test_ph)

# Evaluar el modelo para predecir pH
mse_ph_lin = mean_squared_error(y_test_ph, y_pred_ph)
r2_ph_lin = r2_score(y_test_ph, y_pred_ph)

print("Modelo de Regresión Lineal:")
print(f"Mean Squared Error: {mse_ph_lin}")
print(f"R-squared: {r2_ph_lin}\n")

"""**Árbol de Decisión**"""

# Inicializar el modelo de Árbol de Decisión
tree_reg_brix_ph = DecisionTreeRegressor(random_state=42)

# Ajustar el modelo usando los datos de entrenamiento (Brix como entrada, pH como salida)
tree_reg_brix_ph.fit(X_train_ph, y_train_ph)

# Realizar predicciones para el conjunto de prueba
y_pred_ph_tree = tree_reg_brix_ph.predict(X_test_ph)

# Evaluar el modelo para predecir pH
mse_ph_tree = mean_squared_error(y_test_ph, y_pred_ph_tree)
r2_ph_tree = r2_score(y_test_ph, y_pred_ph_tree)

print("Árbol de Decisión:")
print(f"Mean Squared Error: {mse_ph_tree}")
print(f"R-squared: {r2_ph_tree}\n")

"""**Random Forest**"""

# Inicializar el modelo de Random Forest
rf_reg_brix_ph = RandomForestRegressor(n_estimators=100, random_state=42)

# Ajustar el modelo usando los datos de entrenamiento
rf_reg_brix_ph.fit(X_train_ph, y_train_ph)

# Realizar predicciones para el conjunto de prueba
y_pred_ph_rf = rf_reg_brix_ph.predict(X_test_ph)

# Evaluar el modelo para predecir pH
mse_ph_rf = mean_squared_error(y_test_ph, y_pred_ph_rf)
r2_ph_rf = r2_score(y_test_ph, y_pred_ph_rf)

print("Random Forest:")
print(f"Mean Squared Error: {mse_ph_rf}")
print(f"R-squared: {r2_ph_rf}\n")

"""**Comparación Modelos pH**"""

resultados = pd.DataFrame({
    'Modelo': ['Regresión Lineal', 'Árbol de Decisión', 'Random Forest'],
    'MSE': [mse_ph_lin, mse_ph_tree, mse_ph_rf],
    'R-squared': [r2_ph_lin, r2_ph_tree, r2_ph_rf]
})

print(resultados)

"""---
# Entrenamiento con PCA pH con Brix
---

Se plantea usar todos los datos posibles que tengan algún tipo de relación con los valores a predecir Brix y pH.

Para el entrenamiento de preparar los datos se usarán todas las variables de espectros y se considerará las variables Días y Tipo de uva.
"""

# Crear un DataFrame con los componentes principales
df_componentes_principales = pd.DataFrame(componentes_principales, columns=['Componente 1', 'Componente 2'])

# Asegurarse de que matriz_x tenga un índice correcto
matriz_x.reset_index(drop=True, inplace=True)  # Reiniciar el índice si es necesario

# Agregar las columnas 'Días' y 'Tipo de uva' a los componentes principales
df_componentes_principales['Días'] = matriz_x['Días'].reset_index(drop=True)  # Asegurarse de que las longitudes coincidan
df_componentes_principales['Tipo de uva'] = matriz_x['Tipo de uva'].reset_index(drop=True)  # Asegurarse de que las longitudes coincidan

# Separar 'Tipo de uva' en dos nuevas columnas 'Racimo' y 'Viña'
df_componentes_principales['Viña'] = df_componentes_principales['Tipo de uva'].str[1]  # Segundo carácter
df_componentes_principales['Racimo'] = df_componentes_principales['Tipo de uva'].str[2]  # Tercer carácter

# Eliminar la columna 'Tipo de uva'
df_componentes_principales.drop(columns=['Tipo de uva'], inplace=True)

# Agregar la columna de Brix
df_componentes_principales['Brix'] = matriz_y['Brix'].reset_index(drop=True)  # Asegúrate de que la longitud coincida

# Normalizar la columna de Brix
scaler_brix = StandardScaler()
df_componentes_principales[['Brix']] = scaler_brix.fit_transform(df_componentes_principales[['Brix']])

# Codificación de variables categóricas ('Viña' y 'Racimo')
df_componentes_principales = pd.get_dummies(df_componentes_principales, columns=['Viña', 'Racimo'], drop_first=False)

# Normalizar la columna 'Días'
scaler_dias = StandardScaler()
df_componentes_principales[['Días']] = scaler_dias.fit_transform(df_componentes_principales[['Días']])

# Mostrar el DataFrame resultante
print(df_componentes_principales.head())

"""Al aplicar pd.get_dummies() para convertir la columna Tipo de uva en variables dummy, la columna original se convierte en varias columnas binarias, cada una representando la posición según la viña y del racimo, siendo A=Alto, B=Bajo y M=Medio.

Se realiza la separación de los datos para el entrenamiento y el test en un 70% y 30% ya que es el que mejor resultados da.
"""

# Separar en conjunto de entrenamiento para pH
y_ph = matriz_y.iloc[:, 1].values

# Usar el DataFrame con los componentes principales (df_componentes_principales)
X_train_ph, X_test_ph, y_train_ph, y_test_ph = train_test_split(df_componentes_principales, y_ph, test_size=0.3, random_state=42)

"""----
#Modelado para pH con PCA y Brix
----

**Regresión Lineal**
"""

# Inicializar el modelo de regresión lineal
lin_reg_brix_ph = LinearRegression()

# Ajustar el modelo usando los datos de entrenamiento
lin_reg_brix_ph.fit(X_train_ph, y_train_ph)

# Realizar predicciones para el conjunto de prueba
y_pred_ph = lin_reg_brix_ph.predict(X_test_ph)

# Evaluar el modelo para predecir pH
mse_ph_lin = mean_squared_error(y_test_ph, y_pred_ph)
r2_ph_lin = r2_score(y_test_ph, y_pred_ph)

print("Modelo de Regresión Lineal:")
print(f"Mean Squared Error: {mse_ph_lin}")
print(f"R-squared: {r2_ph_lin}\n")

"""**Árbol de Decisión**"""

# Inicializar el modelo de Árbol de Decisión
tree_reg_brix_ph = DecisionTreeRegressor(random_state=42)

# Ajustar el modelo usando los datos de entrenamiento (Brix como entrada, pH como salida)
tree_reg_brix_ph.fit(X_train_ph, y_train_ph)

# Realizar predicciones para el conjunto de prueba
y_pred_ph_tree = tree_reg_brix_ph.predict(X_test_ph)

# Evaluar el modelo para predecir pH
mse_ph_tree = mean_squared_error(y_test_ph, y_pred_ph_tree)
r2_ph_tree = r2_score(y_test_ph, y_pred_ph_tree)

print("Árbol de Decisión:")
print(f"Mean Squared Error: {mse_ph_tree}")
print(f"R-squared: {r2_ph_tree}\n")

"""**Random Forest**"""

# Inicializar el modelo de Random Forest
rf_reg_brix_ph = RandomForestRegressor(n_estimators=100, random_state=42)

# Ajustar el modelo usando los datos de entrenamiento
rf_reg_brix_ph.fit(X_train_ph, y_train_ph)

# Realizar predicciones para el conjunto de prueba
y_pred_ph_rf = rf_reg_brix_ph.predict(X_test_ph)

# Evaluar el modelo para predecir pH
mse_ph_rf = mean_squared_error(y_test_ph, y_pred_ph_rf)
r2_ph_rf = r2_score(y_test_ph, y_pred_ph_rf)

print("Random Forest:")
print(f"Mean Squared Error: {mse_ph_rf}")
print(f"R-squared: {r2_ph_rf}\n")

"""**Comparación Modelos pH**"""

resultados = pd.DataFrame({
    'Modelo': ['Regresión Lineal', 'Árbol de Decisión', 'Random Forest'],
    'MSE': [mse_ph_lin, mse_ph_tree, mse_ph_rf],
    'R-squared': [r2_ph_lin, r2_ph_tree, r2_ph_rf]
})

print(resultados)