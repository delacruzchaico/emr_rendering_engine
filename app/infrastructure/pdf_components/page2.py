# app/infrastructure/pdf_components/page2.py
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
from .common import crear_tabla_ficha, get_dynamic_style
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import TableStyle
def render_ficha_trompas_ovarios(story, row,  styles):
    import app.infrastructure.database as db
    """
    Traducción de ficha_trompas_ovarios a ReportLab.
    """
    # 1. Extraemos la fila de la data (asumiendo que viene en el dict principal)
#    row = data.get('utero_ecografia', {}) # En tu PHP usas la misma tabla maestra
    
    # 2. Factores de Riesgo (Usando tu función de bits)
    factores_riesgo = db.get_flag_values( 'factores_riesgo', row.get('riesgo_anexos_flags'))

    # 3. Masas (Simulando el get_masas del PHP)
    td_masas = row.get('td_masas') or ""
    ti_masas = row.get('ti_masas') or ""
    od_masas = row.get('od_masas') or ""
    oi_masas = row.get('oi_masas') or ""

    # --- Lógica de TROMPAS ---
    td_info = f"Derecha {row.get('td_info')}" if row.get('td_info') else ""
    ti_info = f"Izquierda {row.get('ti_info')}" if row.get('ti_info') else ""
    
    info_trompas = f"{td_info} {td_masas} {ti_info} {ti_masas}".strip()
    if not info_trompas:
        info_trompas = "Sin Alteraciones"

    # --- Lógica de OVARIO DERECHO ---
    od_long = row.get('od_longitud', 0)
    od_ap = row.get('od_antero_posterior', 0)
    od_trans = row.get('od_transverso', 0)
    
    od_medidas = f"De {od_long}mm. x {od_ap}mm. "
    if od_trans > 0:
        od_medidas += f" x {od_trans}mm. "

    if od_long > 0 or od_ap > 0 or od_trans > 0:
        od_info_final = f"{od_medidas}{row.get('od_info') or ''} {od_masas}"
    else:
        od_info_final = f"{row.get('od_info') or ''} {od_masas}"

    # --- Lógica de OVARIO IZQUIERDO ---
    oi_long = row.get('oi_longitud', 0)
    oi_ap = row.get('oi_antero_posterior', 0)
    oi_trans = row.get('oi_transverso', 0)

    oi_medidas = f"De {oi_long}mm. x {oi_ap}mm. "
    if oi_trans > 0:
        oi_medidas += f" x {oi_trans}mm. "

    if oi_long > 0 or oi_ap > 0 or oi_trans > 0:
        oi_info_final = f"{oi_medidas}{row.get('oi_info') or ''} {oi_masas}"
    else:
        oi_info_final = f"{row.get('oi_info') or ''} {oi_masas}"

    # 4. RENDERIZADO DE TABLA
    # Estilos de celda
    style_b = styles['Normal'].clone('StyleB', fontName='Calibri-Bold', fontSize=10)
    style_n = styles['Normal'].clone('StyleN', fontName='Calibri', fontSize=10)
    header_style = styles['Normal'].clone('Header', fontName='Calibri-Bold', fontSize=12, leading=16, spaceBefore=0)
    # Estilo centrado para el título del examen
    header_center = styles['Normal'].clone('HeaderCenter', fontName='Calibri-Bold', fontSize=12, alignment=1)

    # Definimos anchos basados en tus wc1=25, wc2=45, wc3=98 -> Total 168mm (16.8cm)
    col_widths = [2.3 * cm, 14.5 * cm] # Unimos wc2 y wc3 para el contenido

    tabla_datos = [
        [Paragraph("CHEQUEO DE TROMPAS Y OVARIOS", header_style), ""],
        [Paragraph(f"<b>FACTORES DE RIESGO:</b>  {factores_riesgo}", style_n), ""],
        [Paragraph("EXAMEN ECOGRÁFICO", header_center), ""],
        [Paragraph("A. TROMPAS", style_b), Paragraph(info_trompas, style_n)],
        [Paragraph("B. OVARIO<br/>DERECHO", style_b), Paragraph(od_info_final, style_n)],
        [Paragraph("B. OVARIO<br/>IZQUIERDO", style_b), Paragraph(oi_info_final, style_n)]
    ]

    t = Table(tabla_datos, colWidths=col_widths, rowHeights=[0.5*cm,0.5*cm,0.5*cm,1.5*cm,1.5*cm,1.5*cm],hAlign='LEFT')

    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
        ('SPAN', (0, 0), (1, 0)),        # Span título inicial
        ('SPAN', (0, 1), (1, 1)),        # Span factores riesgo
        ('SPAN', (0, 2), (1, 2)),        # Span título examen
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))

    story.append(t)

