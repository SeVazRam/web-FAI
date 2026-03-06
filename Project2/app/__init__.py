# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, jsonify
from datetime import datetime
import csv
import io
import json

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui_cambiala_en_produccion'

# ==================== IMPORTAR DATOS DESDE MODELS ====================
from app.models import usuarios, planes, historial_cambios

# ==================== IMPORTAR FUNCIONES AUXILIARES ====================
from app.utils import generar_reporte_usuarios, generar_reporte_planes
# ==================== IMPORTAR FUNCIONES DE UTILS ====================
from app.utils import (
    generar_reporte_usuarios,
    generar_reporte_planes,
    exportar_usuarios_csv,
    exportar_usuarios_json,
    exportar_planes_csv,
    exportar_planes_json,
    exportar_historial_csv,
    exportar_historial_json
)


# ==================== RUTAS PRINCIPALES ====================
@app.route('/')
def index():
    if 'username' in session:
        if session['rol'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('cliente_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in usuarios and usuarios[username]['password'] == password:
            session['username'] = username
            session['rol'] = usuarios[username].get('rol', 'cliente')
            flash(f'¡Bienvenido {usuarios[username]["nombre"]}!', 'success')
            
            if session['rol'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('cliente_dashboard'))
        else:
            flash('Incorrect username or password', 'error')
    
    return render_template('login.html') 


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('rol', None)
    flash('Session successfully closed', 'success')
    return redirect(url_for('login'))

# ==================== DASHBOARD DEL ADMIN ====================

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'username' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado', 'error')
        return redirect(url_for('login'))
    
    # Estadísticas
    total_clientes = sum(1 for u in usuarios.values() if u.get('rol') == 'cliente')
    total_admins = sum(1 for u in usuarios.values() if u.get('rol') == 'admin')
    
    # Calcular ingresos mensuales
    ingresos_mensuales = 0
    clientes_por_plan = {}
    for u in usuarios.values():
        if u.get('rol') == 'cliente':
            plan = u.get('plan', 'Sin plan')
            clientes_por_plan[plan] = clientes_por_plan.get(plan, 0) + 1
            
            plan_info = next((p for p in planes if p['nombre'] == plan), None)
            if plan_info:
                ingresos_mensuales += plan_info['precio']
    
    # Lista de usuarios
    lista_usuarios = []
    for username, datos in usuarios.items():
        lista_usuarios.append({
            'username': username,
            'nombre': datos.get('nombre', ''),
            'email': datos.get('email', ''),
            'rol': datos.get('rol', 'cliente'),
            'plan': datos.get('plan', 'N/A') if datos.get('rol') == 'cliente' else 'Admin'
        })
    
    # Estadísticas de actividad
    cambios_hoy = sum(1 for c in historial_cambios 
                     if c.get('fecha', '').startswith(datetime.now().strftime('%Y-%m-%d')))
    
    return render_template('admin_dashboard.html', 
                         total_clientes=total_clientes,
                         total_admins=total_admins,
                         ingresos_mensuales=ingresos_mensuales,
                         clientes_por_plan=clientes_por_plan,
                         historial=historial_cambios[-10:],
                         usuarios=lista_usuarios,
                         planes=planes,
                         cambios_hoy=cambios_hoy,
                         datetime=datetime)

# ==================== GESTIÓN DE USUARIOS ====================

@app.route('/admin/usuarios')
def admin_usuarios():
    if 'username' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado', 'error')
        return redirect(url_for('login'))
    
    lista_usuarios = []
    for username, datos in usuarios.items():
        lista_usuarios.append({
            'username': username,
            'nombre': datos.get('nombre', ''),
            'email': datos.get('email', ''),
            'rol': datos.get('rol', 'cliente'),
            'plan': datos.get('plan', 'N/A') if datos.get('rol') == 'cliente' else '-'
        })
    
    return render_template('admin_usuarios.html', usuarios=lista_usuarios, planes=planes, datetime=datetime)

@app.route('/admin/usuario/nuevo', methods=['GET', 'POST'])
def admin_nuevo_usuario():
    if 'username' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form['username']
        
        if username in usuarios:
            flash('El nombre de usuario ya existe', 'error')
            return render_template('admin_editar_usuario.html', planes=planes, usuario=None)
        
        nuevo_usuario = {
            'password': request.form['password'],
            'nombre': request.form['nombre'],
            'email': request.form['email'],
            'rol': request.form['rol'],
            'fecha_registro': datetime.now().strftime('%Y-%m-%d')
        }
        
        if nuevo_usuario['rol'] == 'cliente':
            nuevo_usuario['plan'] = request.form['plan']
        
        usuarios[username] = nuevo_usuario
        
        historial_cambios.append({
            'tipo': 'Nuevo usuario',
            'usuario': username,
            'detalle': f'Usuario {nuevo_usuario["rol"]} creado',
            'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        flash(f'Usuario {username} creado exitosamente', 'success')
        return redirect(url_for('admin_usuarios'))
    
    return render_template('admin_editar_usuario.html', planes=planes, usuario=None)

@app.route('/admin/usuario/editar/<username>', methods=['GET', 'POST'])
def admin_editar_usuario(username):
    if 'username' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado', 'error')
        return redirect(url_for('login'))
    
    if username not in usuarios:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('admin_usuarios'))
    
    usuario = usuarios[username]
    
    if request.method == 'POST':
        usuario['nombre'] = request.form['nombre']
        usuario['email'] = request.form['email']
        
        if request.form['password']:
            usuario['password'] = request.form['password']
        
        if usuario['rol'] == 'cliente' and 'plan' in request.form:
            plan_anterior = usuario.get('plan', 'N/A')
            plan_nuevo = request.form['plan']
            usuario['plan'] = plan_nuevo
            
            if plan_anterior != plan_nuevo:
                historial_cambios.append({
                    'tipo': 'Cambio de plan por admin',
                    'usuario': username,
                    'detalle': f'{plan_anterior} → {plan_nuevo}',
                    'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        
        flash(f'Usuario {username} actualizado exitosamente', 'success')
        return redirect(url_for('admin_usuarios'))
    
    usuario_data = {
        'username': username,
        'nombre': usuario.get('nombre', ''),
        'email': usuario.get('email', ''),
        'rol': usuario.get('rol', 'cliente'),
        'plan': usuario.get('plan', '') if usuario.get('rol') == 'cliente' else ''
    }
    
    return render_template('admin_editar_usuario.html', planes=planes, usuario=usuario_data)

@app.route('/admin/usuario/eliminar/<username>')
def admin_eliminar_usuario(username):
    if 'username' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado', 'error')
        return redirect(url_for('login'))
    
    if username == session['username']:
        flash('No puedes eliminar tu propio usuario', 'error')
        return redirect(url_for('admin_usuarios'))
    
    if username in usuarios:
        historial_cambios.append({
            'tipo': 'Usuario eliminado',
            'usuario': username,
            'detalle': f'Usuario {usuarios[username]["rol"]} eliminado',
            'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        del usuarios[username]
        flash(f'Usuario {username} eliminado exitosamente', 'success')
    else:
        flash('Usuario no encontrado', 'error')
    
    return redirect(url_for('admin_usuarios'))

# ==================== GESTIÓN DE PLANES ====================

@app.route('/admin/planes')
def admin_planes():
    if 'username' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado', 'error')
        return redirect(url_for('login'))
    
    # Calcular estadísticas para la vista
    total_clientes = sum(1 for u in usuarios.values() if u.get('rol') == 'cliente')
    
    ingresos_mensuales = 0
    for u in usuarios.values():
        if u.get('rol') == 'cliente':
            plan_info = next((p for p in planes if p['nombre'] == u.get('plan')), None)
            if plan_info:
                ingresos_mensuales += plan_info['precio']
    
    # Añadir contador de clientes a cada plan
    for plan in planes:
        plan['clientes'] = sum(1 for u in usuarios.values() 
                              if u.get('rol') == 'cliente' and u.get('plan') == plan['nombre'])
    
    return render_template('admin_planes.html', 
                         planes=planes, 
                         total_clientes=total_clientes,
                         ingresos_mensuales=ingresos_mensuales,
                         datetime=datetime)

@app.route('/admin/plan/nuevo', methods=['GET', 'POST'])
def admin_nuevo_plan():
    if 'username' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nuevo_plan = {
            'id': len(planes) + 1,
            'nombre': request.form['nombre'],
            'precio': float(request.form['precio']),
            'minutos': request.form['minutos'],
            'datos': request.form['datos'],
            'sms': request.form['sms'],
            'descripcion': request.form['descripcion']
        }
        planes.append(nuevo_plan)
        
        historial_cambios.append({
            'tipo': 'Nuevo plan',
            'usuario': session['username'],
            'detalle': f'Plan {nuevo_plan["nombre"]} creado',
            'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        flash('Plan creado exitosamente', 'success')
        return redirect(url_for('admin_planes'))
    
    return render_template('admin_editar_plan.html', plan=None)

@app.route('/admin/plan/editar/<int:plan_id>', methods=['GET', 'POST'])
def admin_editar_plan(plan_id):
    if 'username' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado', 'error')
        return redirect(url_for('login'))
    
    plan = next((p for p in planes if p['id'] == plan_id), None)
    if not plan:
        flash('Plan no encontrado', 'error')
        return redirect(url_for('admin_planes'))
    
    if request.method == 'POST':
        plan_anterior = plan['nombre']
        plan['nombre'] = request.form['nombre']
        plan['precio'] = float(request.form['precio'])
        plan['minutos'] = request.form['minutos']
        plan['datos'] = request.form['datos']
        plan['sms'] = request.form['sms']
        plan['descripcion'] = request.form['descripcion']
        
        historial_cambios.append({
            'tipo': 'Plan editado',
            'usuario': session['username'],
            'detalle': f'{plan_anterior} → {plan["nombre"]}',
            'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        flash('Plan actualizado exitosamente', 'success')
        return redirect(url_for('admin_planes'))
    
    return render_template('admin_editar_plan.html', plan=plan)

@app.route('/admin/plan/eliminar/<int:plan_id>')
def admin_eliminar_plan(plan_id):
    if 'username' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado', 'error')
        return redirect(url_for('login'))
    
    global planes
    plan_eliminado = next((p for p in planes if p['id'] == plan_id), None)
    planes = [p for p in planes if p['id'] != plan_id]
    
    if plan_eliminado:
        historial_cambios.append({
            'tipo': 'Plan eliminado',
            'usuario': session['username'],
            'detalle': f'Plan {plan_eliminado["nombre"]} eliminado',
            'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        flash('Plan eliminado exitosamente', 'success')
    
    return redirect(url_for('admin_planes'))

# ==================== EXPORTACIÓN DE DATOS ====================

@app.route('/admin/exportar')
def admin_exportar():
    if 'username' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado', 'error')
        return redirect(url_for('login'))
    
    total_clientes = sum(1 for u in usuarios.values() if u.get('rol') == 'cliente')
    total_admins = sum(1 for u in usuarios.values() if u.get('rol') == 'admin')
    
    ingresos_mensuales = 0
    for u in usuarios.values():
        if u.get('rol') == 'cliente':
            plan_info = next((p for p in planes if p['nombre'] == u.get('plan')), None)
            if plan_info:
                ingresos_mensuales += plan_info['precio']
    
    cambios_hoy = sum(1 for c in historial_cambios 
                     if c.get('fecha', '').startswith(datetime.now().strftime('%Y-%m-%d')))
    
    return render_template('admin_exportar.html',
                         total_clientes=total_clientes,
                         total_admins=total_admins,
                         ingresos_mensuales=ingresos_mensuales,
                         planes=planes,
                         historial=historial_cambios[-10:],
                         cambios_hoy=cambios_hoy,
                         datetime=datetime)

# Exportar Usuarios
@app.route('/admin/exportar/usuarios/<formato>')
def admin_exportar_usuarios(formato):
    if 'username' not in session or session['rol'] != 'admin':
        return "Acceso no autorizado", 403
    
    data = generar_reporte_usuarios(formato)
    
    if formato == 'csv':
        return exportar_usuarios_csv(data)
    elif formato == 'json':
        return exportar_usuarios_json(data)
    else:
        flash('Formato no soportado', 'error')
        return redirect(url_for('admin_exportar'))
    


# Exportar Planes
@app.route('/admin/exportar/planes/<formato>')
def admin_exportar_planes(formato):
    if 'username' not in session or session['rol'] != 'admin':
        return "Acceso no autorizado", 403
    
    data = generar_reporte_planes()
    
    if formato == 'csv':
        return exportar_planes_csv(data)
    elif formato == 'json':
        return exportar_planes_json(data)
    else:
        flash('Formato no soportado', 'error')
        return redirect(url_for('admin_exportar'))



# Exportar Historial
@app.route('/admin/exportar/historial/<formato>')
def admin_exportar_historial(formato):
    if 'username' not in session or session['rol'] != 'admin':
        return "Acceso no autorizado", 403
    
    if formato == 'csv':
        return exportar_historial_csv()
    elif formato == 'json':
        return exportar_historial_json()
    else:
        flash('Formato no soportado', 'error')
        return redirect(url_for('admin_exportar'))

# ==================== DASHBOARD DEL CLIENTE ====================

@app.route('/cliente/dashboard')
def cliente_dashboard():
    if 'username' not in session or session['rol'] != 'cliente':
        flash('Acceso no autorizado', 'error')
        return redirect(url_for('login'))
    
    username = session['username']
    plan_actual = usuarios[username].get('plan', 'Sin plan')
    
    return render_template('cliente_dashboard.html', 
                         username=username,
                         nombre=usuarios[username].get('nombre', username),
                         plan_actual=plan_actual,
                         planes=planes,
                         datetime=datetime,
                         usuarios=usuarios) 

@app.route('/cliente/cambiar_plan/<int:plan_id>')
def cliente_cambiar_plan(plan_id):
    if 'username' not in session or session['rol'] != 'cliente':
        flash('Acceso no autorizado', 'error')
        return redirect(url_for('login'))
    
    plan = next((p for p in planes if p['id'] == plan_id), None)
    if plan:
        username = session['username']
        plan_anterior = usuarios[username].get('plan', 'Sin plan')
        
        # Actualizar plan del usuario
        usuarios[username]['plan'] = plan['nombre']
        
        # Registrar en historial
        historial_cambios.append({
            'usuario': username,
            'plan_anterior': plan_anterior,
            'plan_nuevo': plan['nombre'],
            'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        flash(f'¡Plan cambiado a {plan["nombre"]} exitosamente!', 'success')
    else:
        flash('Plan no encontrado', 'error')
    
    return redirect(url_for('cliente_dashboard'))

# ==================== CAMBIO DE CONTRASEÑA ====================

@app.route('/cambiar_password', methods=['GET', 'POST'])
def cambiar_password():
    """Permite al usuario cambiar su contraseña"""
    if 'username' not in session:
        flash('Debes iniciar sesión primero', 'error')
        return redirect(url_for('login'))
    
    username = session['username']
    
    if request.method == 'POST':
        password_actual = request.form['password_actual']
        password_nueva = request.form['password_nueva']
        password_confirmar = request.form['password_confirmar']
        
        # Verificar contraseña actual
        if usuarios[username]['password'] != password_actual:
            flash('La contraseña actual es incorrecta', 'error')
            return redirect(url_for('cambiar_password'))
        
        # Verificar que la nueva contraseña no sea igual a la actual
        if password_actual == password_nueva:
            flash('La nueva contraseña no puede ser igual a la actual', 'error')
            return redirect(url_for('cambiar_password'))
        
        # Verificar que las contraseñas nuevas coincidan
        if password_nueva != password_confirmar:
            flash('Las nuevas contraseñas no coinciden', 'error')
            return redirect(url_for('cambiar_password'))
        
        # Verificar longitud mínima
        if len(password_nueva) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return redirect(url_for('cambiar_password'))
        
        # Actualizar contraseña
        usuarios[username]['password'] = password_nueva
        
        # Registrar en historial
        historial_cambios.append({
            'tipo': 'Cambio de contraseña',
            'usuario': username,
            'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        flash('¡Contraseña cambiada exitosamente!', 'success')
        return redirect(url_for('index'))
    
    return render_template('cambiar_password.html', usuario=usuarios[username])

# ==================== API CHATBOT ====================

@app.route('/api/chat', methods=['POST'])
def chat_bot():
    """Endpoint para el chatbot"""
    data = request.get_json()
    mensaje = data.get('mensaje', '').lower().strip()
    
    # Base de conocimiento del chatbot
    respuestas = {
        'hola': ['¡Hola! ¿En qué puedo ayudarte hoy?', '¡Buenos días! ¿Cómo estás?', '¡Hola! Bienvenido al asistente virtual'],
        'planes': ['Tenemos 4 planes disponibles: Básico ($29.99), Estándar ($49.99), Premium ($79.99) y Familiar ($129.99). ¿Te gustaría conocer más detalles de alguno?'],
        'precios': ['Los precios de nuestros planes son:\n- Básico: $29.99/mes\n- Estándar: $49.99/mes\n- Premium: $79.99/mes\n- Familiar: $129.99/mes'],
        'contacto': ['Puedes contactarnos al soporte@telecom.com o al teléfono 123-456-7890. Nuestro horario es de 9:00 a 18:00'],
        'cambiar': ['Para cambiar tu plan, ve a la sección "Planes disponibles" en tu dashboard y selecciona el plan que prefieras. Los cambios son inmediatos.'],
        'ayuda': ['Claro, ¿qué necesitas saber? Puedo ayudarte con información sobre planes, precios, cambios de plan, contacto, etc.'],
        'gracias': ['¡De nada! ¿Necesitas algo más?', 'Un placer ayudarte', 'Para eso estamos'],
        'adios': ['¡Hasta luego! Que tengas un excelente día', '¡Vuelve pronto!', 'Adiós, cualquier cosa aquí estoy']
    }
    
    # Buscar respuesta
    respuesta = "Lo siento, no entendí tu pregunta. ¿Podrías reformularla? Puedo ayudarte con información sobre planes, precios, cambios de plan o contacto."
    
    for palabra_clave, respuestas_list in respuestas.items():
        if palabra_clave in mensaje:
            import random
            respuesta = random.choice(respuestas_list)
            break
    
    # Personalizar según el rol del usuario
    if 'username' in session:
        if session['rol'] == 'admin':
            respuesta += " (como administrador tienes acceso a funciones adicionales)"
        else:
            plan_actual = usuarios[session['username']].get('plan', 'sin plan')
            if 'plan' in mensaje or 'precio' in mensaje:
                respuesta += f" Actualmente tienes el plan {plan_actual}."
    
    return jsonify({'respuesta': respuesta})
