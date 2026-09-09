import unittest

from scripts.container.prepare import PROFILES


class ContainerPrepareProfiles(unittest.TestCase):
    def test_profiles_are_explicit_and_separate(self):
        self.assertEqual(set(PROFILES), {'linux/amd64', 'linux/arm64'})
        self.assertEqual(PROFILES['linux/amd64'], ('Dockerfile', 'packages.lock.json'))
        self.assertEqual(PROFILES['linux/arm64'], ('Dockerfile.arm64', 'packages.arm64.lock.json'))
        self.assertEqual(len({value[0] for value in PROFILES.values()}), 2)
        self.assertEqual(len({value[1] for value in PROFILES.values()}), 2)


if __name__ == '__main__':
    unittest.main()