def render_ficha_mamas(story, row, styles):
    import app.infrastructure.database as db
    """
    Traducción de ficha_mamas a ReportLab.
    Maneja examen clínico y hallazgos ecográficos bilaterales.
    """
    # 1. Extraemos la fila de la data
#    row = data.get('mama_ecografia', {})

    # 2. Factores de Riesgo (Bitmask)
    factores_riesgo = db.get_flag_values('factores_riesgo', row.get('factores_riesgo_flags'))

    # 3. Preparación de estilos
    style_b = styles['Normal'].clone('StyleB', fontName='Calibri-Bold', fontSize=11, leading=11)
    style_n = styles['Normal'].clone('StyleN', fontName='Calibri', fontSize=10, leading=10)

    # Estilo para texto largo (el que antes era tamaño 8)
    style_small = styles['Normal'].clone('StyleSmall', fontName='Calibri', fontSize=7, leading=7)


    header_center = styles['Normal'].clone('HeaderCenter', fontName='Calibri-Bold', fontSize=12, alignment=1)

    # 4. Lógica de fuentes dinámicas (reemplaza el if strlen > 250)
    def get_content_style(text):
        if text and len(str(text)) > 250:
            return style_small
        return style_n

    # 5. RENDERIZADO DE TABLA
    # Anchos basados en wc1=45, wc2=40, wc3=83 -> Total 168mm (16.8cm)
    col_widths = [2 * cm, 15 * cm] # wc1 y (wc2+wc3)
    examen_clinico = row.get('info') or ""
    tabla_datos = [
        [Paragraph("CHEQUEO DE MAMAS", style_b), ""],
        [Paragraph(f"<b>FACTORES DE RIESGO:</b> {factores_riesgo}", style_n), ""],
        [Paragraph(f"<b>EXAMEN CLÍNICO:</b> {examen_clinico}",style_n), "" ],
        [Paragraph("EXAMEN ECOGRÁFICO", header_center), ""],
        [Paragraph("MAMA DERECHA:", style_b), 
         Paragraph(row.get('mama_derecha') or "", get_content_style(row.get('mama_derecha')))],
        [Paragraph("MAMA IZQUIERDA:", style_b), 
         Paragraph(row.get('mama_izquierda') or "", get_content_style(row.get('mama_izquierda')))]
    ]

    t = Table(tabla_datos, colWidths=col_widths,rowHeights=[0.5*cm, 0.5*cm, 0.5*cm,0.5*cm,2.5*cm,2.5*cm],hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
        ('SPAN', (0, 0), (1, 0)),        # Span título inicial
        ('SPAN', (0, 1), (1, 1)),        # Span factores riesgo
        ('SPAN', (0, 2), (1, 2)),        # Span examen clínico
        ('SPAN', (0, 3), (1, 3)),        # Span título examen ecográfico
        ('GRID', (0, 1), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))

    story.append(t)

