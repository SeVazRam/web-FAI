import sys
import os

# Agrega el directorio actual al path de Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Servidor iniciado en http://127.0.0.1:5000")
    print("📁 Estructura verificada")
    print("=" * 50)
    app.run(debug=True)