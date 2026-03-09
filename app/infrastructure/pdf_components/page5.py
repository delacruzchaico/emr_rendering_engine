from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
from .common import crear_tabla_ficha, get_dynamic_style
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import TableStyle

def get_masas_info(visita_id, ubicacion):        
    import app.infrastructure.database as db
    """
    Convierte la lista de masas en un solo bloque de texto legible.
    """
    masas = db.get_masas_lista( visita_id, ubicacion)
    if not masas:
        return ""

    lineas = []
    for m in masas:
        # Ejemplo de formato: "CIE10: Miomatosis - Info adicional"
        # Puedes ajustar esto según qué columnas tenga tu tabla vum
        desc = f"- {m['dec10']}" if m['dec10'] else "- Hallazgo"
        if m.get('info'):
            desc += f": {m['info']}"
        
        # Si tienes medidas en la tabla de masas (ej. diametro1, diametro2)
        if m.get('diametro1'):
            medida = f" ({m['diametro1']}mm"
            if m.get('diametro2'): medida += f" x {m['diametro2']}mm"
            medida += ")"
            desc += medida
            
        lineas.append(desc)

    return "\n".join(lineas)

def render_info_utero(story, data_utero,  styles):
    import app.infrastructure.database as db # Importamos tu módulo de base de datos
    """
    Traduce info_utero de PHP a ReportLab.
    """
    row = data_utero
    visita_id=row.get('visita_id')
    # Estilos
    st_bu12 = styles['Normal'].clone('BU12', fontName='Calibri-Bold', fontSize=12, underline=True)
    st_b10 = styles['Normal'].clone('B10', fontName='Calibri-Bold', fontSize=10, leading=10)
    st_n10 = styles['Normal'].clone('N10', fontName='Calibri', fontSize=10, leading=10)

    # --- LÓGICA DE DATOS ---
    utero_situacion = db.get_flag_values('utero_posicion', row.get('posicion_flag'))
    utero_dimensiones = f"De {row['utero_longitud']}mm. x {row['utero_antero_posterior']}mm. x {row['utero_transverso']}mm."
    utero_bordes = db.get_flag_values('utero_bordes', row.get('bordes_flag'))
    utero_ecogenicidad = db.get_flag_values('utero_ecogenicidad', row.get('ecogenicidad_flag'))
    
    utero_masas = get_masas_info(visita_id, 'utero')
    cervix_masas = get_masas_info(visita_id, 'cervix')
    endometrio_masas = get_masas_info(visita_id, 'endometrio')
    
    # Endometrio
    endometrio_info = ""
    if float(row.get('endometrio_grosor') or 0) > 0:
        forma = db.get_flag_values('endometrio_forma', row.get('endometrio_forma_flag'))
        endometrio_info = f"De {row['endometrio_grosor']}mm. de grosor. {forma}"

    # Ovarios (Helper para medidas)
    def format_ovario(long, ap, trans, info, masas_txt):
        medidas = f"De {long}mm x {ap}mm"
        if float(trans or 0) > 0: medidas += f" x {trans}mm."
        else: medidas += ". "
        
        if any([float(long or 0), float(ap or 0), float(trans or 0)]):
            return f"{medidas} {info or ''} {masas_txt}".strip()
        return f"{info or ''} {masas_txt}".strip()

    od_info = format_ovario(row['od_longitud'], row['od_antero_posterior'], row['od_transverso'], row['od_info'], get_masas_info(visita_id, 'ovario_derecho'))
    oi_info = format_ovario(row['oi_longitud'], row['oi_antero_posterior'], row['oi_transverso'], row['oi_info'], get_masas_info(visita_id, 'ovario_izquierdo'))

    # Fondo de Saco
    vflag_liq = db.get_flag_values('fondo_saco_liquido', row.get('fondo_saco_liquido_flags'))
    vflag_dol = db.get_flag_values('fondo_saco_dolor', row.get('fondo_saco_dolor_flags'))
    liq_txt = vflag_liq if vflag_liq else "No"
    dol_txt = f" Dolor: {vflag_dol}" if vflag_dol else "Sin dolor"

    # --- RENDERIZADO (STORY) ---
    
    if row.get('tipo_ecoutero_flags') == 2:
        story.append(Paragraph("<u>ECOGRAFÍA PÉLVICA:</u>", st_bu12))
    
    story.append(Paragraph("<u>ÚTERO</u>:", st_bu12))

    if any([row['utero_longitud'], row['utero_antero_posterior'], row['utero_transverso']]):
        story.append(Paragraph(f"<b>SITUACIÓN:</b> {utero_situacion}", st_n10))
        story.append(Paragraph("<b>DIMENSIONES:</b>", st_b10))
        story.append(Paragraph(utero_dimensiones, st_n10))
        
        if utero_masas: story.append(Paragraph(utero_masas, st_n10))
        if cervix_masas: story.append(Paragraph(cervix_masas, st_n10))
        
        story.append(Paragraph(f"<b>SUPERFICIE:</b> {utero_bordes}", st_n10))
        story.append(Paragraph(f"<b>ECOGENICIDAD:</b> {utero_ecogenicidad}", st_n10))

    if row.get('utero_info'):
        story.append(Paragraph(row['utero_info'], st_n10))

    # Cervix
    if row.get('cervix_diametro') or row.get('cervix_info'):
        txt = f"<b>CERVIX:</b> {row['cervix_diametro']}mm. " if row.get('cervix_diametro') else "<b>CERVIX:</b> "
        txt += row.get('cervix_info') or ""
        story.append(Paragraph(txt, st_n10))

    # Endometrio
    if endometrio_info or row.get('endometrio_info') or endometrio_masas:
        story.append(Paragraph("<b>ENDOMETRIO:</b>", st_b10))
        if endometrio_info: story.append(Paragraph(endometrio_info, st_n10))
        if row.get('endometrio_info'): story.append(Paragraph(row['endometrio_info'], st_n10))
        if endometrio_masas: story.append(Paragraph(endometrio_masas, st_n10))

    # Douglas
    story.append(Paragraph("<b>FONDO DE SACO DOUGLAS:</b>", st_b10))
    if row['utero_longitud'] or row['utero_transverso']:
        story.append(Paragraph(f"Presencia de líquido {liq_txt}, {dol_txt}", st_n10))
    else:
        story.append(Paragraph("NO SE EXAMINÓ", st_n10))

    story.append(Spacer(1, 0.4*cm))

    # Anexos
    for lado, label in [('td', 'DERECHO'), ('ti', 'IZQUIERDO')]:
        story.append(Paragraph(f"<u>ANEXO {label}:</u>", st_bu12))
        
        # Trompas
        story.append(Paragraph(f"<b>TROMPA {label}:</b>", st_b10))
        info_trompa = row.get(f'{lado}_info') or "Sin Alteraciones"
        # Simulamos el desplazamiento con leftIndent si quieres, o simple
        story.append(Paragraph(info_trompa, st_n10))
        
        t_masas = get_masas_info(visita_id, f'trompa_{"derecha" if lado=="td" else "izquierda"}')
        if t_masas: story.append(Paragraph(t_masas, st_n10))
        
        # Ovarios
        story.append(Paragraph(f"<b>OVARIO {label}:</b>", st_b10))
        story.append(Paragraph(od_info if lado == 'td' else oi_info, st_n10))
        story.append(Spacer(1, 0.4*cm))

