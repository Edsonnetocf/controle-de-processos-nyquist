"""Referências analíticas e casos adversos; sem python-control ou SciPy."""
import itertools
import unittest
import numpy as np
from numpy.testing import assert_allclose
from src.models import TransferFunction, benchmark_models
from src.routh import routh
from src.nyquist import nyquist, winding_number, CriticalPointError, outer_loop_bound
from src.frequency import bode, margins
from src.root_locus import root_locus, minimum_cost_assignment


class ModelTests(unittest.TestCase):
    def test_characteristic_polynomials(self):
        plants = benchmark_models()
        assert_allclose(plants['A'].characteristic(2), [1, 6, 11, 8])
        assert_allclose(plants['B'].characteristic(8), [1, 4, 1, 2])
        assert_allclose(plants['C'].characteristic(2), [1, 6, 9, 8])

    def test_exact_delay(self):
        plant = TransferFunction([1], [1, 1], delay=0.7)
        w = np.array([0.01, 1, 15])
        assert_allclose(plant.frequency_response(w), np.exp(-0.7j*w)/(1+1j*w))

    def test_pade_first_order(self):
        approximate = TransferFunction([1], [1], delay=2).pade(1)
        assert_allclose(approximate.numerator, [-1, 1])
        assert_allclose(approximate.denominator, [1, 1])

    def test_pade_converges_at_fixed_frequency(self):
        plant = TransferFunction([1], [1, 1], delay=0.5)
        exact = plant.frequency_response(1)
        errors = [abs(plant.pade(q).frequency_response(1)-exact) for q in (1, 2, 3)]
        self.assertTrue(errors[0] > errors[1] > errors[2])
        self.assertLess(errors[-1], 1e-7)

    def test_invalid_input(self):
        for num, den, delay in [([1], [0], 0), ([1], [1, 1], -1), ([np.nan], [1], 0)]:
            with self.subTest(num=num, den=den, delay=delay), self.assertRaises(ValueError):
                TransferFunction(num, den, delay)

    def test_delay_requires_explicit_approximation(self):
        plant = benchmark_models()['D']
        with self.assertRaises(ValueError):
            plant.characteristic(1)
        with self.assertRaises(ValueError):
            root_locus(plant, [0, 1])


class RouthTests(unittest.TestCase):
    def test_a_analytical_limit(self):
        plant = benchmark_models()['A']
        for gain, status, count in [(1, 'stable', 0), (59, 'stable', 0),
                                     (60, 'boundary', 0), (61, 'unstable', 2)]:
            with self.subTest(gain=gain):
                result = routh(plant.characteristic(gain))
                self.assertEqual((result.status, result.right_half_plane_poles), (status, count))

    def test_b_analytical_interval(self):
        plant = benchmark_models()['B']
        for gain, status, count in [(5, 'unstable', 1), (6, 'boundary', 0),
                                     (8, 'stable', 0), (10, 'boundary', 0), (11, 'unstable', 2)]:
            with self.subTest(gain=gain):
                result = routh(plant.characteristic(gain))
                self.assertEqual((result.status, result.right_half_plane_poles), (status, count))

    def test_c_analytical_limit(self):
        plant = benchmark_models()['C']
        self.assertEqual(routh(plant.characteristic(8)).status, 'stable')
        self.assertEqual(routh(plant.characteristic(60/7)).status, 'boundary')
        self.assertEqual(routh(plant.characteristic(9)).right_half_plane_poles, 2)

    def test_zero_pivot_and_epsilon_sensitivity(self):
        for epsilon in (1e-6, 1e-8, 1e-10):
            with self.subTest(epsilon=epsilon):
                result = routh([1, 2, 2, 4, 1], epsilon)
                self.assertEqual(result.right_half_plane_poles, 2)
                self.assertIn(2, result.epsilon_rows)

    def test_complete_zero_row_repeated_imaginary_roots(self):
        result = routh([1, 0, 2, 0, 1])
        self.assertEqual(result.status, 'boundary')
        self.assertTrue(result.auxiliary_rows)

    def test_zero_row_does_not_hide_unstable_root(self):
        self.assertEqual(routh([1, 0, 0, 0, -1]).right_half_plane_poles, 1)

    def test_positive_scaling_invariance(self):
        a = np.array([1, 4, 1, 2], dtype=float)
        for multiplier in (1e-20, 1, 1e20):
            self.assertEqual(routh(a*multiplier).status, 'stable')

    def test_constructed_polynomials(self):
        rng = np.random.default_rng(20261123)
        for degree in range(1, 9):
            for unstable in range(degree+1):
                roots = -rng.uniform(0.3, 3, degree)
                roots[:unstable] *= -1
                with self.subTest(degree=degree, unstable=unstable):
                    self.assertEqual(routh(np.poly(roots)).right_half_plane_poles, unstable)


