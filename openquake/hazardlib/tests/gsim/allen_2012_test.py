# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2022 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

from openquake.hazardlib.gsim.allen_2012 import Allen2012
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data generated from EQRM implementation.


class Allen2012TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Allen2012

    def test_all(self):
        self.check('A12/ALLEN2012_MEAN.csv',
                   'A12/ALLEN2012_STD_TOTAL.csv',
                   max_discrep_percentage=0.4,
                   std_discrep_percentage=0.1)
