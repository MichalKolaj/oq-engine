# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020, GEM Foundation
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
import numpy as np
import unittest
from openquake.hazardlib import const
from openquake.hazardlib.contexts import get_mean_stds
from openquake.hazardlib.imt import PGA, SA, MMI
from openquake.hazardlib.gsim.base import registry, CoeffsTable
from openquake.hazardlib.contexts import RuptureContext
from openquake.hazardlib.tests.gsim.mgmpe.dummy import Dummy
from openquake.hazardlib.gsim.mgmpe.modifiable_gmpe import (
    ModifiableGMPE, _dict_to_coeffs_table)
from openquake.hazardlib.gsim.boore_atkinson_2008 import BooreAtkinson2008
from openquake.hazardlib.gsim.boore_2014 import BooreEtAl2014


class ModifiableGMPEAddWithBetweenTest(unittest.TestCase):

    def setUp(self):
        self.ctx = ctx = RuptureContext()
        ctx.mag = 6.
        ctx.rake = 0.
        ctx.hypo_depth = 10.
        ctx.occurrence_rate = .001
        sites = Dummy.get_site_collection(4, vs30=760.)
        for name in sites.array.dtype.names:
            setattr(ctx, name, sites[name])
        ctx.rrup = np.array([1., 10., 30., 70.])
        ctx.rjb = np.array([1., 10., 30., 70.])
        self.imt = PGA()

    def test_add_between_within_sigma(self):
        """ Checks that the modified GMM has between and within std """
        stds_types = [const.StdDev.TOTAL, const.StdDev.INTRA_EVENT,
                      const.StdDev.INTER_EVENT]
        gmm = ModifiableGMPE(gmpe={'Campbell2003': {}},
                             add_between_within_stds={'with_betw_ratio': 0.6})
        out = gmm.get_mean_and_stddevs(self.ctx, self.ctx, self.ctx,
                                       self.imt, stds_types)
        expected_with = np.ones(4) * 0.24381161
        expected_betw = np.ones(4) * 0.40635268
        aae = np.testing.assert_array_almost_equal
        aae(expected_betw, out[1][2])
        aae(expected_with, out[1][1])