def render_ficha_impresion_dx(story, diagnosticos, styles):
    """
    Traduce ficha_impresion_diagnostica.
    Obtiene los diagnósticos marcados y los organiza en dos columnas.
    """
    # 1. Obtención de datos (Simulando el modelo visitas_listadosModel)
    # Deberás tener una función que ejecute: 
    # SELECT * FROM visitas_impresion_dx WHERE visita_id = ...
    # diagnosticos = get_lista_impresion_dx(engine, visita_id)
    
    checked_items = [row['txt_item'] for row in diagnosticos if row.get('checked') == '1']
    
    if not checked_items:
        return # Si no hay nada, no renderizamos la sección

    # 2. Estilos
    style_header = styles['Normal'].clone('DxHeader', fontName='Calibri-Bold', fontSize=12)
    style_item = styles['Normal'].clone('DxItem', fontName='Calibri', fontSize=10,leading=10)
    style_item_small = styles['Normal'].clone('DxItemSmall', fontName='Calibri', fontSize=9, leading=9,spaceBefore=0,spaceAfter=0)

    # 3. Lógica de columnas
    # En PHP calculabas 6 líneas por columna. Aquí dividimos la lista a la mitad.
    mid = (len(checked_items) + 1) // 2
    col1_items = checked_items[:mid]
    col2_items = checked_items[mid:]

    # Construimos los strings con numeración continua
    def build_buffer(items, start_index):
        buffer_str = ""
        for i, text in enumerate(items):
            buffer_str += f"{start_index + i}. {text}<br/>"
        return buffer_str

    # Determinamos si el texto es muy denso para bajar la fuente (como hacías con lineas > 13)
    current_style = style_item_small if len(checked_items) > 13 else style_item

    # 4. Creación de la Tabla
    # 168mm totales -> 8.4cm por columna
    col_widths = [8.5 * cm, 8.5 * cm]
    
    # Fila de título

    theader=[[Paragraph("IMPRESIÓN DIAGNÓSTICA", style_header)]]
    t1=Table(theader,colWidths=[17*cm],rowHeights=[0.5*cm],hAlign='LEFT')
    t1.setStyle(TableStyle([ 
        ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    story.append(t1)
    # Contenido en dos columnas
    content_table_data = [[
        Paragraph(build_buffer(col1_items, 1), current_style),
        Paragraph(build_buffer(col2_items, mid + 1), current_style)
    ]]

    t = Table(content_table_data, colWidths=col_widths,rowHeights=[3*cm],hAlign='LEFT')
    t.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.3, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('MINHEIGHT', (0, 0), (-1, -1), 0.5 * cm), # Altura mínima
    ]))

    story.append(t)

def render_ficha_recomendaciones(story, recomendaciones, styles):
    """
    Traduce ficha_recomendaciones.
    Renderiza la lista de recomendaciones y la fila de Próxima Cita.
    """
    # 1. Obtención de datos

    checked_items = [row['txt_item'] for row in recomendaciones if row.get('checked') == '1']
    
    # 2. Preparación de estilos
    style_header = styles['Normal'].clone('RecHeader', fontName='Calibri-Bold', fontSize=12)
    # Aquí definimos el leading (line-height)
    style_item = styles['Normal'].clone('RecItem', fontName='Calibri', fontSize=10, leading=12)
    style_item_small = styles['Normal'].clone('RecItemSmall', fontName='Calibri', fontSize=9, leading=10.5)

    # 3. Construcción del buffer de texto
    buffer_text = ""
    for i, txt in enumerate(checked_items, 1):
        buffer_text += f"{i}. {txt}<br/>"

    # Si hay más de 6, bajamos un poco la fuente como en tu lógica de SmartCell
    current_style = style_item_small if len(checked_items) > 6 else style_item

    # 4. Tabla de Recomendaciones
    
    t1=Table([[Paragraph("RECOMENDACIONES", style_header)]],
             colWidths=[17*cm],rowHeights=[0.4*cm],hAlign='LEFT')
    t1.setStyle(TableStyle([ 
        ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))

    story.append(t1)
    rec_table = Table([[Paragraph(buffer_text or "Sin recomendaciones específicas.", current_style)]], 
                      colWidths=[17 * cm],rowHeights=[2.5*cm],hAlign='LEFT')
    rec_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4), # Un poco de aire abajo
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('MINHEIGHT', (0, 0), (-1, -1), 0.5 * cm)
    ]))
    story.append(rec_table)

