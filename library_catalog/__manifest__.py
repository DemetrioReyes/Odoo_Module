{
    "name": "Biblioteca - Catálogo",
    "summary": "Gestión de autores y libros con integración automática por ISBN.",
    "version": "16.0.1.0.0",
    "license": "LGPL-3",
    "category": "Library",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_config_parameter.xml",
        "views/author_views.xml",
        "views/book_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "application": True,
}

