import math
import unittest

from dsr_math import (
    dynamic_success_reward,
    replace_constant_success_bonus,
    terminal_stop_diagnostics,
)


class DynamicSuccessRewardTests(unittest.TestCase):
    def test_boundary_equals_standard_success_reward(self):
        self.assertAlmostEqual(
            dynamic_success_reward(2.5, 0.2, 0.2), 2.5
        )

    def test_goal_center_matches_paper_formula(self):
        self.assertAlmostEqual(
            dynamic_success_reward(2.5, 0.2, 0.0), 2.5 * math.e
        )

    def test_reward_increases_closer_to_goal(self):
        near_center = dynamic_success_reward(2.5, 0.2, 0.05)
        near_boundary = dynamic_success_reward(2.5, 0.2, 0.19)
        self.assertGreater(near_center, near_boundary)

    def test_invalid_success_distance_fails(self):
        with self.assertRaises(ValueError):
            dynamic_success_reward(2.5, 0.0, 0.0)

    def test_negative_final_distance_fails(self):
        with self.assertRaises(ValueError):
            dynamic_success_reward(2.5, 0.2, -0.01)

    def test_non_finite_inputs_fail(self):
        for values in (
            (float("nan"), 0.2, 0.0),
            (2.5, float("inf"), 0.0),
            (2.5, 0.2, float("nan")),
        ):
            with self.subTest(values=values), self.assertRaises(ValueError):
                dynamic_success_reward(*values)

    def test_failed_episode_keeps_standard_reward(self):
        self.assertEqual(
            replace_constant_success_bonus(
                base_reward=-0.25,
                episode_success=False,
                success_reward=2.5,
                success_distance=0.2,
                final_distance=0.3,
            ),
            -0.25,
        )

    def test_success_replaces_not_duplicates_constant_bonus(self):
        standard_reward = 3.0
        shaped = replace_constant_success_bonus(
            base_reward=standard_reward,
            episode_success=True,
            success_reward=2.5,
            success_distance=0.2,
            final_distance=0.0,
        )
        self.assertAlmostEqual(shaped, standard_reward + 2.5 * (math.e - 1.0))

    def test_terminal_stop_diagnostics(self):
        self.assertEqual(
            terminal_stop_diagnostics(True, True, True),
            (1.0, 0.0, 0.0),
        )
        self.assertEqual(
            terminal_stop_diagnostics(True, True, False),
            (1.0, 1.0, 0.0),
        )
        self.assertEqual(
            terminal_stop_diagnostics(True, False, False),
            (0.0, 0.0, 1.0),
        )
        self.assertEqual(
            terminal_stop_diagnostics(False, False, False),
            (0.0, 0.0, 0.0),
        )


if __name__ == "__main__":
    unittest.main()
