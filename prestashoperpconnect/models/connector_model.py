# -*- coding: utf-8 -*-
##############################################################################
#
#    Prestashoperpconnect : OpenERP-PrestaShop connector
#    Copyright (C) 2013 Akretion (http://www.akretion.com/)
#    Copyright (C) 2015 Tech-Receptives(<http://www.tech-receptives.com>)
#    Copyright 2013 Camptocamp SA
#    @author: Alexis de Lattre <alexis.delattre@akretion.com>
#    @author Sébastien BEAU <sebastien.beau@akretion.com>
#    @author: Guewen Baconnier
#    @author Parthiv Patel <parthiv@techreceptives.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
from openerp import models, api
from openerp.addons.connector.queue.worker import watcher

_logger = logging.getLogger(__name__)


class QueueWorker(models.Model):
    _inherit = 'queue.worker'

    @api.model
    def _assign_jobs(self, max_jobs=None):
        sql = "SELECT id FROM queue_job "\
              + "WHERE worker_id IS NULL "\
              + "AND state not in ('failed', 'done') "\
              + "AND active = true "\
              + "ORDER BY eta NULLS LAST, priority, date_created "

        if max_jobs is not None:
            sql += ' LIMIT %d' % max_jobs
        sql += ' FOR UPDATE NOWAIT'
        # use a SAVEPOINT to be able to rollback this part of the
        # transaction without failing the whole transaction if the LOCK
        # cannot be acquired
        worker = watcher.worker_for_db(self.env.cr.dbname)
        self.env.cr.execute("SAVEPOINT queue_assign_jobs")
        try:
            self.env.cr.execute(sql)
        except Exception:
            # Here it's likely that the FOR UPDATE NOWAIT failed to get
            # the LOCK, so we ROLLBACK to the SAVEPOINT to restore the
            # transaction to its earlier state. The assign will be done
            # the next time.
            self.env.cr.execute("ROLLBACK TO queue_assign_jobs")
            _logger.debug("Failed attempt to assign jobs, likely due to "
                          "another transaction in progress. "
                          "Trace of the failed assignment of jobs on worker "
                          "%s attempt: ", worker.uuid, exc_info=True)
            return
        job_rows = self.env.cr.fetchall()
        if not job_rows:
            _logger.debug('No job to assign to worker %s', worker.uuid)
            return
        job_ids = [id for id, in job_rows]

        try:
            worker_id = self._worker().id
        except AssertionError as e:
            _logger.exception(e)
            return
        _logger.debug('Assign %d jobs to worker %s', len(job_ids),
                      worker.uuid)
        # ready to be enqueued in the worker
        try:
            self.env['queue.job'].browse(job_ids).write(
                {'state': 'pending',
                 'worker_id': worker_id,
                 }
            )
        except Exception:
            pass  # will be assigned to another worker

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
