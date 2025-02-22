# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2022 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import signal
import psutil
from openquake.commonlib import logs


def main(job_id: int):
    """
    Abort the given job
    """
    for job_id in job_id:
        job = logs.dbcmd('get_job', job_id)  # job_id can be negative
        if job is None:
            print('There is no job %d' % job_id)
            return
        elif job.status in ('complete', 'failed', 'aborted'):
            print('Job %d is %s' % (job.id, job.status))
            return
        name = 'oq-job-%d' % job.id
        for p in psutil.process_iter():
            if p.name() == name:
                try:
                    os.kill(p.pid, signal.SIGINT)
                    logs.dbcmd('set_status', job.id, 'aborted')
                    print('Job %d aborted' % job.id)
                except Exception as exc:
                    print(exc)
                break
        else:  # no break
            # set job as failed if it is 'executing' or 'running' in the db
            # but the corresponding process is not running anymore
            logs.dbcmd('set_status', job.id, 'failed')
            print('Unable to find a process for job %d,'
                  ' setting it as failed' % job.id)


main.job_id = dict(help='job ID', nargs='+')
