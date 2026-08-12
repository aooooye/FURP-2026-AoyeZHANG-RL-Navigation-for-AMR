import json
import math
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from protocol_guard import PROTOCOL_PATH, load_json, validate_protocol
from robustness_core import (
    perturb_pointgoal,
    sample_action_amount,
    sample_localization_biases,
    stateless_standard_normal,
    temporary_actuation_amount,
    wrap_radians,
)


class RobustnessCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = load_json(PROTOCOL_PATH)

    def test_protocol_and_rng_golden_vectors(self):
        validate_protocol(self.protocol)
        for vector in self.protocol["rng"]["golden_vectors"]:
            self.assertAlmostEqual(
                stateless_standard_normal(*vector["key"]),
                vector["standard_normal"],
                places=15,
            )

    def test_stateless_rng_depends_on_seed_channel_and_step_not_call_order(self):
        key = (41001, "scene", "episode", "forward_distance", 7)
        first = stateless_standard_normal(*key)
        stateless_standard_normal(41003, "other", "episode", "turn_angle", 99)
        self.assertEqual(first, stateless_standard_normal(*key))
        self.assertNotEqual(
            first,
            stateless_standard_normal(41002, "scene", "episode", "forward_distance", 7),
        )
        self.assertNotEqual(
            first,
            stateless_standard_normal(41001, "scene", "episode", "turn_angle", 7),
        )
        self.assertNotEqual(
            first,
            stateless_standard_normal(41001, "scene", "episode", "forward_distance", 8),
        )

    def test_localization_bias_is_episode_constant_and_bounded(self):
        first = sample_localization_biases(
            self.protocol,
            noise_seed=41001,
            scene_id="scene",
            episode_id="episode",
        )
        second = sample_localization_biases(
            self.protocol,
            noise_seed=41001,
            scene_id="scene",
            episode_id="episode",
        )
        self.assertEqual(first, second)
        self.assertGreaterEqual(first[0], -0.15)
        self.assertLessEqual(first[0], 0.15)
        self.assertGreaterEqual(first[1], -6.0)
        self.assertLessEqual(first[1], 6.0)

    def test_pointgoal_clean_is_exact_identity(self):
        observations = {
            "pointgoal_with_gps_compass": np.array([1.0, 0.2], dtype=np.float32),
            "depth": np.ones((2, 2), dtype=np.float32),
        }
        output = perturb_pointgoal(
            observations,
            distance_bias_m=0.1,
            bearing_bias_deg=5.0,
            enabled=False,
        )
        self.assertIs(output, observations)

    def test_pointgoal_noise_only_changes_copied_policy_observation(self):
        original_vector = np.array([0.01, math.pi - 0.01], dtype=np.float32)
        original_copy = original_vector.copy()
        observations = {
            "pointgoal_with_gps_compass": original_vector,
            "depth": np.ones((2, 2), dtype=np.float32),
        }
        output = perturb_pointgoal(
            observations,
            distance_bias_m=-0.15,
            bearing_bias_deg=6.0,
            enabled=True,
        )
        self.assertIsNot(output, observations)
        self.assertEqual(float(output["pointgoal_with_gps_compass"][0]), 0.0)
        self.assertGreaterEqual(float(output["pointgoal_with_gps_compass"][1]), -math.pi)
        self.assertLess(float(output["pointgoal_with_gps_compass"][1]), math.pi)
        np.testing.assert_array_equal(original_vector, original_copy)
        self.assertIs(output["depth"], observations["depth"])

    def test_action_noise_is_bounded_and_stop_is_unchanged(self):
        for step in range(1000):
            forward = sample_action_amount(
                self.protocol,
                action_name="move_forward",
                noise_seed=41001,
                scene_id="scene",
                episode_id="episode",
                step_index=step,
            )
            turn = sample_action_amount(
                self.protocol,
                action_name="turn_left",
                noise_seed=41001,
                scene_id="scene",
                episode_id="episode",
                step_index=step,
            )
            self.assertGreaterEqual(forward, 0.235)
            self.assertLessEqual(forward, 0.265)
            self.assertGreaterEqual(turn, 9.5)
            self.assertLessEqual(turn, 10.5)
        self.assertIsNone(
            sample_action_amount(
                self.protocol,
                action_name="stop",
                noise_seed=41001,
                scene_id="scene",
                episode_id="episode",
                step_index=0,
            )
        )

    def test_temporary_actuation_restores_normally_and_on_exception(self):
        actuation = SimpleNamespace(amount=0.25)
        action_space = {1: SimpleNamespace(actuation=actuation)}
        agent = SimpleNamespace(
            agent_config=SimpleNamespace(action_space=action_space)
        )
        with temporary_actuation_amount(agent, 1, 0.24):
            self.assertEqual(actuation.amount, 0.24)
            self.assertEqual(len(action_space), 1)
        self.assertEqual(actuation.amount, 0.25)
        with self.assertRaisesRegex(RuntimeError, "sentinel"):
            with temporary_actuation_amount(agent, 1, 0.26):
                self.assertEqual(actuation.amount, 0.26)
                raise RuntimeError("sentinel")
        self.assertEqual(actuation.amount, 0.25)

    def test_wrap_is_half_open(self):
        self.assertGreaterEqual(wrap_radians(100.0), -math.pi)
        self.assertLess(wrap_radians(100.0), math.pi)


if __name__ == "__main__":
    unittest.main()
