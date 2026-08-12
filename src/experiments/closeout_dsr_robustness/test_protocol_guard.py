import unittest

from protocol_guard import (
    CHECKPOINT_MANIFEST_PATH,
    PROTOCOL_PATH,
    build_run_manifest,
    load_json,
    validate_checkpoint_manifest,
    validate_protocol,
    validate_run_selection,
)


class ProtocolGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = load_json(PROTOCOL_PATH)

    def test_frozen_protocol_and_six_checkpoint_files(self):
        validate_protocol(self.protocol)
        validate_checkpoint_manifest(load_json(CHECKPOINT_MANIFEST_PATH))

    def test_clean_and_formal_run_manifests_are_fully_bound(self):
        clean = build_run_manifest(
            phase="zero_noise",
            condition="clean",
            method="baseline",
            training_seed=100,
            noise_seed=0,
        )
        formal = build_run_manifest(
            phase="formal",
            condition="combined",
            method="dsr",
            training_seed=300,
            noise_seed=41003,
        )
        self.assertEqual(clean["episodes"], 100)
        self.assertFalse(clean["localization_enabled"])
        self.assertFalse(clean["actuation_enabled"])
        self.assertTrue(formal["localization_enabled"])
        self.assertTrue(formal["actuation_enabled"])
        self.assertEqual(len(formal["run_identity_sha256"]), 64)

    def test_rejects_out_of_protocol_selection(self):
        with self.assertRaisesRegex(ValueError, "noise seed"):
            validate_run_selection(
                self.protocol,
                phase="formal",
                condition="combined",
                method="dsr",
                training_seed=300,
                noise_seed=999,
            )
        with self.assertRaisesRegex(ValueError, "training seed 100"):
            validate_run_selection(
                self.protocol,
                phase="smoke",
                condition="actuation",
                method="baseline",
                training_seed=200,
                noise_seed=41001,
            )


if __name__ == "__main__":
    unittest.main()