def render_info_utero_extra(story, data_utero,  styles):
    import app.infrastructure.database as db # Importamos tu módulo de base de datos
    """
    Traduce info_utero de PHP a ReportLab.
    """
    row = data_utero
    visita_id=row.get('visita_id')
    # Estilos
    st_bu12 = styles['Normal'].clone('BU12', fontName='Calibri-Bold', fontSize=12, underline=True)
    st_b10 = styles['Normal'].clone('B10', fontName='Calibri-Bold', fontSize=10, leading=10)
    st_n10 = styles['Normal'].clone('N10', fontName='Calibri', fontSize=10, leading=10)

    # --- LÓGICA DE DATOS ---
    utero_situacion = db.get_flag_values('utero_posicion', row.get('posicion_flag'))
    utero_dimensiones = f"De {row['utero_longitud']}mm. x {row['utero_antero_posterior']}mm. x {row['utero_transverso']}mm."
    utero_bordes = db.get_flag_values('utero_bordes', row.get('bordes_flag'))
    utero_ecogenicidad = db.get_flag_values('utero_ecogenicidad', row.get('ecogenicidad_flag'))
    
    utero_masas = get_masas_info(visita_id, 'utero')
    cervix_masas = get_masas_info(visita_id, 'cervix')
    endometrio_masas = get_masas_info(visita_id, 'endometrio')
    
    # Endometrio
    endometrio_info = ""
    if float(row.get('endometrio_grosor') or 0) > 0:
        forma = db.get_flag_values('endometrio_forma', row.get('endometrio_forma_flag'))
        endometrio_info = f"De {row['endometrio_grosor']}mm. de grosor. {forma}"

    # Ovarios (Helper para medidas)
    def format_ovario(long, ap, trans, info, masas_txt):
        medidas = f"De {long}mm x {ap}mm"
        if float(trans or 0) > 0: medidas += f" x {trans}mm."
        else: medidas += ". "
        
        if any([float(long or 0), float(ap or 0), float(trans or 0)]):
            return f"{medidas} {info or ''} {masas_txt}".strip()
        return f"{info or ''} {masas_txt}".strip()

    od_info = format_ovario(row['od_longitud'], row['od_antero_posterior'], row['od_transverso'], row['od_info'], get_masas_info(visita_id, 'ovario_derecho'))
    oi_info = format_ovario(row['oi_longitud'], row['oi_antero_posterior'], row['oi_transverso'], row['oi_info'], get_masas_info(visita_id, 'ovario_izquierdo'))

    # Fondo de Saco
    vflag_liq = db.get_flag_values('fondo_saco_liquido', row.get('fondo_saco_liquido_flags'))
    vflag_dol = db.get_flag_values('fondo_saco_dolor', row.get('fondo_saco_dolor_flags'))
    liq_txt = vflag_liq if vflag_liq else "No"
    dol_txt = f" Dolor: {vflag_dol}" if vflag_dol else "Sin dolor"

    # --- RENDERIZADO (STORY) ---
    
    if row.get('tipo_ecoutero_flags') == 2:
        story.append(Paragraph("<u>ECOGRAFÍA PÉLVICA:</u>", st_bu12))
    
    story.append(Paragraph("<u>ÚTERO</u>:", st_bu12))

    if any([row['utero_longitud'], row['utero_antero_posterior'], row['utero_transverso']]):
        story.append(Paragraph(f"<b>SITUACIÓN:</b> {utero_situacion}", st_n10))
        story.append(Paragraph(f"<b>DIMENSIONES:</b> {utero_dimensiones}", st_n10))