class ModifiableGMPETest(unittest.TestCase):

    def setUp(self):
        self.ctx = ctx = RuptureContext()
        ctx.mag = 6.
        ctx.rake = 0.
        ctx.hypo_depth = 10.
        ctx.occurrence_rate = .001
        sites = Dummy.get_site_collection(4, vs30=760.)
        for name in sites.array.dtype.names:
            setattr(ctx, name, sites[name])
        ctx.rrup = np.array([1., 10., 30., 70.])
        ctx.rjb = np.array([1., 10., 30., 70.])
        self.imt = PGA()

    def test_set_between_epsilon_raises_error(self):
        """ Check that error is raised for GMPEs with only total std """

        stds_types = [const.StdDev.TOTAL, const.StdDev.INTER_EVENT,
                      const.StdDev.INTRA_EVENT]
        gmm = ModifiableGMPE(gmpe={'Campbell2003': {}},
                             set_between_epsilon={'epsilon_tau': 0.5})
        with self.assertRaises(ValueError):
            gmm.get_mean_and_stddevs(self.ctx, self.ctx, self.ctx,
                                     self.imt, stds_types)

    def test_get_mean_std(self):
        """ Check calculation of mean and stds """

        stds_types = [const.StdDev.TOTAL, const.StdDev.INTER_EVENT,
                      const.StdDev.INTRA_EVENT]

        gmpe_name = 'AkkarEtAlRjb2014'
        gmm = ModifiableGMPE(gmpe={gmpe_name: {}},
                             set_between_epsilon={'epsilon_tau': 0.5})
        mean, stds = gmm.get_mean_and_stddevs(self.ctx, self.ctx, self.ctx,
                                              self.imt, stds_types)

        gmpe = registry[gmpe_name]()
        emean, estds = gmpe.get_mean_and_stddevs(
            self.ctx, self.ctx, self.ctx, self.imt, stds_types)
        idx = stds_types.index(const.StdDev.INTER_EVENT)
        exp_mean = emean + estds[idx] * 0.5

        # Check the computed mean + between event variability
        np.testing.assert_almost_equal(mean, exp_mean)

        # Check that the total std now corresponds to the within event
        # standard deviation
        np.testing.assert_almost_equal(stds[0], estds[2])

    def test_coefficients_as_dictionary(self):
        """Check the parsing of the coefficients to a dictionary"""
        input_coeffs = {"PGA": 1.0, "SA(0.2)": 2.0, "SA(3.0)": 3.0}
        output_coeffs = _dict_to_coeffs_table(input_coeffs, "XYZ")
        self.assertListEqual(list(output_coeffs), ["XYZ"])
        self.assertIsInstance(output_coeffs["XYZ"], CoeffsTable)
        self.assertAlmostEqual(output_coeffs["XYZ"][PGA()]["XYZ"], 1.0)
        self.assertAlmostEqual(output_coeffs["XYZ"][SA(0.2)]["XYZ"], 2.0)
        self.assertAlmostEqual(output_coeffs["XYZ"][SA(3.0)]["XYZ"], 3.0)

    def test_scale_median_scalar(self):
        """Check the scaling of the median ground motion - scalar"""
        gmpe_name = 'AkkarEtAlRjb2014'
        stddevs = [const.StdDev.TOTAL]
        gmm_unscaled = ModifiableGMPE(gmpe={gmpe_name: {}})
        gmm = ModifiableGMPE(gmpe={gmpe_name: {}},
                             set_scale_median_scalar={'scaling_factor': 1.2})
        mean_unscaled = gmm_unscaled.get_mean_and_stddevs(
            self.ctx, self.ctx, self.ctx, self.imt, stddevs)[0]
        mean = gmm.get_mean_and_stddevs(
            self.ctx, self.ctx, self.ctx, self.imt, stddevs)[0]
        np.testing.assert_almost_equal(np.exp(mean) / np.exp(mean_unscaled),
                                       1.2 * np.ones(mean.shape))

    def test_scale_median_vector(self):
        """Check the scaling of the median ground motion - IMT-dependent"""
        gmpe_name = 'AkkarEtAlRjb2014'
        stddevs = [const.StdDev.TOTAL]
        gmm_unscaled = ModifiableGMPE(gmpe={gmpe_name: {}})
        gmm = ModifiableGMPE(
            gmpe={gmpe_name: {}},
            set_scale_median_vector={'scaling_factor': {"PGA": 0.9,
                                                        "SA(0.2)": 1.1}})
        for imt, sfact in zip([PGA(), SA(0.2)], [0.9, 1.1]):
            mean_unscaled = gmm_unscaled.get_mean_and_stddevs(
                self.ctx, self.ctx, self.ctx, imt, stddevs)[0]
            mean = gmm.get_mean_and_stddevs(self.ctx, self.ctx, self.ctx,
                                            imt, stddevs)[0]
            np.testing.assert_almost_equal(
                np.exp(mean) / np.exp(mean_unscaled),
                sfact * np.ones(mean.shape))

    def test_scale_total_sigma_scalar(self):
        """Check the scaling of the total stddev - scalar"""
        gmpe_name = 'AkkarEtAlRjb2014'
        stddevs = [const.StdDev.TOTAL]
        gmm_unscaled = ModifiableGMPE(gmpe={gmpe_name: {}})
        gmm = ModifiableGMPE(
            gmpe={gmpe_name: {}},
            set_scale_total_sigma_scalar={"scaling_factor": 1.2})
        [stddev_unscaled] = gmm_unscaled.get_mean_and_stddevs(
            self.ctx, self.ctx, self.ctx, self.imt, stddevs)[1]
        [stddev] = gmm.get_mean_and_stddevs(self.ctx, self.ctx, self.ctx,
                                            self.imt, stddevs)[1]
        np.testing.assert_array_almost_equal(stddev / stddev_unscaled,
                                             1.2 * np.ones(stddev.shape))

    def test_scale_total_sigma_vector(self):
        """Check the scaling of the total stddev - vector"""
        gmpe_name = 'AkkarEtAlRjb2014'
        stddevs = [const.StdDev.TOTAL]
        gmm_unscaled = ModifiableGMPE(gmpe={gmpe_name: {}})
        gmm = ModifiableGMPE(
            gmpe={gmpe_name: {}},
            set_scale_total_sigma_vector={"scaling_factor": {"PGA": 0.9,
                                                             "SA(0.2)": 1.1}})

        for imt, sfact in zip([PGA(), SA(0.2)], [0.9, 1.1]):
            [stddev_unscaled] = gmm_unscaled.get_mean_and_stddevs(
                self.ctx, self.ctx, self.ctx, imt, stddevs)[1]
            [stddev] = gmm.get_mean_and_stddevs(
                self.ctx, self.ctx, self.ctx, imt, stddevs)[1]
            np.testing.assert_almost_equal(
                stddev / stddev_unscaled,
                sfact * np.ones(stddev.shape))

    def test_fixed_total_sigma(self):
        """Check the assignment of total sigma to a fixed value"""
        gmpe_name = 'AkkarEtAlRjb2014'
        stddevs = [const.StdDev.TOTAL]
        gmm = ModifiableGMPE(
            gmpe={gmpe_name: {}},
            set_fixed_total_sigma={"total_sigma": {"PGA": 0.6,
                                                   "SA(0.2)": 0.75}})

        for imt, sfact in zip([PGA(), SA(0.2)], [0.6, 0.75]):
            [stddev] = gmm.get_mean_and_stddevs(
                self.ctx, self.ctx, self.ctx, imt, stddevs)[1]
            np.testing.assert_almost_equal(stddev,
                                           sfact * np.ones(stddev.shape))

    def test_add_delta(self):
        """Check adding/removing a delta std to the total std"""
        gmpe_name = 'AkkarEtAlRjb2014'
        stddevs = [const.StdDev.TOTAL]

        gmm = ModifiableGMPE(
            gmpe={gmpe_name: {}},
            add_delta_std_to_total_std={"delta": -0.20})
        imt = PGA()
        [stddev] = gmm.get_mean_and_stddevs(
            self.ctx, self.ctx, self.ctx, imt, stddevs)[1]

        # Original total std for PGA is 0.7121
        np.testing.assert_almost_equal(stddev[0], 0.68344277, decimal=6)

    def test_set_total_std_as_tau_plus_phi(self):
        """Check set total std as between plus phi SS"""
        gmpe_name = 'AkkarEtAlRjb2014'
        stddevs = [const.StdDev.TOTAL]

        gmm = ModifiableGMPE(
            gmpe={gmpe_name: {}},
            set_total_std_as_tau_plus_delta={"delta": 0.45})
        imt = PGA()
        [stddev] = gmm.get_mean_and_stddevs(
            self.ctx, self.ctx, self.ctx, imt, stddevs)[1]

        # Original tau for PGA is 0.6201
        np.testing.assert_almost_equal(stddev[0], 0.5701491121, decimal=6)

    def test_horiz_comp_to_geom_mean01(self):
        """ Checks the horizontal component conversion """

        # Initialize the modified GMM
        gmpe_name = 'BooreEtAl2014'
        gmm_unscaled = ModifiableGMPE(gmpe={gmpe_name: {}})
        gmm = ModifiableGMPE(gmpe={gmpe_name: {}}, horiz_comp_to_geom_mean={})

        # Define expected conversion factors for median gm
        expected = [1.009, 1.009, 1.0100744, 1.01714271, 1.0264865,
                    1.03168663, 1.04649942, 1.077]

        # Define IMTs
        imts = [PGA(), SA(0.01), SA(0.1), SA(0.2), SA(0.5), SA(1), SA(5),
                SA(10)]

        # Computing results
        results = []
        for imt in imts:

            # Results from original GMM
            out = get_mean_stds([BooreEtAl2014()], self.ctx, [imt])
            mean_unscaled = out[0].flatten()
            std_unscaled = out[1].flatten()

            # Results from modified GMM
            out = get_mean_stds([gmm], self.ctx, [imt])
            mean_scaled = out[0].flatten()
            std_scaled = out[1].flatten()

            # Storing results
            results.append(np.exp(mean_unscaled[0]) / np.exp(mean_scaled[0]))

        # Check
        np.testing.assert_almost_equal(results, expected, decimal=5)

    def test_horiz_comp_to_geom_mean02(self):
        """ Checks the horizontal component conversion """

        # Initialize the modified GMM
        gmpe_name = 'BooreAtkinson2008'
        gmm = ModifiableGMPE(gmpe={gmpe_name: {}}, horiz_comp_to_geom_mean={})

        # Define IMTs
        imts = [PGA(), SA(0.01), SA(0.1), SA(0.2), SA(0.5), SA(1), SA(5),
                SA(10)]

        # Define expected conversion factors for median gm
        expected = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

        # Define expected conversion factors for stds
        convs = [0.02, 0.03, 0.03, 0.0317185550924273, 0.0371922924372184,
                 0.04, 0.04, 0.04]

        # Computing results
        results = []
        for imt in imts:

            # Results from original GMM
            out = get_mean_stds([BooreAtkinson2008()], self.ctx, [imt])
            mean_unscaled = out[0].flatten()
            std_unscaled = out[1].flatten()

            # Results from modified GMM
            out = get_mean_stds([gmm], self.ctx, [imt])
            mean_scaled = out[0].flatten()
            std_scaled = out[1].flatten()

            # Storing results
            tmp_mean_ratio = np.exp(mean_unscaled[0]) / np.exp(mean_scaled[0])
            tmp_conv_std = (std_unscaled[0]**2 - std_scaled[0]**2)**0.5
            results.append([tmp_mean_ratio, tmp_conv_std])

        # Check
        results = np.array(results)
        np.testing.assert_almost_equal(results[:, 0], expected, decimal=5)
        np.testing.assert_almost_equal(results[:, 1], convs, decimal=5)


