"""
Pre-migration: scenario_type alanı fields.Selection → fields.Char olarak değiştirildi.
Odoo upgrade sırasında eski ir_model_fields_selection kayıtlarını silerken
field.ondelete attribute'ını arıyor — Char alanında bu yok ve AttributeError fırlatıyor.
Bu script, upgrade başlamadan önce o eski selection kayıtlarını temizler.
"""


def migrate(cr, version):
    cr.execute("""
        DELETE FROM ir_model_fields_selection
        WHERE field_id IN (
            SELECT id FROM ir_model_fields
            WHERE name = 'scenario_type'
              AND model IN (
                  'ak.tender.scenario',
                  'ak.tender.scenario.wizard'
              )
        )
    """)
