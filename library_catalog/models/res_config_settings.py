from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    proxy_base_url = fields.Char(
        string="URL base del proxy de libros",
        config_parameter="library_catalog.proxy_base_url",
        help="Endpoint del servicio interno que provee los metadatos por ISBN.",
    )
    proxy_api_key = fields.Char(
        string="Token del proxy de libros",
        config_parameter="library_catalog.proxy_api_key",
        help="Opcional. Token Bearer para autenticar contra el servicio.",
    )

