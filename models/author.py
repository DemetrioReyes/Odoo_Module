from odoo import fields, models


class LibraryAuthor(models.Model):
    _name = "library.author"
    _description = "Autor"

    name = fields.Char(string="Nombre", required=True)
    nationality = fields.Char(string="Nacionalidad")
    biography = fields.Text(string="Biografía")
    book_ids = fields.One2many(
        comodel_name="library.book",
        inverse_name="author_id",
        string="Libros",
    )

