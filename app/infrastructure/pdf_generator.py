import io
from pathlib import Path
from flask import send_file
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Image
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pdfencrypt import StandardEncryption # <--- Importante
from reportlab.lib.units import cm
from .pdf_components.common import draw_page_background, draw_page_background_sorrentino, draw_rubrica_medico
from .pdf_components.page1 import render as render_page1
from .pdf_components.page2 import render as render_page2
from .pdf_components.page3 import render as render_page3
from .pdf_components.page4 import render as render_page4
from .pdf_components.page5 import render as render_page5, render_sorrentino as render_sorrentino_page5, render_sorrentino_extra as render_sorrentino_extra_page5

from reportlab.platypus import Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from collections import Counter


import os

FONTS_DIR="/srv/emr-rendering-engine/app/assets/fonts"

# 1. Registras cada archivo físico con un nombre único
pdfmetrics.registerFont(TTFont('calibri', f"{FONTS_DIR}/calibri-regular.ttf"))
pdfmetrics.registerFont(TTFont('calibri-bold', f"{FONTS_DIR}/calibri-bold.ttf"))

# 2. CREAS LA CONEXIÓN (El "mapeo")
# Esto le dice a ReportLab: "Cuando uses 'calibri' y veas un <b>, usa 'calibri-bold'"
pdfmetrics.registerFontFamily('calibri', normal='calibri', bold='calibri-bold', italic='calibri', boldItalic='calibri-bold')


def generar_pagina_ecografias(imedic_data, estilo_titulo):
    """
    Replica la lógica de la página 6 de PHP: Útero, Ovarios y Mamas.
    """
    elementos_eco = []
    
    # 1. Forzamos nueva página
    elementos_eco.append(PageBreak())
    elementos_eco.append(Spacer(1, 1.5*cm))    
    # Lista de las claves que buscamos (equivalente al get_imedic de PHP)
    # Asumo que 'eco_utero', etc., vienen en el campo 'tipo_clave' o similar
    claves_eco = [
        ('eco_utero', 'Ecografía útero'),
        ('eco_ovarios', 'Ecografía ovarios'),
        ('eco_mamas', 'Ecografía mamas')
    ]
    tipos = {
        'colposcopia': 1, 'schiller': 2, 'frotis': 3, 'pap': 4,
        'eco_utero': 5, 'eco_ovarios': 6, 'eco_mamas': 7
    }
    
    ruta_default = '/var/www/docma/img/no-image.jpg'
    
    

    # Buscamos las imágenes en el dataset
    for clave, titulo in claves_eco:
        # Buscamos la fila que coincida con la clave
        tipo_id = tipos.get(clave)
        row = next((item for item in imedic_data 
                         if item['imedic_tipo_id'] == tipo_id), None)
        if not row:
            ruta_default= '/var/www/docma/img/no-image.jpg'

        if row:
            # Título de la Ecografía

            
            # Construcción de la ruta (usando tu lógica de hash)
            ruta = f"/var/www/docma/{row['ruta_local']}/{row['image_hash']}"
            
            # Imagen de 10cm x 7cm (basado en tus 100x70 de PHP)
            img = Image(ruta, width=10*cm, height=7*cm)
            img.hAlign = 'CENTER'
            
            # Usamos una tabla simple para centrar la imagen y dar espacio
            t = Table([[Paragraph(f"<b>{titulo}</b>", estilo_titulo),img]],
                      colWidths=[4*cm, 10*cm],hAlign='LEFT')
            
            t.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
#                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0.5*cm), # Espaciado entre ecos
            ]))
            elementos_eco.append(t)
            
    return elementos_eco


def get_imagenes_adicionales(full_imedic_data):
    """
    Filtra las imágenes que se repiten por tipo para enviarlas 
    a la página opcional (Página 6).
    """
    buffer_adicionales = []
    stack_tipos_vistos = set() # Usamos un set para búsquedas ultra rápidas O(1)

    for registro in full_imedic_data:
        tipo_id = registro.get('imedic_tipo_id')
        
        if tipo_id in stack_tipos_vistos:
            # Si ya vimos este tipo antes, esta imagen va para la pág 6
            buffer_adicionales.append(registro)
        else:
            # Si es la primera vez que vemos este tipo, lo marcamos como principal
            stack_tipos_vistos.add(tipo_id)
            
    return buffer_adicionales

def generar_cuadricula_fotos(fotos_extra):
    elementos_fotos = []
    
    # Agregamos un salto de página para empezar la Sección de Fotos
    elementos_fotos.append(PageBreak())
    elementos_fotos.append(Spacer(1, 2 * cm))                    
    # Agrupamos las fotos de 2 en 2 para las filas
    filas = []
    for i in range(0, len(fotos_extra), 2):
        chunk = fotos_extra[i:i + 2]
        fila_actual = []
        
        for foto in chunk:
            ruta = f"/var/www/docma/{foto['ruta_local']}/{foto['image_hash']}"
            
            # Creamos el objeto Image de Platypus
            # 8cm x 6cm como tenías en tu lógica original
            img = Image(ruta, width=8*cm, height=6*cm)
            fila_actual.append(img)
            
        # Si la última fila solo tiene una foto, agregamos una celda vacía para mantener el formato
        if len(fila_actual) == 1:
            fila_actual.append("")
            
        filas.append(fila_actual)

    # Creamos la Tabla
    # Definimos el ancho de las columnas (ej. 9cm cada una para centrar en A4)
    tabla_fotos = Table(filas, colWidths=[9*cm, 9*cm], rowHeights=7*cm)

    # Estilo de la tabla: Alineación central y espaciado
    tabla_fotos.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 20),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
    ]))

    elementos_fotos.append(tabla_fotos)
    return elementos_fotos

