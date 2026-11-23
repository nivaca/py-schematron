# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Nicolas Vaughan <nicolasvaughan@proton.me>
# This file is part of py-schematron. See the LICENSE file for details.
"""Pruebas de la firma de las versiones en tools/release.py.

Cada archivo y SHA256SUMS quedan firmados, y cada firma se comprueba con
solo la clave pública publicada; un archivo cambiado, u otra clave, no se
comprueban, y una etiqueta firmada se verifica igual.  Usan claves hechas
aquí, en un GNUPGHOME temporal: nunca las del usuario.
"""

import hashlib
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("release", ROOT / "tools" / "release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def make_key(home: Path, name: str) -> tuple[str, Path]:
    """A key without a passphrase in HOME: its fingerprint, and its public key exported."""
    home.mkdir(mode=0o700)
    env = dict(os.environ, GNUPGHOME=str(home))
    subprocess.run(["gpg", "--batch", "--passphrase", "", "--quick-gen-key",
                    f"{name} <{name}@example.org>", "ed25519", "sign", "never"],
                   env=env, check=True, capture_output=True)
    out = subprocess.run(["gpg", "--batch", "--with-colons", "--list-secret-keys"], env=env,
                         check=True, capture_output=True, text=True).stdout
    fpr = next(line.split(":")[9] for line in out.splitlines() if line.startswith("fpr"))
    public = home.parent / f"{name}.asc"
    public.write_bytes(subprocess.run(["gpg", "--batch", "--armor", "--export", fpr], env=env,
                                      check=True, capture_output=True).stdout)
    return fpr, public


@unittest.skipIf(not shutil.which("gpg") or sys.platform == "win32", "needs gpg")
class SigningTest(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="release-test-"))
        self.homes = []
        self.fpr, self.public = self.key("release")
        # (gpg firma con la clave de prueba: GNUPGHOME apunta a su carpeta)
        patch = mock.patch.dict(os.environ, {"GNUPGHOME": str(self.tmp / "release")})
        patch.start()
        self.addCleanup(patch.stop)
        patch = mock.patch.object(release, "say", lambda text="": None)
        patch.start()
        self.addCleanup(patch.stop)

    def tearDown(self):
        for home in self.homes:
            subprocess.run(["gpgconf", "--kill", "all"],
                           env=dict(os.environ, GNUPGHOME=str(home)), capture_output=True)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def key(self, name):
        self.homes.append(self.tmp / name)
        return make_key(self.tmp / name, name)

    def files(self):
        out = []
        for name, data in (("app.zip", b"zip"), ("app.vsix", b"vsix")):
            (self.tmp / name).write_bytes(data)
            out.append(self.tmp / name)
        return out

    def test_every_file_signed_and_checked(self):
        files = self.files()
        sums = self.tmp / "SHA256SUMS"
        published = release.sign_files(files, self.fpr, self.public, sums)
        self.assertEqual(sums.read_text(), "".join(
            f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}\n" for f in files))
        self.assertEqual([p.name for p in published],
                         ["app.zip", "app.vsix", "SHA256SUMS", "app.zip.asc", "app.vsix.asc",
                          "SHA256SUMS.asc", "release.asc"])
        with release.PublicOnly(self.public) as env:
            for f in files + [sums]:
                self.assertTrue(release.signature_ok(f, env))
            # a file changed after it was signed: its signature is bad
            files[0].write_bytes(b"zip, changed")
            self.assertFalse(release.signature_ok(files[0], env))

    def test_good_signatures_are_kept(self):
        files = self.files()
        sums = self.tmp / "SHA256SUMS"
        release.sign_files(files, self.fpr, self.public, sums)
        before = {f: f.with_name(f.name + ".asc").read_bytes() for f in files + [sums]}
        release.sign_files(files, self.fpr, self.public, sums)
        for f, asc in before.items():
            self.assertEqual(f.with_name(f.name + ".asc").read_bytes(), asc)

    def test_another_key_does_not_check(self):
        """The key published must be the one that signed, or the release stops."""
        _other, other_public = self.key("other")
        with self.assertRaises(release.Failure):
            release.sign_files(self.files(), self.fpr, other_public, self.tmp / "SHA256SUMS")

    def test_fingerprints(self):
        self.assertIn(self.fpr, release.key_fingerprints(self.public))

    def test_signed_tag(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        env = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1")

        def git(*args):
            subprocess.run(["git", "-c", "user.name=T", "-c", "user.email=t@example.org", *args],
                           cwd=repo, env=env, check=True, capture_output=True)
        git("init", "-q")
        git("commit", "-q", "--allow-empty", "-m", "x")
        git("tag", "-a", "v1", "-m", "v1")
        git("tag", "--sign", "--local-user", self.fpr, "-m", "v2", "v2")
        with mock.patch.object(release, "ROOT", repo):
            self.assertFalse(release.tag_verifies("v1", self.public))
            self.assertTrue(release.tag_verifies("v2", self.public))


if __name__ == "__main__":
    unittest.main()