#        story.append(Paragraph(utero_dimensiones, st_n10))
        
        if utero_masas: story.append(Paragraph(utero_masas, st_n10))
        if cervix_masas: story.append(Paragraph(cervix_masas, st_n10))
        
        story.append(Paragraph(f"<b>SUPERFICIE:</b> {utero_bordes}", st_n10))
        story.append(Paragraph(f"<b>ECOGENICIDAD:</b> {utero_ecogenicidad}", st_n10))

    if row.get('utero_info'):
        story.append(Paragraph(row['utero_info'], st_n10))

    # Cervix
    if row.get('cervix_diametro') or row.get('cervix_info'):
        txt = f"<b>CERVIX:</b> {row['cervix_diametro']}mm. " if row.get('cervix_diametro') else "<b>CERVIX:</b> "
        txt += row.get('cervix_info') or ""
        story.append(Paragraph(txt, st_n10))

    # Endometrio
    if endometrio_info or row.get('endometrio_info') or endometrio_masas:
        story.append(Paragraph(f"<b>ENDOMETRIO:</b> {endometrio_info}", st_n10))
        # if endometrio_info: story.append(Paragraph(endometrio_info, st_n10))
        if row.get('endometrio_info'): story.append(Paragraph(row['endometrio_info'], st_n10))
        if endometrio_masas: story.append(Paragraph(endometrio_masas, st_n10))

    # Douglas
    story.append(Paragraph(f"<b>FONDO DE SACO DOUGLAS:</b> Presencia de líquido {liq_txt}, {dol_txt}", st_n10))

    story.append(Spacer(1, 0.4*cm))

    # Anexos
    for lado, label in [('td', 'DERECHO'), ('ti', 'IZQUIERDO')]:
        story.append(Paragraph(f"<u>ANEXO {label}:</u>", st_bu12))
        
        # Trompas
        story.append(Paragraph(f"<b>TROMPA {label}:</b>", st_b10))
        info_trompa = row.get(f'{lado}_info') or "Sin Alteraciones"
        # Simulamos el desplazamiento con leftIndent si quieres, o simple
        story.append(Paragraph(info_trompa, st_n10))
        
        t_masas = get_masas_info(visita_id, f'trompa_{"derecha" if lado=="td" else "izquierda"}')
        if t_masas: story.append(Paragraph(t_masas, st_n10))
        
        # Ovarios
        story.append(Paragraph(f"<b>OVARIO {label}:</b>", st_b10))
        story.append(Paragraph(od_info if lado == 'td' else oi_info, st_n10))
        story.append(Spacer(1, 0.4*cm))

