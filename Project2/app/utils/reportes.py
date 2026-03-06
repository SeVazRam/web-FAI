# app/utils/reportes.py
from app.models import usuarios, planes

# ==================== FUNCIONES AUXILIARES ====================

def generar_reporte_usuarios(formato='csv'):
    """Genera reporte de usuarios en diferentes formatos"""
    data = []
    for username, datos in usuarios.items():
        data.append({
            'username': username,
            'nombre': datos.get('nombre', ''),
            'email': datos.get('email', ''),
            'rol': datos.get('rol', 'cliente'),
            'plan': datos.get('plan', 'N/A') if datos.get('rol') == 'cliente' else 'Admin',
            'fecha_registro': datos.get('fecha_registro', 'No disponible')
        })
    return data

def generar_reporte_planes():
    """Genera reporte de planes y asignaciones"""
    reporte = []
    for plan in planes:
        clientes_asignados = sum(1 for u in usuarios.values() 
                                if u.get('rol') == 'cliente' and u.get('plan') == plan['nombre'])
        reporte.append({
            'id': plan['id'],
            'nombre': plan['nombre'],
            'precio': plan['precio'],
            'minutos': plan['minutos'],
            'datos': plan['datos'],
            'sms': plan['sms'],
            'clientes': clientes_asignados,
            'ingreso_mensual': clientes_asignados * plan['precio']
        })
    return reporte
