"""
Sistema de Gestión de Modelos de Machine Learning
Implementa herencia, polimorfismo, encapsulamiento, clases abstractas,
listas, diccionarios, tuplas, manejo de excepciones y métodos especiales.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod


# =============================================================================
# 1. Clase Base Abstracta: ModeloML
# =============================================================================

class ModeloML(ABC):
    """Clase base abstracta para todos los modelos de Machine Learning."""

    def __init__(self, nombre_modelo: str, tipo_modelo: str) -> None:
        self._nombre_modelo: str = nombre_modelo
        self._precision: float = 0.0
        self._tipo_modelo: str = tipo_modelo

    # Métodos abstractos
    @abstractmethod
    def entrenar(self, datos: dict) -> None:
        """Simula el entrenamiento del modelo con los datos provistos."""
        ...

    @abstractmethod
    def predecir(self, datos: dict) -> list:
        """Realiza predicciones sobre los datos provistos."""
        ...

    # Método concreto
    def evaluar(self) -> float:
        """Retorna la precisión actual del modelo."""
        return self._precision

    def __str__(self) -> str:
        return (
            f"Modelo : {self._nombre_modelo}\n"
            f"Tipo   : {self._tipo_modelo}\n"
            f"Precisión: {self._precision:.2f}%"
        )


# =============================================================================
# 2. Subclases
# =============================================================================

class Clasificador(ModeloML):
    """Modelo de clasificación. Precisión simulada entre 70% y 95%."""

    # Rango como tupla (inmutable, requerimiento de tuplas)
    RANGO_PRECISION: tuple[float, float] = (70.0, 95.0)

    def __init__(self, nombre_modelo: str) -> None:
        super().__init__(nombre_modelo, tipo_modelo="Clasificador")

    def entrenar(self, datos: dict) -> None:
        """Simula entrenamiento generando una precisión aleatoria en el rango del clasificador."""
        muestras = datos.get("numero_muestras", 0)
        if muestras <= 0:
            raise ValueError("El dataset debe tener al menos una muestra para entrenar.")

        self._precision = round(
            random.uniform(*self.RANGO_PRECISION), 2
        )
        print(f"[{self._nombre_modelo}] Entrenado con {muestras} muestras → precisión: {self._precision}%")

    def predecir(self, datos: dict) -> list:
        """Retorna etiquetas de clase simuladas."""
        n = datos.get("numero_muestras", 1)
        return [random.randint(0, 1) for _ in range(n)]


class Regresor(ModeloML):
    """Modelo de regresión. Precisión simulada entre 60% y 90%."""

    RANGO_PRECISION: tuple[float, float] = (60.0, 90.0)

    def __init__(self, nombre_modelo: str) -> None:
        super().__init__(nombre_modelo, tipo_modelo="Regresor")

    def entrenar(self, datos: dict) -> None:
        """Simula entrenamiento generando una precisión aleatoria en el rango del regresor."""
        muestras = datos.get("numero_muestras", 0)
        if muestras <= 0:
            raise ValueError("El dataset debe tener al menos una muestra para entrenar.")

        self._precision = round(
            random.uniform(*self.RANGO_PRECISION), 2
        )
        print(f"[{self._nombre_modelo}] Entrenado con {muestras} muestras → precisión: {self._precision}%")

    def predecir(self, datos: dict) -> list:
        """Retorna valores continuos simulados."""
        n = datos.get("numero_muestras", 1)
        return [round(random.uniform(0.0, 100.0), 2) for _ in range(n)]


# =============================================================================
# 3. Clase Dataset
# =============================================================================

class Dataset:
    """Representa un conjunto de datos para entrenar o evaluar modelos."""

    def __init__(self, nombre_dataset: str, numero_muestras: int, numero_features: int) -> None:
        # Validación con manejo de excepciones
        if numero_muestras <= 0:
            raise ValueError(
                f"numero_muestras debe ser mayor que 0, se recibió: {numero_muestras}"
            )
        if numero_features <= 0:
            raise ValueError(
                f"numero_features debe ser mayor que 0, se recibió: {numero_features}"
            )

        self.nombre_dataset: str = nombre_dataset
        self.numero_muestras: int = numero_muestras
        self.numero_features: int = numero_features

    def resumen(self) -> None:
        """Imprime un resumen del dataset."""
        print("=" * 40)
        print(f"Dataset      : {self.nombre_dataset}")
        print(f"Muestras     : {self.numero_muestras}")
        print(f"Features     : {self.numero_features}")
        print("=" * 40)

    def como_dict(self) -> dict:
        """Retorna los datos del dataset como diccionario (para pasarlo a entrenar)."""
        return {
            "nombre": self.nombre_dataset,
            "numero_muestras": self.numero_muestras,
            "numero_features": self.numero_features,
        }

    def __str__(self) -> str:
        return f"Dataset('{self.nombre_dataset}', muestras={self.numero_muestras}, features={self.numero_features})"


# =============================================================================
# 4. Clase SistemaGestionML
# =============================================================================

class SistemaGestionML:
    """
    Administra múltiples modelos de ML.
    Usa lista para almacenar modelos y diccionario para guardar resultados.
    """

    def __init__(self) -> None:
        self._modelos: list[ModeloML] = []
        self._resultados: dict[str, float] = {}   # nombre_modelo → precisión

    def agregar_modelo(self, modelo: ModeloML) -> None:
        """Agrega un modelo al sistema."""
        self._modelos.append(modelo)
        print(f"Modelo '{modelo._nombre_modelo}' agregado al sistema.")

    def entrenar_todos(self, dataset: Dataset) -> None:
        """Entrena todos los modelos registrados con el dataset dado."""
        print("\n--- Entrenando todos los modelos ---")
        datos = dataset.como_dict()

        for modelo in self._modelos:
            try:
                modelo.entrenar(datos)
                self._resultados[modelo._nombre_modelo] = modelo.evaluar()
            except ValueError as e:
                print(f"Error entrenando '{modelo._nombre_modelo}': {e}")

    def mostrar_ranking(self) -> None:
        """Muestra el ranking de modelos ordenado de mayor a menor precisión."""
        if not self._resultados:
            print("No hay resultados. Entrena los modelos primero.")
            return

        print("\n========== RANKING DE MODELOS ==========")

        # Ordenar diccionario por precisión descendente → lista de tuplas
        ranking: list[tuple[str, float]] = sorted(
            self._resultados.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        for posicion, (nombre, precision) in enumerate(ranking, start=1):
            barra = "█" * int(precision // 5)
            print(f"  {posicion}. {nombre:<25} {precision:>6.2f}%  {barra}")

        print("=" * 40)

    def mostrar_mejor_modelo(self) -> None:
        """Indica cuál fue el mejor modelo."""
        if not self._resultados:
            print("No hay resultados. Entrena los modelos primero.")
            return

        mejor_nombre = max(self._resultados, key=self._resultados.get)
        mejor_precision = self._resultados[mejor_nombre]

        # Buscar el objeto modelo correspondiente
        mejor_modelo = next(m for m in self._modelos if m._nombre_modelo == mejor_nombre)

        print("\n========== MEJOR MODELO ==========")
        print(mejor_modelo)
        print(f"\nPrecisión final: {mejor_precision:.2f}%")
        print("=" * 34)

    def __str__(self) -> str:
        return (
            f"SistemaGestionML("
            f"modelos={len(self._modelos)}, "
            f"entrenados={len(self._resultados)})"
        )


# =============================================================================
# Programa principal
# =============================================================================

def main() -> None:
    # 1. Crear dataset (con validación de excepciones)
    print("\n>>> Creando dataset...")
    try:
        dataset = Dataset(
            nombre_dataset="Iris Extendido",
            numero_muestras=500,
            numero_features=12,
        )
    except ValueError as e:
        print(f"Error al crear dataset: {e}")
        return

    dataset.resumen()

    # Demostración de manejo de excepción con datos inválidos
    print(">>> Intentando crear dataset con muestras inválidas...")
    try:
        mal_dataset = Dataset("Roto", numero_muestras=-5, numero_features=3)
    except ValueError as e:
        print(f"  Excepción capturada correctamente → {e}\n")

    # 2. Crear sistema y al menos 4 modelos (mezcla de clasificadores y regresores)
    sistema = SistemaGestionML()
    print(f"\n>>> {sistema}")

    modelos: list[ModeloML] = [
        Clasificador("RandomForest v1"),
        Clasificador("SVM Lineal"),
        Regresor("Regresión Lineal"),
        Regresor("Gradient Boosting"),
        Clasificador("Red Neuronal MLP"),   # 5to modelo (bonus)
    ]

    print("\n>>> Agregando modelos al sistema...")
    for modelo in modelos:
        sistema.agregar_modelo(modelo)

    # Polimorfismo: mismo método entrenar(), comportamiento diferente según clase
    # 3. Entrenar todos los modelos
    sistema.entrenar_todos(dataset)

    # 4. Mostrar ranking ordenado de mayor a menor precisión
    sistema.mostrar_ranking()

    # 5. Indicar cuál fue el mejor modelo
    sistema.mostrar_mejor_modelo()

    # Información extra: __str__ de cada modelo
    print("\n>>> Detalle de todos los modelos:")
    for modelo in modelos:
        print("-" * 35)
        print(modelo)
    print("-" * 35)


if __name__ == "__main__":
    main()