def render_info_mama(story, data_mama, styles):
    """
    Traduce info_mama de PHP a ReportLab.
    Incluye lógica de reducción de fuente si el texto supera los 250 caracteres.
    """
    row = data_mama
    
    # Definición de estilos base
    st_bu10 = styles['Normal'].clone('BU10', fontName='Calibri-Bold', fontSize=10, leading=10, underline=True)
    st_n10 = styles['Normal'].clone('N10', fontName='Calibri', fontSize=10, leading=10)
    st_n8 = styles['Normal'].clone('N8', fontName='Calibri', fontSize=8, leading=8)

    # Procesar ambas mamas
    for lado in ['derecha', 'izquierda']:
        label = f"<u>MAMA {lado.upper()}</u> :"
        texto = row.get(f'mama_{lado}', '')
        
        # Título de la sección
        story.append(Paragraph(label, st_bu10))
        
        # Lógica de auto-ajuste de fuente (PHP: strlen > 250)
        if len(texto) > 250:
            estilo_elegido = st_n8
        else:
            estilo_elegido = st_n10
            
        # Añadir el contenido
        story.append(Paragraph(texto if texto else "Sin hallazgos significativos.", estilo_elegido))
        
        # Espacio entre mama derecha e izquierda
        story.append(Spacer(1, 0.3 * cm))

