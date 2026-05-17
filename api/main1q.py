from fastapi import FastAPI, HTTPException
import pandas as pd
from datetime import date, timedelta
from pydantic import BaseModel
from math import sqrt
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

"""
API: DENTRO DE LA CARPETA DE DSMARKET-API
cd /Users/lucia/Downloads/master/tfm/TFM/dsmarket-api
conda activate api
uvicorn main:app --host 0.0.0.0 --port 8000
POST http://127.0.0.1:8000/recomendaciones/individual
{"tienda_id":"BOS_1","producto_id":"HOME_&_GARDEN_1_110","semana_inicio":"2016-04-25"} 
POST http://127.0.0.1:8000/recomendaciones/masiva
{"semana_inicio":"2016-04-25","items":[{"tienda_id":"BOS_1","producto_id":"HOME_&_GARDEN_1_110"},{"tienda_id":"BOS_1","producto_id":"HOME_&_GARDEN_1_334"}]}
POST http://127.0.0.1:8000/decisiones
{"recomendacion_id":"REC_20160425_BOS_1_HOME_&_GARDEN_1_110","decision":"modificada","cantidad_recomendada":50,"cantidad_final":45,"motivo_modificacion":"Ajuste manual por criterio de Operaciones","usuario":"operations_manager"}
POST http://127.0.0.1:8000/ventas-reales
{"tienda_id": "BOS_1", "producto_id": "HOME_&_GARDEN_1_110", "semana_inicio": "2016-04-25", "demanda_real": 42}

uvicorn main1q:app --host 0.0.0.0 --port 8000


FRONTEND: EN OTRA TERMINAL SIN CERRAR LA ANTERIOR
http://0.0.0.0:8000/app
http://127.0.0.1:8000/app
"""
app = FastAPI(title="DSMarket Stock Recommendation API", description="API para generar recomendaciones de abastecimiento semanal.")

@app.get("/")
def inicio():
    return {"mensaje": "API de DSMarket funcionando", "documentacion": "/docs"}

@app.get("/health")
def comprobar_estado():
    return {"estado": "ok"}

RUTA_PREDICCIONES = "data/pred_item_tienda.parquet"
df_predicciones = pd.read_parquet(RUTA_PREDICCIONES) 
df_predicciones["date"] = pd.to_datetime(df_predicciones["date"]) # lo pasamos a fecha

RUTA_INVENTARIO = "data/inventario_actual.csv"
df_inventario = pd.read_csv(RUTA_INVENTARIO)

RUTA_POLITICAS = "data/politicas_inventario.csv"
df_politicas = pd.read_csv(RUTA_POLITICAS)

RUTA_DECISIONES = "data/decisiones_operaciones.csv"

RUTA_RECOMENDACIONES_GENERADAS = "data/recomendaciones_generadas.csv" # predicciones q se han hecho

RUTA_VENTAS_REALES = "data/ventas_reales.csv" # esto habria que hacer que se cargase desde la base de datos pero bueno para probar esta bien

def obtener_stock(tienda_id: str, producto_id: str):
    print(df_inventario)
    fila = df_inventario[(df_inventario["store_code"] == tienda_id) & (df_inventario["item"] == producto_id)]
    if fila.empty:
        raise HTTPException(status_code=404, detail = "No se encontró stock actual para esa tienda y producto.")
    return int(fila["stock_actual"].values[0])

def obtener_politica_inventario(producto_id: str) -> dict:
    resultado = df_politicas[(df_politicas["item"] == producto_id) & (df_politicas["active"] == True)]
    if resultado.empty:
        raise HTTPException(status_code = 404, detail = "No se encontró política de inventario activa para ese producto.")
    return resultado.iloc[0].to_dict()

def calcular_recomendacion(tienda_id: str, producto_id: str, semana_inicio: date):
    semana_fin = semana_inicio + timedelta(days=6)
    datos_semana = df_predicciones[(df_predicciones["store_code"] == tienda_id) & (df_predicciones["item"] == producto_id) & (df_predicciones["date"] >= pd.to_datetime(semana_inicio)) & (df_predicciones["date"] <= pd.to_datetime(semana_fin))]
    if len(datos_semana) == 0:
        raise HTTPException(status_code=404, detail="No se encontraron predicciones para la tienda y producto especificados en la semana indicada.")
    demanda_predicha = datos_semana["pred_final"].sum()
    stock_actual = obtener_stock(tienda_id, producto_id)
    politica = obtener_politica_inventario(producto_id)
    periodo_proteccion = politica["review_period_days"] + politica["lead_time_days"]
    stock_seguridad = round(politica["z_value"] * politica["sigma_error"] * sqrt(periodo_proteccion))
    stock_objetivo = round(demanda_predicha + stock_seguridad)
    cantidad_a_reponer = max(stock_objetivo - stock_actual, 0)
    recomendacion_id = f"REC_{semana_inicio.strftime('%Y%m%d')}_{tienda_id}_{producto_id}" # para poder registrar luego si se han aceptado las recomendaciones o no, por trazabilidad
    return {"recomendacion_id": recomendacion_id, "tienda_id": tienda_id, "producto_id": producto_id, "semana_inicio": semana_inicio, "semana_fin": semana_fin, "dias_encontrados": len(datos_semana), "demanda_predicha": round(demanda_predicha, 2), "stock_actual": stock_actual, "cantidad_a_reponer": cantidad_a_reponer, "abc_class": politica["abc_class"], "xyz_class": politica["xyz_class"], "service_level": politica["service_level"], "stock_seguridad": stock_seguridad, "stock_objetivo": stock_objetivo}

