import unittest
import numpy as np
from numpy.testing import assert_allclose
from src.pid import PIDConfig, plant_zoh_coefficients, continuous_loop, delay_limits, simulate_pid
from src.nyquist import nyquist


class PIDTests(unittest.TestCase):
    def test_exact_zoh_coefficients_dc_gain(self):
        for ts in (0.005, 0.01, 0.05):
            num, den = plant_zoh_coefficients(ts)
            self.assertAlmostEqual(sum(num)/sum(den), 1, places=10)

    def test_step_converges_to_reference(self):
        result = simulate_pid(delay=0, duration=60)
        self.assertLess(abs(result.output[-1]-1), 1e-7)
        self.assertFalse(result.stopped_early)

    def test_delay_buffer_and_quantization(self):
        result = simulate_pid(delay=0.033, duration=2)
        self.assertEqual(result.delay_samples, 3)
        self.assertEqual(result.effective_delay, 0.03)
        assert_allclose(result.delayed_command[:3], 0)
        assert_allclose(result.delayed_command[3:-1], result.command[:-4])

    def test_continuous_prediction_matches_nyquist(self):
        config = PIDConfig()
        limit = delay_limits(config)['continuous_s']
        self.assertEqual(nyquist(continuous_loop(config, 0.8*limit)).status, 'stable')
        self.assertEqual(nyquist(continuous_loop(config, 1.2*limit)).status, 'unstable')

    def test_digital_behavior_on_both_sides_of_limit(self):
        config = PIDConfig()
        limit = delay_limits(config)['digital_s']
        stable = simulate_pid(config, 0.6*limit, 100)
        unstable = simulate_pid(config, 1.5*limit, 100)
        self.assertLess(stable.metrics()['tail_max_abs_error'], 0.01)
        self.assertGreater(unstable.metrics()['max_abs_output'], 3)

    def test_predictions_converge_as_sampling_decreases(self):
        differences = []
        for ts in (0.02, 0.01, 0.005):
            limits = delay_limits(PIDConfig(sample_time=ts))
            differences.append(abs(limits['digital_s']-limits['continuous_s']))
        self.assertTrue(differences[0] > differences[1] > differences[2])

    def test_termination_is_reported(self):
        result = simulate_pid(delay=3, duration=100, safety_limit=5)
        self.assertTrue(result.stopped_early)
        self.assertLess(result.time[-1], 100)

    def test_invalid_configuration(self):
        for kwargs in ({'ki':0}, {'tf':0}, {'sample_time':0}, {'kp':float('nan')}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                PIDConfig(**kwargs)
