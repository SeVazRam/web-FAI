# app/utils/exportaciones.py
from flask import Response
from datetime import datetime
import csv
import io
import json
from app.models import historial_cambios

def exportar_usuarios_csv(data):
    output = io.StringIO()
    fieldnames = ['username', 'nombre', 'email', 'rol', 'plan', 'fecha_registro']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    writer.writeheader()
    for row in data:
        writer.writerow(row)
    
    output.seek(0)
    fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=usuarios_{fecha}.csv'}
    )

def exportar_usuarios_json(data):
    fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
    return Response(
        json.dumps(data, indent=2, ensure_ascii=False),
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename=usuarios_{fecha}.json'}
    )

def exportar_planes_csv(data):
    output = io.StringIO()
    fieldnames = ['id', 'nombre', 'precio', 'minutos', 'datos', 'sms', 'clientes', 'ingreso_mensual']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    writer.writeheader()
    for row in data:
        writer.writerow(row)
    
    output.seek(0)
    fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=planes_{fecha}.csv'}
    )

def exportar_planes_json(data):
    fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
    return Response(
        json.dumps(data, indent=2, ensure_ascii=False),
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename=planes_{fecha}.json'}
    )

def exportar_historial_csv():
    output = io.StringIO()
    fieldnames = ['fecha', 'usuario', 'plan_anterior', 'plan_nuevo']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    writer.writeheader()
    for registro in historial_cambios:
        # Adaptar diferentes formatos de historial
        row = {
            'fecha': registro.get('fecha', ''),
            'usuario': registro.get('usuario', 'Sistema'),
            'plan_anterior': registro.get('plan_anterior', registro.get('detalle', 'N/A')),
            'plan_nuevo': registro.get('plan_nuevo', '')
        }
        writer.writerow(row)
    
    output.seek(0)
    fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=historial_cambios_{fecha}.csv'}
    )

def exportar_historial_json():
    fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
    return Response(
        json.dumps(historial_cambios, indent=2, ensure_ascii=False),
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename=historial_cambios_{fecha}.json'}
    )