class NyquistTests(unittest.TestCase):
    def test_clockwise_convention(self):
        theta = np.linspace(0, 2*np.pi, 1500, endpoint=False)
        self.assertEqual(winding_number(-1+0.4*np.exp(1j*theta))[0], -1)
        self.assertEqual(winding_number(-1+0.4*np.exp(-1j*theta))[0], 1)

    def test_point_on_contour_is_rejected(self):
        with self.assertRaises(CriticalPointError):
            winding_number([-2, 0, 1j])

    def test_a_matches_analytical_limit(self):
        plant = benchmark_models()['A']
        for gain, count in [(1, 0), (59, 0), (61, 2), (100, 2)]:
            with self.subTest(gain=gain):
                result = nyquist(plant, gain)
                self.assertTrue(result.converged)
                self.assertEqual(result.closed_loop_unstable, count)

    def test_unstable_open_loop_and_negative_encirclement(self):
        plant = benchmark_models()['B']
        for gain, count in [(5, 1), (8, 0), (11, 2)]:
            with self.subTest(gain=gain):
                result = nyquist(plant, gain)
                self.assertEqual(result.open_loop_unstable, 1)
                self.assertEqual(result.closed_loop_unstable, count)
                self.assertEqual(result.clockwise_encirclements+1, count)

    def test_nonminimum_phase(self):
        plant = benchmark_models()['C']
        self.assertEqual(nyquist(plant, 8).closed_loop_unstable, 0)
        self.assertEqual(nyquist(plant, 9).closed_loop_unstable, 2)

    def test_integrator_indentation(self):
        result = nyquist(TransferFunction([1], [1, 1, 0]), 1)
        self.assertEqual(result.status, 'stable')
        self.assertEqual(result.closed_loop_unstable, 0)
        self.assertTrue(any((result.contour.real > 0) & (abs(result.contour) < 0.001)))

    def test_critical_gain_is_not_classified_as_stable(self):
        result = nyquist(benchmark_models()['A'], 60)
        self.assertIn(result.status, ['boundary', 'inconclusive'])
        self.assertIsNone(result.closed_loop_unstable)

    def test_analytical_delay_threshold(self):
        # 2 e^(-tau s)/(s+1): wc=sqrt(3), taucrit=(pi-atan(wc))/wc.
        wc = np.sqrt(3)
        limit = (np.pi-np.arctan(wc))/wc
        stable = nyquist(TransferFunction([1], [1, 1], 0.8*limit), 2)
        unstable = nyquist(TransferFunction([1], [1, 1], 1.2*limit), 2)
        self.assertEqual(stable.closed_loop_unstable, 0)
        self.assertEqual(unstable.closed_loop_unstable, 2)
        boundary = nyquist(TransferFunction([1], [1, 1], limit), 2)
        self.assertIn(boundary.status, ['boundary', 'inconclusive'])

    def test_hidden_cancellation_rejected(self):
        with self.assertRaises(ValueError):
            nyquist(TransferFunction([1, -1], [1, 0, -1]), 1)

    def test_small_gain_unstable_root_not_hidden_by_indentation(self):
        result = nyquist(TransferFunction([-1], [1, 0]), 1e-8)
        self.assertEqual(result.closed_loop_unstable, 1)
        self.assertLess(result.indent_radius, 1e-9)

    def test_nearly_axis_pole_does_not_receive_false_certificate(self):
        result = nyquist(TransferFunction([1], [1, -1e-10]), 0.5e-10)
        self.assertEqual(result.status, 'inconclusive')
        self.assertIsNone(result.closed_loop_unstable)

    def test_high_gain_requires_larger_outer_contour(self):
        plant = benchmark_models()['A']
        result = nyquist(plant, 1e12)
        self.assertEqual(result.closed_loop_unstable, 2)
        self.assertGreater(result.radius, 10000)
        self.assertLess(outer_loop_bound(plant, 1e12, result.radius), 0.1)

    def test_two_imaginary_axis_poles(self):
        result = nyquist(TransferFunction([1], [1, 0, 1]), 1)
        self.assertIn(result.status, ['boundary', 'inconclusive'])
        self.assertIsNone(result.closed_loop_unstable)


