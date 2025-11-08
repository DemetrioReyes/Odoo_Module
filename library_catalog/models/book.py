import base64
import json
import logging
from datetime import date, datetime

import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class LibraryBook(models.Model):
    _name = "library.book"
    _description = "Libro"

    name = fields.Char(string="Título")
    author_id = fields.Many2one(
        comodel_name="library.author",
        string="Autor",
        ondelete="restrict",
    )
    publication_date = fields.Date(string="Fecha de publicación")
    isbn = fields.Char(string="ISBN", required=True, copy=False)
    publisher = fields.Char(string="Editorial", readonly=True)
    page_count = fields.Integer(string="Páginas", readonly=True)
    cover_image = fields.Binary(
        string="Portada",
        readonly=True,
        attachment=True,
        help="Imagen de portada proporcionada por el servicio externo.",
    )
    proxy_last_sync = fields.Datetime(
        string="Última sincronización",
        readonly=True,
        help="Momento en el que se consultó el servicio externo.",
    )
    proxy_raw_payload = fields.Text(
        string="Datos originales",
        readonly=True,
        help="JSON recibido desde el servicio externo.",
    )

    _sql_constraints = [
        ("isbn_unique", "unique(isbn)", "El ISBN debe ser único."),
    ]

    @api.model
    def _get_proxy_base_url(self):
        param = self.env["ir.config_parameter"].sudo()
        base_url = param.get_param("library_catalog.proxy_base_url")
        if not base_url:
            raise UserError(
                _("Configura la URL base del proxy en los Ajustes técnicos.")
            )
        return base_url.rstrip("/")

    @api.model
    def _get_proxy_api_key(self):
        param = self.env["ir.config_parameter"].sudo()
        return param.get_param("library_catalog.proxy_api_key")

    def action_fetch_proxy_metadata(self):
        for book in self:
            book._fetch_and_apply_proxy_data()

    def _fetch_and_apply_proxy_data(self):
        self.ensure_one()
        if not self.isbn:
            raise UserError(_("Debes definir un ISBN antes de sincronizar."))

        base_url = self._get_proxy_base_url()
        endpoint = f"{base_url.rstrip('/')}/{self.isbn}"
        headers = {
            "Accept": "application/json",
        }
        api_key = self._get_proxy_api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            response = requests.get(endpoint, timeout=10, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            _logger.exception("Error conectando al proxy de libros: %s", exc)
            raise UserError(
                _("No se pudo conectar al servicio de catálogo. Intenta más tarde.")
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            _logger.exception("Respuesta inválida desde el proxy: %s", exc)
            raise UserError(_("La respuesta del servicio no es JSON válido.")) from exc

        self._apply_proxy_payload(payload)

    def _apply_proxy_payload(self, payload):
        self.ensure_one()
        if not payload:
            raise UserError(_("El servicio no devolvió información para este ISBN."))

        updates = {}

        title = payload.get("title") or payload.get("name")
        if title:
            updates["name"] = title

        publication_date = (
            payload.get("publication_date")
            or payload.get("published")
            or payload.get("publish_date")
        )
        if publication_date:
            try:
                publication_date = self._normalize_publication_date(publication_date)
                updates["publication_date"] = publication_date
            except Exception as exc:  # pylint: disable=broad-except
                _logger.warning(
                    "No se pudo interpretar la fecha de publicación '%s': %s",
                    publication_date,
                    exc,
                )

        publisher = (
            payload.get("publisher")
            or payload.get("imprint")
            or payload.get("publishing_company")
        )
        if publisher:
            updates["publisher"] = publisher

        pages = (
            payload.get("page_count")
            or payload.get("pages")
            or payload.get("number_of_pages")
        )
        if pages:
            try:
                updates["page_count"] = int(pages)
            except (TypeError, ValueError):
                _logger.warning("El número de páginas no es válido: %s", pages)

        cover = (
            payload.get("cover_image")
            or payload.get("cover")
            or payload.get("cover_url")
        )
        if cover:
            try:
                if isinstance(cover, dict):
                    cover = cover.get("data") or cover.get("content")
                if isinstance(cover, str):
                    if cover.startswith("http"):
                        cover = self._download_cover_from_url(cover)
                    else:
                        if cover.startswith("data:"):
                            cover = cover.split(",", 1)[1]
                        base64.b64decode(cover)
                if isinstance(cover, bytes):
                    cover = base64.b64encode(cover).decode()
                if cover:
                    updates["cover_image"] = cover
            except (ValueError, AttributeError) as exc:
                _logger.warning("No se pudo decodificar la portada: %s", exc)

        author_payload = payload.get("author") or payload.get("authors")
        if author_payload:
            author = self._find_or_create_author(author_payload)
            if author:
                updates["author_id"] = author.id

        updates["proxy_raw_payload"] = json.dumps(payload, ensure_ascii=False)
        updates["proxy_last_sync"] = fields.Datetime.now()
        self.write(updates)

    def _download_cover_from_url(self, url):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as exc:
            _logger.warning("No se pudo descargar la portada desde %s: %s", url, exc)
            return None

    @api.model
    def _find_or_create_author(self, author_payload):
        name = None
        nationality = None
        biography = None

        if isinstance(author_payload, dict):
            name = author_payload.get("name") or author_payload.get("full_name")
            nationality = author_payload.get("nationality")
            biography = author_payload.get("biography") or author_payload.get("bio")
        elif isinstance(author_payload, list):
            main_author = author_payload[0] if author_payload else None
            return self._find_or_create_author(main_author)
        elif isinstance(author_payload, str):
            name = author_payload

        if not name:
            return None

        author = self.env["library.author"].search(
            [("name", "=ilike", name)], limit=1
        )
        if author:
            updates = {}
            if nationality and not author.nationality:
                updates["nationality"] = nationality
            if biography and not author.biography:
                updates["biography"] = biography
            if updates:
                author.write(updates)
            return author

        return self.env["library.author"].create(
            {
                "name": name,
                "nationality": nationality,
                "biography": biography,
            }
        )

    @staticmethod
    def _normalize_publication_date(value):
        """Convierte diferentes formatos de fecha a cadena ISO (YYYY-MM-DD)."""
        if not value:
            return None

        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()

        value_str = str(value).strip()
        if not value_str:
            return None

        # Año único como "2006"
        if value_str.isdigit():
            if len(value_str) == 4:
                return f"{value_str}-01-01"
            if len(value_str) == 8:  # formato YYYYMMDD
                return f"{value_str[0:4]}-{value_str[4:6]}-{value_str[6:8]}"

        # Intentar parseo ISO estándar
        try:
            parsed = fields.Date.from_string(value_str)
            return fields.Date.to_string(parsed)
        except Exception:  # pylint: disable=broad-except
            pass

        # Intentar parseo flexible con datetime de Python (ej. "2006-05")
        try:
            parsed_dt = datetime.fromisoformat(value_str)
            return parsed_dt.date().isoformat()
        except Exception:  # pylint: disable=broad-except
            pass

        return None

