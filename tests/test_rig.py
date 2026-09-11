"""
Lightweight sanity checks for the rig's math -- NOT a full test suite.
The real way this project gets verified is by rendering frames and
looking at them (see CLAUDE.md). This file just catches obviously
broken kinematics/blending before you get that far.

Run with: python -m unittest tests/test_rig.py
"""

import math
import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.rig import Pose, compute_points, layout_points
from engine.pose_blend import blend_poses, PoseCycle
from engine.poses import STAND, POSES, CYCLES


class TestForwardKinematics(unittest.TestCase):
    def test_stand_pose_has_all_points(self):
        points = compute_points(STAND, H=1.0)
        expected = {"hip", "neck", "head", "sh_r", "sh_l", "hip_r", "hip_l",
                    "el_r", "hand_r", "el_l", "hand_l",
                    "knee_r", "foot_r", "toe_r", "knee_l", "foot_l", "toe_l"}
        self.assertEqual(set(points.keys()), expected)

    def test_head_is_above_hip(self):
        points = compute_points(STAND, H=1.0)
        self.assertLess(points["head"][1], points["hip"][1])

    def test_auto_grounding_puts_lowest_foot_at_zero(self):
        for name, pose in POSES.items():
            points = layout_points(pose, H=1.0, facing="right")
            lowest = max(points["toe_r"][1], points["toe_l"][1],
                         points["foot_r"][1], points["foot_l"][1])
            self.assertAlmostEqual(lowest, 0.0, places=5, msg=f'pose "{name}" not grounded')

    def test_facing_left_mirrors_x(self):
        right_points = layout_points(STAND, H=1.0, facing="right")
        left_points = layout_points(STAND, H=1.0, facing="left")
        self.assertAlmostEqual(right_points["head"][0], -left_points["head"][0], places=5)

    def test_all_library_poses_compute_without_error(self):
        for name, pose in POSES.items():
            points = compute_points(pose, H=1.0)
            for pname, (x, y) in points.items():
                self.assertTrue(math.isfinite(x), f'{name}.{pname}.x is not finite')
                self.assertTrue(math.isfinite(y), f'{name}.{pname}.y is not finite')


class TestBlending(unittest.TestCase):
    def test_blend_at_zero_matches_start(self):
        other = POSES["cheer"]
        blended = blend_poses(STAND, other, 0.0)
        self.assertAlmostEqual(blended.torso_angle, STAND.torso_angle, places=3)

    def test_blend_at_one_matches_end(self):
        other = POSES["cheer"]
        blended = blend_poses(STAND, other, 1.0)
        self.assertAlmostEqual(blended.r_shoulder_angle, other.r_shoulder_angle, places=3)

    def test_blend_shortest_path_wraps_angle(self):
        a = Pose(torso_angle=350.0)
        b = Pose(torso_angle=10.0)
        halfway = blend_poses(a, b, 0.5)
        # Should pass through 0/360, not swing the long way through 180.
        self.assertTrue(halfway.torso_angle < 10 or halfway.torso_angle > 350)


class TestCycles(unittest.TestCase):
    def test_all_cycles_sample_without_error(self):
        for name, cycle in CYCLES.items():
            self.assertIsInstance(cycle, PoseCycle)
            for phase in (0.0, 0.25, 0.5, 0.75, 0.99):
                pose = cycle.sample(phase)
                points = compute_points(pose, H=1.0)
                self.assertIn("hip", points)

    def test_cycle_wraps_around(self):
        cycle = CYCLES["walk"]
        start = cycle.sample(0.0)
        wrapped = cycle.sample(1.0)
        self.assertAlmostEqual(start.torso_angle, wrapped.torso_angle, places=3)


if __name__ == "__main__":
    unittest.main()