def render_proxima_cita(story, data_informe, styles):
    # 2. Preparación de estilos
    style_header = styles['Normal'].clone('RecHeader', fontName='Calibri-Bold', fontSize=12)
    # Aquí definimos el leading (line-height)
    style_item = styles['Normal'].clone('RecItem', fontName='Calibri', fontSize=10, leading=12)
    style_item_small = styles['Normal'].clone('RecItemSmall', fontName='Calibri', fontSize=10, leading=10.5)

    # 5. Fila de Próxima Cita
    # data_informe viene de tu tabla v121_informes
    proxima_cita = data_informe.get('proxima_cita') or ""
    
    cita_data = [
        [Paragraph("PRÓXIMA CITA:", style_header), Paragraph(proxima_cita, style_item)]
    ]
    
    cita_table = Table(cita_data, colWidths=[4 * cm, 13 * cm],rowHeights=[0.5*cm],hAlign='LEFT')
    cita_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (0, 0), colors.lightgrey), # Fondo gris para el label
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(cita_table)

def render_ficha_recomendaciones_generales(story, styles):
    """
    Traduce ficha_recomendaciones_generales.
    Texto fijo de carácter preventivo al final de la página 2.
    """
    # 1. Preparación de estilos
    # Usamos fuente 10 para el título y 8 para el cuerpo (como en tu PHP)
    style_header = styles['Normal'].clone('RecGenHeader', 
                                          fontName='Calibri-Bold', 
                                          fontSize=9, 
                                          alignment=1) # Centrado
    
    style_body = styles['Normal'].clone('RecGenBody', 
                                        fontName='Calibri', 
                                        fontSize=9,
                                        leading=9, 
                                        alignment=0) # Izquierda

    # 2. El texto fijo (respetando tus saltos de línea)
    texto_generales = (
        "Cumplir con las recomendaciones indicadas a la brevedad posible. "
        "A las mujeres mayores de 40 años se les recomienda una mamografía bilateral anualmente."
        "<b>Se recomienda un Chequeo Integral Ginecológico cada 12 meses.</b>"
    )

    # 3. Construcción de la tabla
    data = [
        [Paragraph("RECOMENDACIONES GENERALES", style_header)],
        [Paragraph(texto_generales, style_body)]
    ]

    t = Table(data, colWidths=[17 * cm],rowHeights=[0.3*cm,0.7*cm],hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.lightgrey),
        ('GRID', (0, 1), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))

    story.append(t)


def render(story, visita_id, styles):
    import app.infrastructure.database as db
    """
    Encapsula toda la estructura de la Página 1.
    'data' debe ser un diccionario que contenga 'paciente', 'antecedentes', etc.
    """
#    visita_data = db.get_visita_data(visita_id)
    utero_ecografia_data=db.get_utero_ecografia_data(visita_id)
    render_ficha_trompas_ovarios(story, utero_ecografia_data, styles)
    
    story.append(Spacer(1, 0.2 * cm))
    mama_ecografia_data=db.get_v121_mama_ecografia(visita_id)
    render_ficha_mamas(story, mama_ecografia_data, styles)

    story.append(Spacer(1, 0.2 * cm))
    impresion_dx_data=db.get_lista_impresion_dx(visita_id)
    render_ficha_impresion_dx(story, impresion_dx_data, styles)

    story.append(Spacer(1, 0.2 * cm))
    recomendaciones_data=db.get_lista_recomendaciones(visita_id)
    render_ficha_recomendaciones(story, recomendaciones_data, styles)
    informe_data=db.get_informe_data(visita_id)
    render_proxima_cita(story,informe_data,styles)

    story.append(Spacer(1, 0.2 * cm))
    render_ficha_recomendaciones_generales(story,styles)
    story.append(Spacer(1, 0.1 * cm))
