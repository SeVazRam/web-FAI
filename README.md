app/
├── 📂 models/               # Modelos de base de datos (SQLAlchemy)
│   ├── __init__.py
│   ├── usuarios.py          # Gestión de usuarios
│   ├── planes.py            # Planes o suscripciones
│   └── historial.py         # Historial de acciones o interacciones
│
├── 📂 utils/                 # Funciones auxiliares
│   ├── __init__.py
│   ├── reportes.py           # Generación de reportes
│   └── exportaciones.py      # Exportación de datos (CSV, PDF, etc.)
│
├── 📂 templates/             # Plantillas HTML (Jinja2)
│   └── ...
│
└── 📄 __init__.py            # Inicialización de la app, configuración y rutas