class ModifiableGMPETestSwissAmpl(unittest.TestCase):
    """
    Tests the implementation of a correction factor for intensity
    """

    def setUp(self):
        self.ctx = ctx = RuptureContext()
        ctx.mag = 6.0
        ctx.hypo_depth = 10.
        ctx.occurrence_rate = .001
        sites = Dummy.get_site_collection(
            4, amplfactor=[-1.0, 1.5, 0.00, -1.99])
        for name in sites.array.dtype.names:
            setattr(ctx, name, sites[name])
        ctx.rhypo = ctx.rrup = ctx.repi = np.array([1., 10., 30., 70.])
        self.imt = MMI()

    def test_get_mean_std(self):
        """ Check calculation of amplified mean"""

        for gmpe_name in ['ECOS2009', 'BindiEtAl2011RepiFixedH',
                          'BaumontEtAl2018High2210IAVGDC30n7',
                          'FaccioliCauzzi2006']:

            stds_types = [const.StdDev.TOTAL]
            gmm = ModifiableGMPE(gmpe={gmpe_name: {}},
                                 apply_swiss_amplification={})
            mean, stds = gmm.get_mean_and_stddevs(
                self.ctx, self.ctx, self.ctx, self.imt, stds_types)

            gmpe = registry[gmpe_name]()
            emean, estds = gmpe.get_mean_and_stddevs(
                self.ctx, self.ctx, self.ctx, self.imt, stds_types)

            exp_mean = emean + np.array([-1.00, 1.50, 0, -1.99])

            # Check the computed mean + amplification
            np.testing.assert_almost_equal(mean, exp_mean)