def render(story, visita_id, styles):
    import app.infrastructure.database as db
    """
    Encapsula toda la estructura de la Página 1.
    'data' debe ser un diccionario que contenga 'paciente', 'antecedentes', etc.
    """
    utero_data = db.get_utero_ecografia_data(visita_id)
    #     render_info_utero(story,utero_data,styles)
    # 1. Creamos una lista vacía (nuestro sub-story)
    sub_story_utero = []
    # 2. Llamamos a tu función tal cual la tienes (ella hará los .append)
    # Solo asegúrate de que tu función use la lista que le pasas
    render_info_utero(sub_story_utero, utero_data, styles)
    # 3. Insertamos el sub-story en la tabla
    # Nota: ReportLab permite pasar una lista de Flowables directamente como contenido de celda
    ancho_recuadro = 6 * cm

    tabla_contenedor = Table([[sub_story_utero]], colWidths=[ancho_recuadro],rowHeights=[12.5*cm],hAlign='LEFT')
    tabla_contenedor.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))
       
    story.append(tabla_contenedor)

    # 4. Agregamos la tabla al story principal del documento
    # story.append(tabla_contenedor)

    story.append(Spacer(1, 2.5 * cm))


    mama_data = db.get_v121_mama_ecografia(visita_id)

    sub_story_mama=[]

    render_info_mama(sub_story_mama,mama_data,styles)


    ancho_recuadro = 7 * cm
    tabla_contenedor = Table([[sub_story_mama]], colWidths=[ancho_recuadro],rowHeights=[6*cm],hAlign='LEFT')
    tabla_contenedor.setStyle(TableStyle([
#        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))


    story.append(tabla_contenedor)

def render_sorrentino(story, visita_id, styles):
    import app.infrastructure.database as db
    """
    Encapsula toda la estructura de la Página 1.
    'data' debe ser un diccionario que contenga 'paciente', 'antecedentes', etc.
    """
    utero_data = db.get_utero_ecografia_data(visita_id)
    #     render_info_utero(story,utero_data,styles)
    # 1. Creamos una lista vacía (nuestro sub-story)
    sub_story_utero = []
    
    # 2. Llamamos a tu función tal cual la tienes (ella hará los .append)
    # Solo asegúrate de que tu función use la lista que le pasas
    render_info_utero(sub_story_utero, utero_data, styles)
    # 3. Insertamos el sub-story en la tabla
    # Nota: ReportLab permite pasar una lista de Flowables directamente como contenido de celda
    ancho_recuadro = 16.5 * cm

    tabla_contenedor = Table([[sub_story_utero]], colWidths=[ancho_recuadro],rowHeights=[12.5*cm],hAlign='LEFT')
    tabla_contenedor.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))
       
    story.append(tabla_contenedor)

    # 4. Agregamos la tabla al story principal del documento
    # story.append(tabla_contenedor)

    story.append(Spacer(1, 2.5 * cm))


    mama_data = db.get_v121_mama_ecografia(visita_id)

    sub_story_mama=[]

    render_info_mama(sub_story_mama,mama_data,styles)

    #     ancho_recuadro = 7 * cm
    #     tabla_contenedor = Table([[sub_story_mama]], colWidths=[ancho_recuadro],rowHeights=[6*cm],hAlign='LEFT')
    #     tabla_contenedor.setStyle(TableStyle([
    # #        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
    #         ('VALIGN', (0,0), (-1,-1), 'TOP'),
    #         ('LEFTPADDING', (0,0), (-1,-1), 0),
    #     ]))
    story.extend(sub_story_mama)

def render_sorrentino_extra(story, visita_id, styles):
    import app.infrastructure.database as db
    """
    Encapsula toda la estructura de la Página 1.
    'data' debe ser un diccionario que contenga 'paciente', 'antecedentes', etc.
    """
    utero_data = db.get_utero_ecografia_data(visita_id)
    #     render_info_utero(story,utero_data,styles)
    # 1. Creamos una lista vacía (nuestro sub-story)
    sub_story_utero = []
    
    # 2. Llamamos a tu función tal cual la tienes (ella hará los .append)
    # Solo asegúrate de que tu función use la lista que le pasas
    render_info_utero_extra(sub_story_utero, utero_data, styles)
    # 3. Insertamos el sub-story en la tabla
    # Nota: ReportLab permite pasar una lista de Flowables directamente como contenido de celda
    ancho_recuadro = 16.5 * cm

    tabla_contenedor = Table([[sub_story_utero]], colWidths=[ancho_recuadro],rowHeights=[8.6*cm],hAlign='LEFT')
    tabla_contenedor.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))
       
    story.append(tabla_contenedor)

    # 4. Agregamos la tabla al story principal del documento
    # story.append(tabla_contenedor)

    story.append(Spacer(1, 2.5 * cm))


    mama_data = db.get_v121_mama_ecografia(visita_id)

    sub_story_mama=[]

    render_info_mama(sub_story_mama,mama_data,styles)

    #     ancho_recuadro = 7 * cm
    #     tabla_contenedor = Table([[sub_story_mama]], colWidths=[ancho_recuadro],rowHeights=[6*cm],hAlign='LEFT')
    #     tabla_contenedor.setStyle(TableStyle([
    # #        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
    #         ('VALIGN', (0,0), (-1,-1), 'TOP'),
    #         ('LEFTPADDING', (0,0), (-1,-1), 0),
    #     ]))
    story.extend(sub_story_mama)
