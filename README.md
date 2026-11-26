# SciELO Explorer — cliente Streamlit para PYBOT

Aplicación experimental para consultar servicios públicos de **SciELO ArticleMeta**, explorar metadatos y recuperar XML de artículos individuales.

> Este proyecto es un cliente independiente. No es el servidor `articles_meta` de SciELO, no despliega MongoDB ni replica su infraestructura.

## 1. Funciones

- Abrir una búsqueda temática en el buscador oficial de SciELO.
- Consultar identificadores de artículos por ISSN mediante ArticleMeta.
- Consultar metadatos JSON de un artículo por su `code`.
- Solicitar el XML individual en `xmlrsps` o `xmlwos`.
- Inspeccionar si el XML contiene título, DOI, resumen, `body`, secciones y referencias.
- Descargar identificadores CSV, metadatos JSON y XML original.

## 2. Limitaciones deliberadas

- La búsqueda temática se abre en SciELO; esta versión **no extrae automáticamente** el HTML del buscador.
- ArticleMeta es principalmente un servicio de recuperación de registros bibliográficos/metadatos en JSON. El formato XML solicitado puede variar en contenido y cobertura.
- La presencia de XML no garantiza que incluya el cuerpo completo del artículo. La aplicación ofrece un diagnóstico estructural, no una certificación de texto completo.
- La aplicación no ejecuta el `dumparticles.py` original y no intenta descargar toda la red.
- La consulta por ISSN depende de que el endpoint público acepte el parámetro `issn` en la instalación disponible. Si no lo acepta, se mostrará el error de la API.
- No hay reintentos automáticos ante HTTP 403 o 429. Detén la consulta y respeta las restricciones del servicio.
- Streamlit Community Cloud tiene almacenamiento efímero. Los archivos descargados por el usuario se guardan localmente en su equipo; no se conserva una biblioteca permanente en el servidor.

## 3. Ejecutar localmente en Windows

Se recomienda Python 3.11 o 3.12.

```powershell
# 1. Entrar en la carpeta del proyecto
cd D:\SCIELO_EXPLORER

# 2. Crear entorno virtual
py -3.11 -m venv .venv

# 3. Activarlo
.\.venv\Scripts\Activate.ps1

# 4. Instalar dependencias
python -m pip install --upgrade pip
pip install -r requirements.txt

# 5. Ejecutar
streamlit run app.py
```

Si PowerShell impide activar el entorno, puede ejecutarse directamente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## 4. Subir a GitHub

Crea un repositorio vacío, por ejemplo `scielo-explorer-pybot`. Desde la carpeta del proyecto:

```bash
git init
git add .
git commit -m "Initial SciELO Explorer client"
git branch -M main
git remote add origin https://github.com/USUARIO/scielo-explorer-pybot.git
git push -u origin main
```

Sustituye `USUARIO` por tu usuario real de GitHub. No publiques tokens, claves ni archivos de datos privados.

## 5. Desplegar en Streamlit Community Cloud

1. Sube el proyecto a GitHub.
2. Entra en https://share.streamlit.io/
3. Selecciona **Create app**.
4. Selecciona el repositorio, la rama `main` y el archivo `app.py`.
5. Despliega la aplicación.

El archivo `requirements.txt` instala las dependencias. No se necesita `packages.txt` ni una base de datos externa para esta versión.

## 6. Endpoints consultados

Base URL predeterminada:

`https://articlemeta.scielo.org/api/v1`

La aplicación utiliza estas rutas:

- `GET /article/identifiers/?issn=...&limit=...`
- `GET /article/?code=...`
- `GET /article?code=...&format=xmlrsps`
- `GET /article?code=...&format=xmlwos`

La ruta de XML y los formatos `xmlrsps` / `xmlwos` se basan en el script oficial `processing/dumparticles.py`. El endpoint de identificadores y sus parámetros deben verificarse con la documentación vigente y con respuestas reales de ArticleMeta.

## 7. Referencias oficiales

- Repositorio `articles_meta`: https://github.com/scieloorg/articles_meta
- Script original `dumparticles.py`: https://github.com/scieloorg/articles_meta/blob/master/processing/dumparticles.py
- Documentación ArticleMeta: https://github.com/scieloorg/articles_meta/tree/master/docs
- Buscador SciELO: https://search.scielo.org/
- SciELO Publishing Schema: https://scielo.readthedocs.io/

La documentación de ArticleMeta describe un servicio REST para recuperar registros de artículos, revistas, fascículos y colecciones en JSON. También recomienda los archivos masivos mensuales para cargas iniciales y advierte que recuperar todos los registros individualmente por HTTP puede tardar varios días.

## 8. Licencia y uso de datos

El código de este prototipo se distribuye bajo MIT. Esto **no concede derechos sobre los artículos recuperados**. Antes de reutilizar o redistribuir textos, comprueba la licencia del artículo y las condiciones de la revista.

## 9. Estado del proyecto

**Versión:** 0.1.0 — prototipo de cliente.

No se declara que la conexión haya sido probada en producción desde este entorno. La primera ejecución debe considerarse una prueba controlada: consultar un ISSN, recuperar un solo artículo y revisar su XML antes de aumentar el volumen.