def guardar_recomendacion_generada(recomendacion: dict):
    nueva_fila = pd.DataFrame([{
        "recomendacion_id": recomendacion["recomendacion_id"],
        "tienda_id": recomendacion["tienda_id"],
        "producto_id": recomendacion["producto_id"],
        "semana_inicio": recomendacion["semana_inicio"],
        "semana_fin": recomendacion["semana_fin"],
        "demanda_predicha": recomendacion["demanda_predicha"],
        "stock_actual": recomendacion["stock_actual"],
        "stock_seguridad": recomendacion["stock_seguridad"],
        "stock_objetivo": recomendacion["stock_objetivo"],
        "cantidad_a_reponer": recomendacion["cantidad_a_reponer"],
        "abc_class": recomendacion["abc_class"],
        "xyz_class": recomendacion["xyz_class"],
        "service_level": recomendacion["service_level"]
    }])
    try:
        df_existente = pd.read_csv(RUTA_RECOMENDACIONES_GENERADAS)
        df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
    except FileNotFoundError:
        df_final = nueva_fila
    df_final.to_csv(RUTA_RECOMENDACIONES_GENERADAS, index=False)

def interpretar_bias(bias: float):
    if bias > 0:
        return "El modelo tiende a infrapredecir: la demanda real suele ser mayor que la predicha."
    elif bias < 0:
        return "El modelo tiende a sobrepredecir: la demanda real suele ser menor que la predicha."
    else:
        return "El modelo no muestra sesgo medio en las observaciones evaluadas."
    

class PeticionRecomendacion(BaseModel):
    tienda_id: str
    producto_id: str
    semana_inicio: date 

@app.post("/recomendaciones/individual")
def crear_recomendacion_individual(peticion: PeticionRecomendacion): # mejor sacamos la funcion fuera para poder reutilizarla en las peticiones masivas
    recomendacion = calcular_recomendacion(peticion.tienda_id, peticion.producto_id, peticion.semana_inicio)
    guardar_recomendacion_generada(recomendacion)
    return recomendacion

class ItemRecomendacion(BaseModel):
    tienda_id: str
    producto_id: str

class PeticionMasiva(BaseModel):
    semana_inicio: date
    items: list[ItemRecomendacion] # la petivion masiva es hacer peticiones de muchos items (separando los items por tiendas)

@app.post("/recomendaciones/masiva")
def crear_recomendacion_masiva(peticion: PeticionMasiva):
    resultados = []
    for item in peticion.items:
        recomendacion = calcular_recomendacion(item.tienda_id, item.producto_id, peticion.semana_inicio)
        guardar_recomendacion_generada(recomendacion)
        resultados.append(recomendacion)
    return {"semana_inicio": peticion.semana_inicio, "total_recomendaciones": len(resultados), "recomendaciones": resultados}

class DecisionOperaciones(BaseModel): # tenemos que registrar si los usuarios usan nuestras recomendaciones o no
    recomendacion_id: str 
    decision: str
    cantidad_recomendada: int
    cantidad_final: int
    motivo_modificacion: str | None = None
    usuario: str

@app.post("/decisiones")
def registrar_decision(decision: DecisionOperaciones):
    nueva_fila = pd.DataFrame([decision.model_dump()]) # convierte la decision que tiene el formato que hemos definido arriba en un diccionario de python y luego lo convertimos en un dataframe
    nueva_fila.to_csv(RUTA_DECISIONES, mode="a", header=False, index=False, encoding="utf-8")
    return {"estado": "decision registrada", "decision": decision}

