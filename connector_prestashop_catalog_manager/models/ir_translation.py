# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api


class IrTranslation(models.Model):
    _inherit = 'ir.translation'

    @api.multi
    def write_on_source_model(self):
        """ Force a write on source model to make catalog_manager
            export the translation
        """
        for translation in self:
            if translation.type == 'model':
                # get model and ir_field
                model, fieldname = self.name.split(',')
                model_obj = self.env[model]
                instance = model_obj.browse(self.res_id)
                instance_vals = instance.read([fieldname])[0]
                untranslated_content = instance_vals[fieldname]
                instance.write({fieldname: untranslated_content})
        return True

    @api.multi
    def write(self, vals):
        res = super(IrTranslation, self).write(vals)

        self.write_on_source_model()
        return res

    @api.model
    def create(self, vals):
        res = super(IrTranslation, self).create(vals)

        res.write_on_source_model()
        return res
