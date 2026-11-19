# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Nicolas Vaughan <nicolasvaughan@proton.me>
# This file is part of py-schematron. See the LICENSE file for details.
"""Tests of installers/install.py, without network or pip: the release comes
from this repository (--from), the TEI stylesheets are not fetched, and the
environment's Python is this one.  A real install, on Linux, macOS and
Windows, is run by the GitHub workflow (installers job)."""

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("install", REPO / "installers" / "install.py")
install = importlib.util.module_from_spec(spec)
spec.loader.exec_module(install)


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="pysch-installers-")
        self.home = Path(self._tmp.name)
        patches = [
            mock.patch.object(Path, "home", lambda: self.home),
            mock.patch.dict(os.environ, {"XDG_DATA_HOME": "", "LOCALAPPDATA": ""}),
            # (no environment and no pip: the "environment's Python" is this one)
            mock.patch.object(install, "make_venv", self.fake_venv),
            mock.patch.object(install, "install_libraries", lambda python: None),
            mock.patch.object(install, "say", lambda text="": None),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def tearDown(self):
        self._tmp.cleanup()

    @staticmethod
    def fake_venv(venv):
        venv.mkdir(parents=True, exist_ok=True)
        return Path(sys.executable)

    def run_installer(self, *args):
        install.main(["--no-tei-stylesheets", *args])


class TestPlaces(unittest.TestCase):
    def test_folders_of_each_system(self):
        home = Path("/h")
        with mock.patch.object(Path, "home", lambda: home), \
                mock.patch.dict(os.environ, {"XDG_DATA_HOME": "", "LOCALAPPDATA": ""}):
            for platform, expected in (("linux", home / ".local/share/py-schematron"),
                                       ("darwin", home / "Library/Application Support/py-schematron"),
                                       ("win32", home / "AppData/Local/py-schematron")):
                with mock.patch.object(sys, "platform", platform):
                    self.assertEqual(install.home_of_app(), expected)
            with mock.patch.object(sys, "platform", "linux"), \
                    mock.patch.dict(os.environ, {"XDG_DATA_HOME": "/data"}):
                self.assertEqual(install.home_of_app(), Path("/data/py-schematron"))

    def test_commands_of_each_system(self):
        program, python = Path("/p/program"), Path("/p/venv/bin/python")
        with mock.patch.object(sys, "platform", "linux"):
            texts = install.commands(program, python)
        self.assertEqual(sorted(texts), ["py-schematron-all.sh", "py-schematron.py"])
        self.assertIn(f'exec "{python}" "{program / "py-schematron.py"}" "$@"', texts["py-schematron.py"])
        self.assertIn(f'PY_SCHEMATRON_PYTHON="{python}"', texts["py-schematron-all.sh"])
        with mock.patch.object(sys, "platform", "win32"):
            texts = install.commands(program, python)
        self.assertEqual(list(texts), ["py-schematron.cmd"])
        self.assertIn("%*", texts["py-schematron.cmd"])
        for text in texts.values():
            self.assertIn(install.MARK, text)

    def test_too_old_a_python(self):
        with mock.patch.object(sys, "version_info", (3, 14, 0)), self.assertRaises(SystemExit) as e:
            install.main([])
        self.assertIn("needs Python 3.15", str(e.exception))


@unittest.skipIf(sys.platform == "win32", "the commands are shell scripts here")
class TestInstall(Base):
    def test_install_run_update_and_uninstall(self):
        self.run_installer("--from", str(REPO))
        home = install.home_of_app()
        program = home / "program"
        self.assertTrue((program / "py-schematron.py").is_file())
        self.assertTrue((program / "LICENSE").is_file())
        bin_ = self.home / ".local" / "bin"             # (no ~/bin here)
        command = bin_ / "py-schematron.py"
        self.assertTrue(install.ours(command))
        self.assertTrue(os.access(command, os.X_OK))
        out = subprocess.run([str(command), "--version"], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertRegex(out.stdout, r"^py-schematron\.py \d")
        # an update keeps the download cache
        (program / ".schema-cache").mkdir()
        (program / ".schema-cache" / "x-s.rng").write_text("<x/>")
        self.run_installer("--from", str(REPO))
        self.assertTrue((program / ".schema-cache" / "x-s.rng").is_file())
        # uninstall: the folder and the commands
        install.main(["--uninstall"])
        self.assertFalse(home.exists())
        self.assertFalse(command.exists())
        self.assertFalse((bin_ / "py-schematron-all.sh").exists())

    def test_home_bin_is_used_when_it_exists(self):
        (self.home / "bin").mkdir()
        self.run_installer("--from", str(REPO))
        self.assertTrue(install.ours(self.home / "bin" / "py-schematron.py"))

    def test_from_a_release_zip(self):
        archive = self.home / "py-schematron-v.9.9.zip"
        with zipfile.ZipFile(archive, "w") as z:
            for name in ("py-schematron.py", "py-schematron-all.sh", "LICENSE"):
                z.write(REPO / name, f"py-schematron-v.9.9/{name}")
        self.run_installer("--from", str(archive))
        self.assertTrue((install.home_of_app() / "program" / "py-schematron-all.sh").is_file())

    def test_a_command_it_did_not_make_is_left_alone(self):
        (self.home / "bin").mkdir()
        other = self.home / "bin" / "py-schematron.py"
        other.symlink_to("/somewhere/else/py-schematron.py")
        self.run_installer("--from", str(REPO))
        self.assertTrue(other.is_symlink())                   # left alone...
        self.assertTrue(install.ours(self.home / "bin" / "py-schematron-all.sh"))
        self.run_installer("--from", str(REPO), "--force")    # ...unless --force
        self.assertTrue(install.ours(other))
        install.main(["--uninstall"])
        other.symlink_to("/somewhere/else/py-schematron.py")
        install.main(["--uninstall"])                         # (not ours: stays)
        self.assertTrue(other.is_symlink())

    def test_not_a_release(self):
        with self.assertRaises(SystemExit) as e:
            self.run_installer("--from", str(self.home))
        self.assertIn("there is no py-schematron.py", str(e.exception))


class TestLaunchers(unittest.TestCase):
    def test_the_launchers_are_there(self):
        sh = (REPO / "installers" / "install.sh").read_text()
        ps1 = (REPO / "installers" / "install.ps1").read_text()
        for text in (sh, ps1):
            self.assertIn("raw.githubusercontent.com/nivaca/py-schematron/main/installers/install.py", text)
            self.assertIn("3, 15", text)
        if sys.platform != "win32":
            self.assertEqual(subprocess.run(["sh", "-n", str(REPO / "installers" / "install.sh")]).returncode, 0)


if __name__ == "__main__":
    unittest.main()
