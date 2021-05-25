# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class IrTranslation(models.Model):
    _inherit = "ir.translation"

    def write_on_source_model(self):
        """Force a write on source model to make catalog_manager
        export the translation
        """
        for translation in self:
            if translation.type == "model":
                # get model and ir_field
                model, fieldname = translation.name.split(",")
                model_obj = translation.env[model]
                instance = model_obj.browse(translation.res_id)
                instance_vals = instance.read([fieldname])[0]
                untranslated_content = instance_vals[fieldname]
                instance.with_context(catalog_manager_force_translation=True).write(
                    {fieldname: untranslated_content}
                )
        return True

    def write(self, vals):
        res = False
        for translation in self:
            if translation.env.context.get("catalog_manager_force_translation", False):
                continue
            res = super().write(vals)

            self.write_on_source_model()
        return res

    @api.model
    def create(self, vals):
        res = super().create(vals)

        if not self.env.context.get("catalog_manager_ignore_translation", False):
            # It is called from a binding creation so,
            # Once the binding will be created, it will export everything.
            # this way we avoid job duplicities exporting the same instance
            res.write_on_source_model()
        return res
