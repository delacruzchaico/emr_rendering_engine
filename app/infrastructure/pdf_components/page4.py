from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
from .common import crear_tabla_ficha, get_dynamic_style
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import TableStyle
from datetime import date

def render_info_frotis(story, data_frotis, styles):
    import app.infrastructure.database as db
    """
    Traduce info_frotis.
    Maneja valoración hormonal, microbiología, morfología y diagnóstico.
    """
    row = data_frotis
    
    # 1. Extracción y normalización de flags (Equivalente a strtolower + get_flag_values)
    # Valoración Hormonal
    vh_cs = db.get_flag_values( 'vhormo_cs', row.get('vhormo_cs_flags')).lower()
    vh_ci = db.get_flag_values( 'vhormo_ci', row.get('vhormo_ci_flags')).lower()
    vh_cb = db.get_flag_values( 'vhormo_cb', row.get('vhormo_cb_flags')).lower()
    vh_cp = db.get_flag_values( 'vhormo_cp', row.get('vhormo_cp_flags')).lower()
    
    # Estudio Microbiológico
    em_bac = db.get_flag_values( 'emicro_bacilos', row.get('emicro_bacilos_flags')).lower()
    em_coc = db.get_flag_values( 'emicro_coco', row.get('emicro_coco_flags')).lower()
    em_hif = db.get_flag_values( 'emicro_hifas', row.get('emicro_hifas_flags')).lower()
    em_can = db.get_flag_values( 'emicro_candida', row.get('emicro_candida_flags')).lower()
    
    # Morfología Celular
    morf = db.get_flag_values( 'morfologia_celular', row.get('morfologia_celular_flags')).lower()
    morf_inv = db.get_flag_values( 'morfologia_celular_invasion', row.get('morfologia_celular_invasion_flags')).lower()
    morf_info = (row.get('morfologia_celular_info') or "").lower()
    
    morfologia_celular_completa = f"{morf} {morf_inv} {morf_info}".strip()
    
    # Diagnóstico (Lista de checks)
    # dataset() en tu PHP parece retornar la lista completa de opciones indicando 'checked'
    diagnosticos = db.get_flag_dataset('frotis_dx', row.get('frotis_dx_flags'))

    # 2. Estilos
    st_b12 = styles['Normal'].clone('B12', fontName='Calibri-Bold', fontSize=12, leading=14)
    st_n10 = styles['Normal'].clone('N10', fontName='Calibri', fontSize=10, leading=12)

    # 3. IMPRESIÓN DE DATOS
    
    # --- 1. VALORACIÓN HORMONAL ---
    story.append(Paragraph("1. VALORACIÓN HORMONAL:", st_b12))
    if vh_cs: story.append(Paragraph(f"Células superficiales {vh_cs}", st_n10))
    if vh_ci: story.append(Paragraph(f"Células intermedias {vh_ci}", st_n10))
    if vh_cb: story.append(Paragraph(f"Células basales {vh_cb}", st_n10))
    if vh_cp: story.append(Paragraph(f"Células parabasales {vh_cp}", st_n10))
    story.append(Spacer(1, 0.4*cm))

    # --- 2. ESTUDIO MICROBIOLÓGICO ---
    story.append(Paragraph("2. ESTUDIO MICROBIOLÓGICO:", st_b12))
    if em_bac: story.append(Paragraph(f"Bacilos {em_bac}", st_n10))
    if em_coc: story.append(Paragraph(f"Cocos {em_coc}", st_n10))
    if em_hif: story.append(Paragraph(f"Hifas {em_hif}", st_n10))
    if em_can: story.append(Paragraph(f"Candida {em_can}", st_n10))
    story.append(Spacer(1, 0.4*cm))

    # --- 3. MORFOLOGÍA CELULAR ---
    story.append(Paragraph("3. MORFOLOGÍA CELULAR:", st_b12))
    story.append(Paragraph(morfologia_celular_completa, st_n10))
    story.append(Spacer(1, 0.4*cm))

    # --- 4. DIAGNÓSTICO ---
    story.append(Paragraph("4. DIAGNÓSTICO", st_b12))
    for d in diagnosticos:
        if d.get('checked') == 1:
            # Simulamos el Cell(10) con una indentación en el párrafo o &nbsp;
            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- {d['flag']}", st_n10))