@app.get("/decisiones")
def consultar_decisiones():
    try:
        df_decisiones = pd.read_csv(RUTA_DECISIONES, encoding="utf-8", encoding_errors="replace")
        df_decisiones = df_decisiones.where(pd.notnull(df_decisiones), None)
        return {"total_decisiones": len(df_decisiones), "decisiones": df_decisiones.to_dict(orient="records")}
    except FileNotFoundError:
        return {"total_decisiones": 0, "decisiones": []}
    
class VentaReal(BaseModel):
    tienda_id: str
    producto_id: str
    semana_inicio: date
    demanda_real: float

@app.post("/ventas-reales")
def registrar_venta_real(venta: VentaReal):
    nueva_fila = pd.DataFrame([venta.model_dump()])
    try:
        df_existente = pd.read_csv(RUTA_VENTAS_REALES)
        df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
    except FileNotFoundError:
        df_final = nueva_fila
    df_final.to_csv(RUTA_VENTAS_REALES, index=False)

    return {"estado": "venta real registrada", "venta": venta}


@app.get("/monitorizacion/modelo")
def monitorizar_modelo():
    try:
        df_rec = pd.read_csv(RUTA_RECOMENDACIONES_GENERADAS)
        df_real = pd.read_csv(RUTA_VENTAS_REALES)
    except FileNotFoundError:
        raise HTTPException(status_code = 404, detail = "No hay suficientes datos para calcular métricas del modelo.")
    if df_rec.empty or df_real.empty:
        raise HTTPException(status_code = 404, detail = "No hay suficientes datos para calcular métricas del modelo.")
    df_rec["semana_inicio"] = pd.to_datetime(df_rec["semana_inicio"])
    df_real["semana_inicio"] = pd.to_datetime(df_real["semana_inicio"])
    df_rec = df_rec.drop_duplicates(subset=["tienda_id", "producto_id", "semana_inicio"], keep="last" ) # si hay varias recomendaciones para el mismo item y semana nos quedamos con la última que se ha generado, que es la que se ha guardado en el csv, para luego compararla con las ventas reales. Esto es importante porque puede haber recomendaciones modificadas por los usuarios, entonces lo que queremos es comparar las ventas reales con la recomendación final que se ha dado a operaciones, no con todas las recomendaciones que se han generado.
    df_real = df_real.drop_duplicates(subset=["tienda_id", "producto_id", "semana_inicio"], keep="last")
    df_eval = df_rec.merge(df_real, on=["tienda_id", "producto_id", "semana_inicio"], how="inner")
    if df_eval.empty:
        raise HTTPException(status_code = 404, detail = "No hay coincidencias entre recomendaciones generadas y ventas reales.")
    df_eval["error"] = df_eval["demanda_real"] - df_eval["demanda_predicha"]
    df_eval["error_absoluto"] = df_eval["error"].abs()
    df_eval["error_cuadratico"] = df_eval["error"] ** 2
    df_eval_mape = df_eval[df_eval["demanda_real"] != 0].copy()
    if len(df_eval_mape) > 0:
        mape = (df_eval_mape["error_absoluto"] / df_eval_mape["demanda_real"]).mean() * 100
    else:
        mape = None
    mae = df_eval["error_absoluto"].mean()
    rmse = (df_eval["error_cuadratico"].mean()) ** 0.5
    bias = df_eval["error"].mean()
    return {"total_observaciones_evaluadas": len(df_eval), "mae": round(mae, 2), "rmse": round(rmse, 2), "mape": round(mape, 2) if mape is not None else None, "bias": round(bias, 2),"interpretacion_bias": interpretar_bias(bias),
        "detalle": df_eval[[
            "tienda_id",
            "producto_id",
            "semana_inicio",
            "demanda_predicha",
            "demanda_real",
            "error",
            "error_absoluto"
        ]].to_dict(orient="records")}


app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/app")
def abrir_frontend():
    return FileResponse("frontend/index.html")

@app.get("/logo-dsmarket.png")
def obtener_logo():
    return FileResponse("logo-dsmarket.png") 

class PeticionTienda(BaseModel):
    tienda_id: str
    semana_inicio: date
 
@app.post("/recomendaciones/tienda") # solo se generan para las q tengan productos en el stock actual 
def crear_recomendaciones_tienda(peticion: PeticionTienda):
    productos_tienda = df_inventario[df_inventario["store_code"] == peticion.tienda_id]["item"].unique()
    if len(productos_tienda) == 0:
        raise HTTPException(status_code = 404, detail = "No se encontraron productos para esa tienda.")
    resultados = []
    for producto_id in productos_tienda:
        recomendacion = calcular_recomendacion( peticion.tienda_id, producto_id, peticion.semana_inicio)
        resultados.append(recomendacion)
    return {"tienda_id": peticion.tienda_id, "semana_inicio": peticion.semana_inicio, "total_recomendaciones": len(resultados), "recomendaciones": resultados }