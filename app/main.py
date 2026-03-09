import logging
import warnings
import os

# 1. SILENCIAR WARNINGS DE LIBRERÍAS (Requests / Urllib3)
# Esto detiene los mensajes de "doesn't match a supported version"
warnings.filterwarnings("ignore", message=".*urllib3.*")
warnings.filterwarnings("ignore", category=UserWarning)

# 2. SILENCIAR SQLALCHEMY (ENGINE Y POOL)
# Forzamos el nivel a ERROR para que no muestre los SELECT/BEGIN/ROLLBACK
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.pool').setLevel(logging.ERROR)

# 3. OPCIONAL: Si usas Gunicorn (por el log de 'Booting worker')
# Puedes ajustar el nivel de log del servidor si te molesta el INFO
logging.getLogger('gunicorn.error').setLevel(logging.WARNING)



from flask import Flask, request, jsonify
from app.infrastructure.pdf_generator import generate_medical_report
from datetime import datetime, timedelta

# 1. Silenciar el motor de SQLAlchemy
sql_logger = logging.getLogger('sqlalchemy.engine')
sql_logger.setLevel(logging.ERROR) # Solo errores críticos
sql_logger.propagate = False       # ¡ESTA ES LA CLAVE! Evita que suba al log de Flask

# 2. Silenciar el pool de conexiones (por si acaso)
logging.getLogger('sqlalchemy.pool').setLevel(logging.ERROR)

logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)

def es_solicitud_valida(pdf_last_request):
    # Si viene vacío, Nulo o con la fecha 'cero' de MySQL
    if not pdf_last_request or pdf_last_request == '0000-00-00 00:00:00':
        print("DEBUG: Fecha inválida o vacía detectada.")
        return False
    
    if isinstance(pdf_last_request, str):
        try:
            # Limpiamos milisegundos si existen y convertimos
            clean_date = pdf_last_request.split('.')[0]
            pdf_last_request = datetime.strptime(clean_date, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return False

    ahora = datetime.now()
    diferencia = (ahora - pdf_last_request).total_seconds()
    
    # Validamos que esté en el rango de 30 segundos
    return 0 <= diferencia <= 30


app = Flask(__name__)

app.config['SQLALCHEMY_ECHO'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint técnico para que Docker sepa que el motor está vivo."""
    return jsonify({
        "status": "operational",
        "service": "emr-rendering-engine",
        "version": "1.0.0"
    }), 200

@app.route('/api/v1/render/chig/<int:visita_id>',methods=['GET'])
def render_by_id(visita_id):
    from app.infrastructure.database import get_informe_data
    # datos = get_patient_data(id)
    # Llamamos a tu generador de PDF que ya funciona
    formato = request.args.get('formato', '').lower()  # 'estandar' / sorrentino / sorrentino_xl
    bgimage = request.args.get('bgimage', '').lower()  # con imagenes de fondo
    rubrica = request.args.get('rubrica', '').lower()
    extra = request.args.get('extra', '').lower()

    informe_data = get_informe_data(visita_id)
        
    pdf_last_request = informe_data.get('pdf_last_request');
    
    #    if es_solicitud_valida(pdf_last_request):
    return generate_medical_report(visita_id,formato,bgimage,rubrica,extra)    

    # 2. SI NO ES VÁLIDO (Aquí es donde fallaba antes)
    # Debes retornar un mensaje y un código de error (403 Forbidden)
    print(f"DEBUG: Bloqueando generación para visita {visita_id} por timestamp expirado {pdf_last_request}.")
    return {
        "status": "error",
        "message": "El token de seguridad ha expirado (30s). Por favor, intente generar el informe nuevamente."
    }, 403


@app.route('/render/<int:id>')
def test_data(id):
    from app.infrastructure.database import get_patient_data
    datos = get_patient_data(id)
    if datos:
        return datos  # Flask automáticamente convierte diccionarios a JSON
    return "No hay datos", 404