def render_info_pap(story, data, styles):
    import app.infrastructure.database as db
    """
    Traduce info_pap. Renderiza el informe citológico del Papanicolaou.
    """
    pap_list = data.get('pap',[])
    if isinstance(pap_list, list) and len(pap_list) > 0:
        row = pap_list[0]
    else:
        # Si no hay datos, creamos un diccionario vacío para que el resto
        # de los .get() de la página no exploten
        row = {}

    if not row or not row['fecha_resultado'] or str(row['fecha_resultado']) == '0000-00-00':
        return

    # Estilos
    st_b12 = styles['Normal'].clone('B12', fontName='Calibri-Bold', fontSize=11, leading=12)
    st_n10 = styles['Normal'].clone('N10', fontName='Calibri', fontSize=10, leading=10,leftIndent=1.5*cm)
    
    # 1. Cabecera del PAP
    header_data = [
        [Paragraph(f"FECHA: {row['fecha_muestra']}", st_b12), 
         Paragraph(f"N° PAP: {row['nro_pap']}", st_b12)]
    ]
    t_header = Table(header_data, colWidths=[5*cm, 3*cm],hAlign='LEFT')
    story.append(t_header)
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("MÉDICO SOLICITANTE:", st_b12))
    # 'medico' viene de la tabla visitas principal
    medico = data.get('visita', {}).get('medico', '')
    story.append(Paragraph(f"Dr. {medico}", st_b12))
    story.append(Spacer(1, 0.4*cm))

    # 2. Secciones con Flags
    secciones = [
        ("1. CALIDAD DE LA MUESTRA:", 'calidad_muestra', 'calidad_muestra_flags'),
        ("2. TROFISMO DEL EPITELIO:", 'trofismo_epitelio', 'trofismo_epitelio_flags'),
        ("3. PROCESO INFECCIOSO:", 'proceso_infeccioso', 'proceso_infeccioso_flags'),
        ("4. INFILTRADO INFLAMATORIO:", 'infiltrado_inflama', 'infiltrado_inflama_flags'),
        ("5. CAMBIOS REACTIVOS:", 'cambios_reactivos', 'cambios_reactivos_flags'),
    ]

    for titulo, key_emr, key_row in secciones:
        story.append(Paragraph(titulo, st_b12))
        valor = db.get_flag_values( key_emr, row.get(key_row))
        # Sangría simulada con espacio
        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{valor}.", st_n10))
        story.append(Spacer(1, 0.2*cm))

    # 3. DIAGNÓSTICO CITOLÓGICO
    story.append(Paragraph("6. DIAGNÓSTICO CITOLÓGICO:", st_b12))
    
    if str(row.get('alterado')) == '1':
        citologia = str(row.get('citologia_resultado') or "").upper()
    else:
        citologia = 'NEGATIVO A CÉLULAS NEOPLÁSICAS'

    if row.get('citologia_resultado_info'):
        citologia += f"<br/>{row['citologia_resultado_info']}"

    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>{citologia}.</b>", st_b12))
    story.append(Spacer(1, 0.4*cm))

    # 4. OBSERVACIONES
    story.append(Paragraph("7. OBSERVACIONES:", st_b12))
    pap_info_flags = db.get_flag_values( 'pap_info', row.get('pap_info_flags'))
    
    if pap_info_flags or row.get('info'):
        obs_txt = f"{pap_info_flags}. {row.get('info', '')}".strip()
        obs_txt = obs_txt.rstrip('.') # Limpiar puntos extra
        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{obs_txt}.", st_n10))
    else:
        story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;Ninguno.", st_n10))