class FirmaFinal(Flowable):
    def __init__(self, medico_id):
        Flowable.__init__(self)
        self.medico_id = medico_id
    def draw(self):
        # Esta es la bala de plata: se dibuja en la capa del Story (encima de todo)
        draw_rubrica_medico(self.canv, self.medico_id)


def generate_medical_report(visita_id, formato, bgimage, rubrica, extra):
    from app.infrastructure.database import get_patient_data, get_visita_data, get_full_trace, get_informe_data

    
    buffer = io.BytesIO()

    visita_data = get_visita_data(visita_id)
    imedic_data = get_full_trace(visita_id)


    
    dataset={}
    ape_pat = visita_data.get('ape_pat')
    ape_mat = visita_data.get('ape_mat')
    nombres = visita_data.get('nombres')
    fecha = visita_data.get('fecha')
    dataset['paciente_nombres'] = f"{ape_pat} {ape_mat}, {nombres}".strip()
    dataset['bgimage'] = bgimage
    dataset['formato'] = formato
    dataset['extra'] = extra
    dataset['imedic_data'] = imedic_data

    dataset['medico_id'] = visita_data.get('medico_id')
    dataset['sede_id'] = visita_data.get('sede_id')

    user_pwd = visita_data.get('nro_doc')  # Ejemplo: DNI del paciente como clave
    owner_pwd = f"docker::oncogyn{user_pwd}"    # Clave interna de la clínica
    
    # 2. Creamos el objeto de encriptación
    # canPrint=True permite imprimir, canCopy=False prohíbe copiar texto
    enc = StandardEncryption(user_pwd, owner_pwd, canPrint=1, canCopy=0)
    # Ajustamos márgenes: 1 pulgada (72 puntos) es el estándar    
    #    doc = SimpleDocTemplate(buffer, pagesize=A4,  rightMargin=50, encrypt=enc)
    if rubrica=="true": 
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=40, bottomMargin=1*cm,
                                leftMargin=1.5*cm, rightMargin=1.5*cm, encrypt=enc)
    else:
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=40, bottomMargin=1*cm,
                                leftMargin=1.5*cm, rightMargin=1.5*cm)
        
    doc.title = f"Informe {ape_pat}_{fecha}"
    doc.author = "OncoGyn - KVINDER EIRL 20615095622" 
    doc.creator = "Sistema Docma - Microservicio de Renderizado Python v2.0"
    styles = getSampleStyleSheet()
    styles['Normal'].fontName = 'Calibri'
    styles['Normal'].fontSize = 12
    styles['Normal'].leading = 14
    story = []

    # --- CUERPO ---
    # --- PÁGINA 1 ---
    story.append(Spacer(1, 2.4 * cm))
    render_page1(story, visita_id, styles)    
    if rubrica == "true": story.append(FirmaFinal(visita_data.get('medico_id')))
    # --- PÁGINA 2 ---
    story.append(PageBreak())
    story.append(Spacer(1, 2.4 * cm))
    render_page2(story, visita_id, styles)
    if rubrica == "true": story.append(FirmaFinal(visita_data.get('medico_id')))
    # --- PÁGINA 3 ---
    story.append(PageBreak())
    story.append(Spacer(1, 2.4 * cm))
    render_page3(story, visita_id, styles)
    if rubrica == "true": story.append(FirmaFinal(visita_data.get('medico_id')))
    # --- PÁGINA 4 ---
    story.append(PageBreak())
    story.append(Spacer(1, 2.4 * cm))
    render_page4(story, visita_id, styles)
    if rubrica == "true": story.append(FirmaFinal(visita_data.get('medico_id')))

    if formato == "sorrentino":
        story.append(PageBreak())

        if len(extra)>0:
            story.append(Spacer(1, 3 * cm))
            render_sorrentino_extra_page5(story, visita_id, styles)
        else:
            story.append(Spacer(1, 4.5 * cm))
            render_sorrentino_page5(story, visita_id, styles)
        
        if rubrica == "true": story.append(FirmaFinal(visita_data.get('medico_id')))

        ecos_story = generar_pagina_ecografias(imedic_data, styles['Normal'])
        story.extend(ecos_story)
        if rubrica == "true": story.append(FirmaFinal(visita_data.get('medico_id')))
        
        # imagenes adicionales
        if len(imedic_data) > 7:
            story.extend(generar_cuadricula_fotos(get_imagenes_adicionales(imedic_data)))
            if rubrica == "true": story.append(FirmaFinal(visita_data.get('medico_id')))


        doc.build(story,
                  onFirstPage=lambda can, d: draw_page_background_sorrentino(can, d, dataset),
                  onLaterPages=lambda can, d: draw_page_background_sorrentino(can, d, dataset))    
    else:
        story.append(PageBreak()) # <--- formato standar
        story.append(Spacer(1, 4.5 * cm))
        render_page5(story, visita_id, styles)
        if rubrica == "true": story.append(FirmaFinal(visita_data.get('medico_id')))
        # imagenes adicionales
        if len(imedic_data) > 7:
            story.extend(generar_cuadricula_fotos(get_imagenes_adicionales(imedic_data)))
            if rubrica == "true": story.append(FirmaFinal(visita_data.get('medico_id')))

        doc.build(story,
                  onFirstPage=lambda can, d: draw_page_background(can, d, dataset),
                  onLaterPages=lambda can, d: draw_page_background(can, d, dataset))

        
    buffer.seek(0)
    
    return send_file(
        buffer, 
        mimetype='application/pdf', 
        download_name=f"Informe_{ape_pat}.pdf"
    )