class FrequencyTests(unittest.TestCase):
    def test_bode_first_order_reference(self):
        result = bode(TransferFunction([1], [1, 1]), [0.1, 1, 10])
        self.assertAlmostEqual(result.magnitude_db[1], -10*np.log10(2), places=10)
        self.assertAlmostEqual(result.phase_deg[1], -45, places=10)

    def test_exact_unwrapped_delay_phase(self):
        w = np.geomspace(0.01, 100, 100)
        result = bode(TransferFunction([1], [1, 1], 3), w)
        assert_allclose(result.phase_deg, np.degrees(-np.arctan(w)-3*w), atol=1e-10)

    def test_integrator_phase_margin(self):
        result = margins(TransferFunction([1], [1, 1, 0]))
        wc = np.sqrt((np.sqrt(5)-1)/2)
        self.assertAlmostEqual(result.gain_crossovers[0], wc, places=9)
        self.assertAlmostEqual(result.phase_margin_deg, 90-np.degrees(np.arctan(wc)), places=8)

    def test_third_order_gain_and_phase_margins(self):
        result = margins(TransferFunction([1], [1, 3, 3, 1]), 4)
        wc = np.sqrt(4**(2/3)-1)
        self.assertAlmostEqual(result.gain_margin, 2, places=8)
        self.assertAlmostEqual(result.phase_crossovers[0], np.sqrt(3), places=8)
        self.assertAlmostEqual(result.phase_margin_deg, 180-3*np.degrees(np.arctan(wc)), places=8)

    def test_delay_margin_reference(self):
        result = margins(TransferFunction([1], [1, 1], 0.5), 2)
        wc = np.sqrt(3)
        self.assertAlmostEqual(result.gain_crossovers[0], wc, places=8)
        self.assertAlmostEqual(result.phase_margin_deg, 120-np.degrees(0.5*wc), places=8)
        for crossing in result.phase_crossovers:
            self.assertLess(abs(np.sin(np.arctan(crossing)+0.5*crossing)), 1e-8)

    def test_absent_crossing_not_invented_as_infinite(self):
        result = margins(TransferFunction([1], [1, 1]), 0.5)
        self.assertIsNone(result.gain_margin)
        self.assertIsNone(result.phase_margin_deg)

    def test_invalid_frequency_grid(self):
        with self.assertRaises(ValueError):
            bode(TransferFunction([1], [1, 1]), [1, 0])

    def test_static_phase_crossing_of_unstable_plant(self):
        result = margins(benchmark_models()['B'], 5)
        self.assertAlmostEqual(result.gain_margin, 1.2, places=10)
        self.assertEqual(result.phase_crossovers[0], 0)

    def test_static_unit_magnitude_boundary(self):
        result = margins(benchmark_models()['B'], 6)
        self.assertAlmostEqual(result.gain_crossovers[0], 0)
        self.assertAlmostEqual(result.phase_margin_deg, 0, places=10)


class RootLocusTests(unittest.TestCase):
    def test_second_order_analytical_roots(self):
        gains = np.array([0, 0.5, 1, 2, 4])
        result = root_locus(TransferFunction([1], [1, 2, 0]), gains)
        for gain, calculated in zip(gains, result.roots):
            expected = np.array([-1+np.sqrt(1-gain+0j), -1-np.sqrt(1-gain+0j)])
            assignment = minimum_cost_assignment(abs(calculated[:, None]-expected[None, :]))
            assert_allclose(calculated, expected[assignment], atol=1e-10)

    def test_hungarian_matches_exhaustive_reference(self):
        rng = np.random.default_rng(13)
        for n in range(1, 6):
            cost = rng.uniform(0, 4, (n, n))
            assignment = minimum_cost_assignment(cost)
            actual = sum(cost[i, assignment[i]] for i in range(n))
            reference = min(sum(cost[i, p[i]] for i in range(n)) for p in itertools.permutations(range(n)))
            self.assertAlmostEqual(actual, reference, places=12)

    def test_closed_loop_residuals(self):
        plant = benchmark_models()['C']
        result = root_locus(plant, np.linspace(0, 15, 100))
        for gain, roots in zip(result.gains, result.roots):
            coefficients = plant.characteristic(gain)
            residual = abs(np.polyval(coefficients, roots)) / np.polyval(abs(coefficients), abs(roots))
            self.assertLess(float(max(residual)), 1e-12)

    def test_invalid_gain_order(self):
        with self.assertRaises(ValueError):
            root_locus(benchmark_models()['A'], [2, 1])


if __name__ == '__main__':
    unittest.main()