def render_info_pap_2columnas(story, data, styles):
    import app.infrastructure.database as db
    """
    Traduce info_pap_2columnas.
    Usa una estructura de tabla para alinear etiquetas y valores perfectamente.
    """
    # row = data.get('pap',[])[0]
    pap_list = data.get('pap',[])
    if isinstance(pap_list, list) and len(pap_list) > 0:
        row = pap_list[0]
    else:
        # Si no hay datos, creamos un diccionario vacío para que el resto
        # de los .get() de la página no exploten
        row = {}


    if not row or not row.get('fecha_resultado') or str(row.get('fecha_resultado')) == '0000-00-00':
        return

    # 1. Definición de Estilos
    st_b12 = styles['Normal'].clone('B12', fontName='Calibri-Bold', fontSize=12, leading=14)
    st_n10 = styles['Normal'].clone('N10', fontName='Calibri', fontSize=10, leading=12)

    # 2. Preparación de Datos de la Tabla
    # Estructura: [ [Etiqueta, Valor], ... ]

    # Médico Solicitante
    medico = data.get('visita', {}).get('medico', '')

    # Diagnóstico Citológico
    if str(row.get('alterado')) == '1':
        citologia = str(row.get('citologia_resultado') or "").upper()
    else:
        citologia = 'NEGATIVO A CÉLULAS NEOPLÁSICAS'

    if row.get('citologia_resultado_info'):
        citologia += f"\n{row['citologia_resultado_info']}"

    # Observaciones
    pap_info_flags = db.get_flag_values( 'pap_info', row.get('pap_info_flags'))
    obs_txt = "Ninguno."
    if pap_info_flags or row.get('info'):
        obs_txt = f"{pap_info_flags} {row.get('info', '')}".strip().rstrip('.') + "."


    proceso_infeccioso = db.get_flag_values( 'proceso_infeccioso', row.get('proceso_infeccioso_flags'))

    if proceso_infeccioso=="": proceso_infeccioso="Ninguno";

    cambios_reactivos=db.get_flag_values( 'cambios_reactivos', row.get('cambios_reactivos_flags'))

    if cambios_reactivos=="": cambios_reactivos="Ninguno"
    # 3. Construcción de filas (Etiqueta en st_b12, Valor en st_n10)
    rows = [
        [Paragraph(f"FECHA: {row['fecha_muestra']}", st_b12), 
         Paragraph(f"N° PAP: {row['nro_pap']}", st_b12)],

        [Paragraph("MÉDICO SOLICITANTE:", st_b12), 
         Paragraph(f"Dr. {medico}", st_n10)],

        [Paragraph("1. CALIDAD DE LA MUESTRA:", st_b12), 
         Paragraph(f"{db.get_flag_values( 'calidad_muestra', row.get('calidad_muestra_flags'))}.", st_n10)],

        [Paragraph("2. TROFISMO DEL EPITELIO:", st_b12), 
         Paragraph(f"{db.get_flag_values( 'trofismo_epitelio', row.get('trofismo_epitelio_flags'))}.", st_n10)],

        [Paragraph("3. PROCESO INFECCIOSO:", st_b12), 
         Paragraph(f"{proceso_infeccioso}.", st_n10)],

        [Paragraph("4. INFILTRADO INFLAMATORIO:", st_b12), 
         Paragraph(f"{db.get_flag_values( 'infiltrado_inflama', row.get('infiltrado_inflama_flags'))}.", st_n10)],

        [Paragraph("5. CAMBIOS REACTIVOS:", st_b12),
         Paragraph(f"{cambios_reactivos}.", st_n10)],

        [Paragraph("6. DIAGNÓSTICO CITOLÓGICO:", st_b12), 
         Paragraph(f"<b>{citologia}.</b>", st_b12)],

        [Paragraph("7. OBSERVACIONES:", st_b12), 
         Paragraph(obs_txt, st_n10)],
    ]

    # 4. Creación de la Tabla con anchos fijos (9cm y 7.8cm para sumar 16.8cm)
    t = Table(rows, colWidths=[9*cm, 8*cm])

    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6), # Reemplaza tus Ln()
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        # ('GRID', (0,0), (-1,-1), 0.5, colors.grey), # Activa para debug de alineación
    ]))

    story.append(t)


def render(story, visita_id, styles):
    import app.infrastructure.database as db
    """
    Encapsula toda la estructura de la Página 1.
    'data' debe ser un diccionario que contenga 'paciente', 'antecedentes', etc.
    """
    #    visita_data = db.get_visita_data(visita_id)
    frotis_data=db.get_frotis_data(visita_id)    
    #    render_info_frotis(story, frotis_data, styles)
    frotis_content = []
    render_info_frotis(frotis_content, frotis_data, styles)
    # 2. Metemos ese contenido dentro de una Tabla de una sola celda
    # Fijamos el ancho (16.8cm) y el ALTO (ej. 10cm)
    # Si el frotis es corto, la tabla igual medirá 10cm.
    # Si el frotis es largo, la tabla crecerá (puedes limitarlo)
    ancho = 16.8 * cm
    alto_fijo = 13 * cm 
    t_frotis = Table([[frotis_content]], colWidths=[ancho], rowHeights=[alto_fijo])
    
    t_frotis.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'), # El texto empieza arriba
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        # ('GRID', (0,0), (-1,-1), 0.5, colors.red), # Solo para debug
    ]))
    
    story.append(t_frotis)

    visita_data=db.get_visita_data(visita_id)

    data={'pap':db.filter_visita_pap(visita_id),'visita':visita_data}

    fecha_limite = date(2022, 4, 1)
    if visita_data.get('sede_id')==1 or visita_data.get('fecha')<=fecha_limite:
        render_info_pap(story, data, styles)
    else:
        render_info_pap_2columnas(story, data, styles)
