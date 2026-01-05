README for FilesToolsManagment

*****************************************
Para la app, se necesitan las librerías: 
- PyQt6 (librería para la UI, más profesional)
- pymupdf (para previsualizar pdfs)
- Pillow (para imagenes)
- pillow-heif (para imagenes .heic de iphone)

---------------------------------------------
Pasos para crear el .exe de cualquier código:
- Instala la librería necesaria: pip install pyinstaller
- Navega a la ruta del script que quiera tener el .exe
- Por ejemplo "lanzador.py"
- Ejecuta PyInstaller en tu terminal:
    pyinstaller --noconsole --onefile --icon=app_icon.ico renameApp_UI.py

    La magia de usar PyInstaller: el archivo .exe resultante es totalmente independiente.
    Aquí te explico qué sucede técnicamente para que te quedes tranquilo:
1. ¿Qué pasa si no tiene Python?
    No importa. Cuando ejecutas el comando pyinstaller --onefile, la herramienta "congela" el intérprete de Python y lo mete dentro del archivo .exe.
    El usuario final no necesita instalar Python.
    El archivo lleva consigo todo lo necesario para "auto-ejecutarse" en cualquier ordenador con Windows.
2. ¿Qué pasa con las librerías (Pandas, Openpyxl)?
    Van incluidas en el paquete. PyInstaller analiza tu código, detecta que usas pandas y openpyxl, y copia todos los archivos de esas librerías dentro del ejecutable.
    Al abrir el .exe, este crea una carpeta temporal invisible, descomprime las librerías allí y las usa.
    Por eso notarás que el archivo .exe puede pesar entre 30MB y 60MB; ese peso es, básicamente, Pandas y el motor de Python comprimidos.


----------------------------------------------
AÑADIDOS:



-------------------
Posibles MEJORAS en el futuro:
- recortar pagina de pdf para crear otro pdf. 
- Unir 4 puntos y encuadrar la imagen ahí. 
- Seleccionar 2 imagenes/pdf en forma de dni, y darle forma de pdf_dni_dosCaras

